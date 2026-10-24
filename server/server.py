# -*- coding: utf-8 -*-
"""小柯機器人 YouTube 下載工具 - 本機／自架後端服務

單檔 Flask 服務，提供：
  GET  /                      網頁介面（線上版同一份程式碼）
  GET  /api/health            健康檢查
  POST /api/info              解析網址，回傳影片／播放清單資訊與可用解析度
  POST /api/jobs              建立下載任務（mp4／mp3 + 解析度 + 播放清單項目）
  GET  /api/jobs/<id>         查詢進度
  POST /api/jobs/<id>/cancel  取消任務
  GET  /api/files/<id>/<n>    把下載好的檔案給瀏覽器
"""
import os
import re
import sys
import time
import uuid
import threading
import traceback
from pathlib import Path

from flask import Flask, request, jsonify, send_file, send_from_directory

import yt_dlp

HERE = Path(__file__).resolve().parent
WEB_DIR = HERE.parent / "web"
PORT = int(os.environ.get("XK_PORT", "8787"))

DOWNLOAD_DIR = Path(
    os.environ.get("XK_DOWNLOAD_DIR")
    or (Path.home() / "Downloads" / "小柯YouTube")
)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

QUALITY_LADDER = [360, 480, 720, 1080, 1440, 2160, 4320]

app = Flask(__name__, static_folder=None)

JOBS = {}
JOBS_LOCK = threading.Lock()


# ---------------------------------------------------------------- 共用工具

@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    # Chrome 從 https 網頁連本機服務需要這個標頭（Private Network Access）
    resp.headers["Access-Control-Allow-Private-Network"] = "true"
    return resp


@app.route("/api/<path:_any>", methods=["OPTIONS"])
def cors_preflight(_any):
    return ("", 204)


def base_opts():
    return {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "ignoreerrors": False,
        "nocheckcertificate": True,
        "retries": 5,
        "fragment_retries": 5,
    }


def clean_url(url):
    url = (url or "").strip()
    if not url:
        raise ValueError("請輸入影片網址")
    if not re.match(r"^https?://", url):
        url = "https://" + url
    return url


def thumb_of(info):
    t = info.get("thumbnail")
    if t:
        return t
    thumbs = info.get("thumbnails") or []
    return thumbs[-1]["url"] if thumbs else None


def short_err(e):
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(e))
    msg = msg.replace("ERROR: ", "").strip()
    return msg[:300] or e.__class__.__name__


# ---------------------------------------------------------------- 解析

def extract_resolutions(info):
    heights = set()
    for f in info.get("formats") or []:
        h = f.get("height")
        if h and f.get("vcodec") not in (None, "none"):
            heights.add(int(h))
    out = [step for step in QUALITY_LADDER if any(abs(h - step) <= 40 for h in heights)]
    if not out and heights:
        out = sorted(heights)[-4:]
    return out


@app.post("/api/info")
def api_info():
    try:
        url = clean_url((request.get_json(silent=True) or {}).get("url"))
    except ValueError as e:
        return jsonify(ok=False, error=str(e)), 400

    opts = base_opts()
    opts["extract_flat"] = "in_playlist"
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        return jsonify(ok=False, error="解析失敗：" + short_err(e)), 400

    if info.get("_type") == "playlist" and info.get("entries"):
        entries = []
        for i, e in enumerate(info["entries"], start=1):
            if not e:
                continue
            entries.append({
                "index": i,
                "id": e.get("id"),
                "title": e.get("title") or ("第 %d 部影片" % i),
                "duration": e.get("duration"),
                "thumbnail": thumb_of(e),
                "uploader": e.get("uploader") or e.get("channel"),
            })
        resolutions = [360, 720, 1080]
        if entries:
            try:
                with yt_dlp.YoutubeDL(base_opts()) as ydl:
                    first = ydl.extract_info(
                        "https://www.youtube.com/watch?v=" + entries[0]["id"],
                        download=False)
                resolutions = extract_resolutions(first) or resolutions
            except Exception:
                pass
        return jsonify(ok=True, type="playlist",
                       title=info.get("title") or "播放清單",
                       uploader=info.get("uploader") or info.get("channel"),
                       thumbnail=thumb_of(info) or (entries[0]["thumbnail"] if entries else None),
                       count=len(entries), entries=entries, resolutions=resolutions)

    return jsonify(ok=True, type="video", title=info.get("title") or "影片",
                   id=info.get("id"), uploader=info.get("uploader") or info.get("channel"),
                   duration=info.get("duration"), thumbnail=thumb_of(info),
                   resolutions=extract_resolutions(info))


# ---------------------------------------------------------------- 下載

def build_format(mode, quality):
    if mode == "mp3":
        return "bestaudio/best"
    if quality in (None, "", "best"):
        return "bv*+ba/b"
    q = int(quality)
    # 先挑 H.264（相容性最好），再退回其他編碼
    return ("bv*[height<=%d][vcodec^=avc1]+ba[ext=m4a]/"
            "bv*[height<=%d][ext=mp4]+ba[ext=m4a]/"
            "bv*[height<=%d]+ba/b[height<=%d]/b" % (q, q, q, q))


class Cancelled(Exception):
    pass


def sanitize(name):
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", name).strip(" .")
    return name[:100] or "下載"


def make_job(payload):
    job_id = uuid.uuid4().hex[:12]
    job = {
        "id": job_id,
        "status": "queued",
        "mode": payload["mode"],
        "quality": payload.get("quality"),
        "url": payload["url"],
        "title": payload.get("title") or "",
        "total": max(1, int(payload.get("total") or 1)),
        "done_items": 0,
        "current": 1,
        "current_title": "",
        "item_percent": 0.0,
        "percent": 0.0,
        "speed": None,
        "eta": None,
        "stage": "準備中",
        "files": [],
        "error": None,
        "cancel": False,
        "created": time.time(),
    }
    with JOBS_LOCK:
        JOBS[job_id] = job
    return job


def recalc(job):
    frac = (job["done_items"] + min(job["item_percent"], 100) / 100.0) / job["total"]
    job["percent"] = round(min(frac, 1.0) * 100, 1)


def collect_files(job, info):
    seen = {f["path"] for f in job["files"]}

    def take(entry):
        if not entry:
            return
        for rd in entry.get("requested_downloads") or []:
            p = rd.get("filepath") or rd.get("_filename")
            if p and p not in seen and os.path.exists(p):
                seen.add(p)
                job["files"].append({
                    "name": os.path.basename(p),
                    "path": p,
                    "size": os.path.getsize(p),
                })

    if info and info.get("_type") == "playlist":
        for e in info.get("entries") or []:
            take(e)
    else:
        take(info)


def run_job(job, playlist_items, nums=None):
    job["status"] = "running"
    job["stage"] = "連線中"

    # YouTube 的 playlist_index 不等於「這次選了第幾部」，要換算成選取清單裡的位置
    pos_map = {n: i + 1 for i, n in enumerate(nums or [])}
    is_playlist = job["total"] > 1 or bool(playlist_items)
    folder = DOWNLOAD_DIR / sanitize(job["title"]) if (is_playlist and job["title"]) else DOWNLOAD_DIR
    folder.mkdir(parents=True, exist_ok=True)

    if is_playlist:
        outtmpl = str(folder / "%(playlist_index)02d - %(title).90s.%(ext)s")
    else:
        outtmpl = str(folder / "%(title).120s.%(ext)s")

    def progress_hook(d):
        if job["cancel"]:
            raise Cancelled()
        st = d.get("status")
        info = d.get("info_dict") or {}
        idx = info.get("playlist_index")
        if idx:
            job["current"] = min(pos_map.get(int(idx), int(idx)), job["total"])
        t = info.get("title")
        if t:
            job["current_title"] = t
        if st == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            got = d.get("downloaded_bytes") or 0
            if total:
                job["item_percent"] = got / total * 100
            job["speed"] = d.get("speed")
            job["eta"] = d.get("eta")
            job["stage"] = "下載中"
            recalc(job)
        elif st == "finished":
            job["item_percent"] = 100.0
            job["speed"] = None
            job["stage"] = "轉檔中" if job["mode"] == "mp3" else "合併中"
            recalc(job)

    def pp_hook(d):
        if job["cancel"]:
            raise Cancelled()
        name = d.get("postprocessor") or ""
        if d.get("status") == "started":
            if "ExtractAudio" in name:
                job["stage"] = "轉成 MP3"
            elif "Merger" in name:
                job["stage"] = "合併影音"
            elif "Thumbnail" in name or "Metadata" in name:
                job["stage"] = "寫入資訊"
        elif d.get("status") == "finished" and "MoveFiles" in name:
            # 一部影片真正完成，計入已完成數
            job["done_items"] = min(job["current"], job["total"])
            job["item_percent"] = 0.0
            recalc(job)

    opts = base_opts()
    opts.update({
        # pl_thumbnail 留空＝不要把播放清單封面另外存成一個檔
        "outtmpl": {"default": outtmpl, "pl_thumbnail": ""},
        "format": build_format(job["mode"], job["quality"]),
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [pp_hook],
        "ignoreerrors": "only_download" if is_playlist else False,
        "writethumbnail": job["mode"] == "mp3",
    })
    if job["mode"] == "mp3":
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail", "already_have_thumbnail": False},
        ]
    else:
        opts["merge_output_format"] = "mp4"
        opts["postprocessors"] = [{"key": "FFmpegMetadata"}]
    if playlist_items:
        opts["playlist_items"] = playlist_items

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(job["url"], download=True)
        collect_files(job, info)
        if not job["files"]:
            raise RuntimeError("下載完成但找不到檔案")
        job["done_items"] = job["total"]
        job["item_percent"] = 100.0
        job["percent"] = 100.0
        job["stage"] = "完成"
        job["status"] = "done"
    except Cancelled:
        job["status"] = "canceled"
        job["stage"] = "已取消"
    except Exception as e:
        job["status"] = "error"
        job["stage"] = "失敗"
        job["error"] = short_err(e)
        sys.stderr.write(traceback.format_exc())


@app.post("/api/jobs")
def api_create_job():
    data = request.get_json(silent=True) or {}
    try:
        url = clean_url(data.get("url"))
    except ValueError as e:
        return jsonify(ok=False, error=str(e)), 400
    mode = data.get("mode") or "mp4"
    if mode not in ("mp4", "mp3"):
        return jsonify(ok=False, error="格式只能是 mp4 或 mp3"), 400

    items = data.get("items")
    playlist_items = None
    nums = None
    total = 1
    if isinstance(items, list) and items:
        nums = sorted({int(i) for i in items})
        playlist_items = ",".join(str(n) for n in nums)
        total = len(nums)

    job = make_job({
        "url": url, "mode": mode, "quality": data.get("quality"),
        "title": data.get("title"), "total": total,
    })
    threading.Thread(target=run_job, args=(job, playlist_items, nums if playlist_items else None),
                     daemon=True).start()
    return jsonify(ok=True, job_id=job["id"])


def public_job(job):
    return {
        "id": job["id"], "status": job["status"], "stage": job["stage"],
        "percent": job["percent"], "item_percent": round(job["item_percent"], 1),
        "current": job["current"], "total": job["total"],
        "current_title": job["current_title"], "speed": job["speed"],
        "eta": job["eta"], "error": job["error"], "mode": job["mode"],
        "folder": str(DOWNLOAD_DIR),
        "files": [
            {"name": f["name"], "size": f["size"], "url": "/api/files/%s/%d" % (job["id"], i)}
            for i, f in enumerate(job["files"])
        ],
    }


@app.get("/api/jobs/<job_id>")
def api_job(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify(ok=False, error="找不到這個任務"), 404
    return jsonify(ok=True, job=public_job(job))


@app.post("/api/jobs/<job_id>/cancel")
def api_cancel(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify(ok=False, error="找不到這個任務"), 404
    job["cancel"] = True
    return jsonify(ok=True)


@app.get("/api/files/<job_id>/<int:idx>")
def api_file(job_id, idx):
    job = JOBS.get(job_id)
    if not job or idx >= len(job["files"]):
        return jsonify(ok=False, error="檔案不存在"), 404
    f = job["files"][idx]
    if not os.path.exists(f["path"]):
        return jsonify(ok=False, error="檔案已被移動或刪除"), 404
    return send_file(f["path"], as_attachment=True, download_name=f["name"])


@app.get("/api/health")
def api_health():
    return jsonify(ok=True, app="小柯機器人 YouTube 下載工具", version="1.0.0",
                   yt_dlp=yt_dlp.version.__version__, folder=str(DOWNLOAD_DIR))


# ---------------------------------------------------------------- 網頁

@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/<path:filename>")
def web_files(filename):
    if (WEB_DIR / filename).is_file():
        return send_from_directory(WEB_DIR, filename)
    return jsonify(ok=False, error="not found"), 404


def main():
    print("小柯機器人 YouTube 下載工具　後端已啟動")
    print("  網頁介面：http://127.0.0.1:%d/" % PORT)
    print("  下載資料夾：%s" % DOWNLOAD_DIR)
    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=PORT, threads=16)
    except ImportError:
        app.run(host="0.0.0.0", port=PORT, threaded=True)


if __name__ == "__main__":
    main()
