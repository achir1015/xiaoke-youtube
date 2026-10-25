# -*- coding: utf-8 -*-
"""小柯機器人 YouTube 下載工具 - 桌面版（Windows／Linux／macOS）

把後端服務包進一個原生視窗：打開就能用，不需要命令列；關掉視窗就停止所有執行。
"""
import multiprocessing
import os
import sys

# 打包後，任何套件用到 multiprocessing（例如進度條 tqdm 會建立多行程鎖，macOS／Linux
# 因此啟動 resource_tracker 輔助行程），那個子行程都是用「這個 App 執行檔」去跑的。
# 沒有 freeze_support()，子行程會把整個 App 再開一次——使用者看到的就是 App 跳掉又重開。
# 這一行一定要在其他東西之前執行。
if __name__ == "__main__":
    multiprocessing.freeze_support()

# 不要顯示 Hugging Face 的下載進度條：視窗程式看不到它，而且它正是會建立多行程鎖的元兇
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TQDM_DISABLE", "1")
# Intel Mac 上語音／翻譯引擎與其他套件各自帶了 OpenMP，同時載入會直接 abort 讓 App 閃退
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import json  # noqa: E402
import faulthandler  # noqa: E402
import socket  # noqa: E402
import subprocess  # noqa: E402
import threading  # noqa: E402
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402
from pathlib import Path  # noqa: E402

IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"


def log_dir():
    if IS_MAC:
        d = Path.home() / "Library" / "Logs" / "XiaokeYouTube"
    elif IS_WINDOWS:
        d = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "xiaoke-youtube" / "logs"
    else:
        d = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state") / "xiaoke-youtube"
    d.mkdir(parents=True, exist_ok=True)
    return d


def setup_logging():
    """視窗程式沒有主控台，輸出與當機訊息都寫進記錄檔；上一次的保留為 app.prev.log，
    這樣 App 閃退重開後，還看得到上一次為什麼掛掉。"""
    try:
        d = log_dir()
        cur, prev = d / "app.log", d / "app.prev.log"
        if cur.exists():
            os.replace(cur, prev)
        f = open(cur, "a", encoding="utf-8", buffering=1)
        if getattr(sys, "frozen", False) or sys.stdout is None:
            sys.stdout = f
            sys.stderr = f
        faulthandler.enable(f)          # 連 C 層級的當機（segfault、abort）都留下 Python 堆疊
        os.environ["XK_LOG_DIR"] = str(d)
        print("===== 啟動 pid=%d argv=%s =====" % (os.getpid(), sys.argv), flush=True)
    except OSError:
        pass


if __name__ == "__main__":
    setup_logging()

# tqdm 只要「建立」進度條（就算設成不顯示）就會建立 multiprocessing 鎖，
# 在 macOS／Linux 打包版裡就會觸發上面說的「App 被再開一次」。
# 這個 App 只有單一行程，先把它的多行程鎖設成「已存在（None）」，它就只會用執行緒鎖。
try:
    from tqdm.std import TqdmDefaultWriteLock
    TqdmDefaultWriteLock.mp_lock = None
except ImportError:
    pass

APP_VERSION = "1.2.0"
APP_NAME = "小柯機器人 YouTube 下載工具"
UPDATE_URL = "https://raw.githubusercontent.com/achir1015/xiaoke-youtube/main/version.json"
RELEASE_PAGE = "https://github.com/achir1015/xiaoke-youtube/releases/latest"


def base_path():
    """打包後是解壓目錄，開發時是專案根目錄。"""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


BASE = base_path()


def setup_ffmpeg():
    """優先用放在程式旁邊的 ffmpeg，找不到就靠系統 PATH。"""
    name = "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"
    for folder in (BASE / "ffmpeg", BASE, Path(sys.executable).parent / "ffmpeg"):
        if (folder / name).exists():
            os.environ["XK_FFMPEG_DIR"] = str(folder)
            os.environ["PATH"] = str(folder) + os.pathsep + os.environ.get("PATH", "")
            return str(folder)
    return None


# 開放區域網路連線，手機才連得到；Windows 第一次會跳防火牆詢問，
# 公用網路（咖啡廳等）預設會被防火牆擋住
HOST = "0.0.0.0"


def free_port(preferred=8787):
    for port in (preferred, 0):
        s = socket.socket()
        try:
            s.bind((HOST, port))
            return s.getsockname()[1]
        except OSError:
            continue
        finally:
            s.close()
    return preferred


if getattr(sys, "frozen", False) and not IS_WINDOWS and not IS_MAC:
    # 打包版在 Linux 上帶的是 Qt 後端，指定清楚才不會去找系統的 GTK
    os.environ.setdefault("PYWEBVIEW_GUI", "qt")

setup_ffmpeg()
PORT = free_port()
os.environ.setdefault("XK_PORT", str(PORT))
sys.path.insert(0, str(BASE / "server"))

import server as backend  # noqa: E402  （要先設好環境變數再載入）
import webview  # noqa: E402


def serve():
    try:
        from waitress import serve as wserve
        wserve(backend.app, host=HOST, port=PORT, threads=16)
    except ImportError:
        backend.app.run(host=HOST, port=PORT, threaded=True)


class Api:
    """給網頁呼叫的桌面功能。"""

    def version(self):
        return {"version": APP_VERSION, "name": APP_NAME}

    def open_folder(self, path=None):
        target = Path(path or backend.DOWNLOAD_DIR)
        try:
            target.mkdir(parents=True, exist_ok=True)
            if IS_WINDOWS:
                os.startfile(str(target))                       # noqa: S606
            elif IS_MAC:
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
            return {"ok": True}
        except (OSError, subprocess.SubprocessError) as e:
            return {"ok": False, "error": str(e)}

    def pick_folder(self):
        win = webview.windows[0]
        picked = win.create_file_dialog(
            webview.FOLDER_DIALOG, directory=str(backend.DOWNLOAD_DIR))
        if not picked:
            return {"ok": False, "canceled": True}
        folder = picked[0] if isinstance(picked, (list, tuple)) else picked
        backend.set_download_dir(folder)
        return {"ok": True, "download_dir": str(backend.DOWNLOAD_DIR)}

    def check_update(self):
        try:
            req = urllib.request.Request(UPDATE_URL, headers={"User-Agent": "xiaoke-youtube"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode("utf-8"))
            latest = str(data.get("version") or "").strip()
            return {
                "ok": True,
                "current": APP_VERSION,
                "latest": latest,
                "newer": is_newer(latest, APP_VERSION),
                "notes": data.get("notes") or "",
                "page": data.get("page") or RELEASE_PAGE,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def open_release_page(self):
        import webbrowser
        webbrowser.open(RELEASE_PAGE)
        return {"ok": True}

    def open_youtube(self):
        open_youtube_window()
        return {"ok": True}


# ---------------------------------------------------------------- 內建 YouTube 視窗

def backend_call(path, body=None, timeout=60):
    """在程式這一側呼叫本機後端：YouTube 是 https 頁面，從網頁直接連本機 http 會被擋，
    所以影片上的下載標籤都透過這裡轉送。"""
    url = "http://127.0.0.1:%d%s" % (PORT, path)
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "error": "HTTP %d" % e.code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class YouTubeApi:
    """給 YouTube 視窗裡「下載這個視訊」標籤用的橋接，對應 web/yt-overlay.js 的 __xkCall。"""

    def info(self, args):
        return backend_call("/api/info", {"url": args.get("url")}, timeout=90)

    def start(self, args):
        return backend_call("/api/jobs", args)

    def poll(self, args):
        d = backend_call("/api/jobs/%s" % args.get("id"))
        if d.get("ok"):
            d["finish_label"] = "開啟資料夾"
        return d

    def finish(self, args):
        return Api().open_folder()


# 注入在 overlay 前面：把 __xkCall 接到 pywebview 的 js_api
_BRIDGE_JS = """
window.__xkCall = function (m, a) {
  return new Promise(function (resolve, reject) {
    function go() { window.pywebview.api[m](a).then(resolve, reject); }
    if (window.pywebview && window.pywebview.api && window.pywebview.api[m]) go();
    else window.addEventListener('pywebviewready', go, { once: true });
  });
};
"""

_yt_window = None


def open_youtube_window():
    global _yt_window
    if _yt_window is not None:
        try:
            _yt_window.show()
            _yt_window.restore()
            return
        except Exception:
            _yt_window = None

    overlay = (BASE / "web" / "yt-overlay.js").read_text(encoding="utf-8")
    win = webview.create_window(
        "YouTube — 小柯機器人（影片右上角有「下載這個視訊」）",
        "https://www.youtube.com/",
        width=1280, height=860, min_size=(480, 400),
        js_api=YouTubeApi(),
    )

    def inject():
        # YouTube 偶爾會先跳去 Google 做「背景登入檢查」（網址帶 passive=true），
        # 在內嵌視窗裡有時會卡在那一頁，一般人會以為非登入不可——直接帶回 YouTube。
        # 使用者自己按「登入」的頁面沒有 passive=true，不會被干涉。
        try:
            url = win.get_current_url() or ""
            if "accounts.google.com" in url and "passive=true" in url:
                win.load_url("https://www.youtube.com/")
                return
        except Exception:
            pass
        # 每次整頁載入都重新注入；YouTube 站內換影片不會整頁載入，由 overlay 自己追蹤
        try:
            win.evaluate_js(_BRIDGE_JS + overlay)
        except Exception as e:
            print("注入下載標籤失敗：", e, flush=True)

    def closed():
        global _yt_window
        _yt_window = None

    win.events.loaded += inject
    win.events.closed += closed
    _yt_window = win


def is_newer(latest, current):
    def parts(v):
        out = []
        for chunk in str(v).split("."):
            digits = "".join(c for c in chunk if c.isdigit())
            out.append(int(digits or 0))
        return out
    a, b = parts(latest), parts(current)
    size = max(len(a), len(b))
    a += [0] * (size - len(a))
    b += [0] * (size - len(b))
    return a > b


def main():
    print("%s v%s　後端埠號 %d" % (APP_NAME, APP_VERSION, PORT), flush=True)
    threading.Thread(target=serve, daemon=True).start()

    window = webview.create_window(
        APP_NAME,
        "http://127.0.0.1:%d/" % PORT,
        width=1000, height=820, min_size=(420, 620),
        background_color="#0d1117",
        js_api=Api(),
    )
    window.events.closed += lambda: os._exit(0)   # 關閉視窗＝停止所有執行

    # Linux／macOS 的視窗圖示要另外指定，Windows 是用 exe 自己的圖示
    icon = BASE / "web" / "icon-512.png"
    try:
        if not IS_WINDOWS and icon.exists():
            webview.start(icon=str(icon))
        else:
            webview.start()
    except TypeError:
        # 舊版 pywebview 不吃 icon 參數
        webview.start()
    os._exit(0)


if __name__ == "__main__":
    main()
