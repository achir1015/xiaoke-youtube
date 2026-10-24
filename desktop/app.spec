# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 設定：小柯機器人 YouTube 下載工具（Windows 桌面版）

建置：
    pyinstaller desktop/app.spec --noconfirm
輸出：
    dist/XiaokeYouTube/XiaokeYouTube.exe
"""
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).parent          # noqa: F821  （SPECPATH 由 PyInstaller 提供）

datas = [
    (str(ROOT / "web"), "web"),
    (str(ROOT / "server" / "server.py"), "server"),
    (str(ROOT / "server" / "stt.py"), "server"),
    (str(ROOT / "version.json"), "."),
]
binaries = []
hiddenimports = ["waitress", "flask", "jinja2", "werkzeug"]

# yt-dlp 的解析器與語音辨識套件都是動態載入的，要整包收進來
for pkg in ("yt_dlp", "faster_whisper", "ctranslate2", "opencc", "av", "tokenizers"):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    except Exception:
        print("[小柯] 略過沒安裝的套件：%s" % pkg)
        continue
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# 如果專案裡放了 ffmpeg，就一起打包（CI 會先下載到 ffmpeg/）
ffmpeg_dir = ROOT / "ffmpeg"
if ffmpeg_dir.is_dir():
    datas.append((str(ffmpeg_dir), "ffmpeg"))

a = Analysis(
    [str(ROOT / "desktop" / "app.py")],
    pathex=[str(ROOT / "server")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="XiaokeYouTube",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ROOT / "web" / "favicon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="XiaokeYouTube",
)
