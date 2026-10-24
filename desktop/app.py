# -*- coding: utf-8 -*-
"""小柯機器人 YouTube 下載工具 - 桌面版（Windows／Linux／macOS）

把後端服務包進一個原生視窗：打開就能用，不需要命令列；關掉視窗就停止所有執行。
"""
import os
import sys
import json
import socket
import subprocess
import threading
import urllib.request
from pathlib import Path

IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"

APP_VERSION = "1.0.4"
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


def free_port(preferred=8787):
    for port in (preferred, 0):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", port))
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
        wserve(backend.app, host="127.0.0.1", port=PORT, threads=16)
    except ImportError:
        backend.app.run(host="127.0.0.1", port=PORT, threaded=True)


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
