# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 設定：小柯機器人 YouTube 下載工具（Windows 桌面版）

建置：
    pyinstaller desktop/app.spec --noconfirm
輸出：
    dist/XiaokeYouTube/XiaokeYouTube.exe
"""
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).parent          # noqa: F821  （SPECPATH 由 PyInstaller 提供）
MAC_ICON = ROOT / "build" / "XiaokeYouTube.icns"

datas = [
    (str(ROOT / "web"), "web"),
    (str(ROOT / "server" / "server.py"), "server"),
    (str(ROOT / "server" / "stt.py"), "server"),
    (str(ROOT / "server" / "mt.py"), "server"),
    (str(ROOT / "version.json"), "."),
]
binaries = []
hiddenimports = ["waitress", "flask", "jinja2", "werkzeug"]

# yt-dlp 的解析器與語音辨識套件都是動態載入的，要整包收進來
for pkg in ("yt_dlp", "faster_whisper", "ctranslate2", "opencc", "av", "tokenizers",
            "sentencepiece"):
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
    if sys.platform == "darwin":
        # macOS 的執行檔要放在 Frameworks 才會被簽章，放在 Resources 會讓整個 .app 簽章失效
        for tool in ("ffmpeg", "ffprobe"):
            if (ffmpeg_dir / tool).exists():
                binaries.append((str(ffmpeg_dir / tool), "ffmpeg"))
    else:
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
    # Windows 用 .ico、macOS 用 .icns（build-mac.sh 產生）；Linux 的視窗圖示由程式啟動時指定
    icon=(str(ROOT / "web" / "favicon.ico") if sys.platform == "win32"
          else str(MAC_ICON) if sys.platform == "darwin" and MAC_ICON.exists()
          else None),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="XiaokeYouTube",
)

if sys.platform == "darwin":
    import json
    version = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"]
    app = BUNDLE(                                   # noqa: F821
        coll,
        name="小柯YT下載.app",
        icon=str(MAC_ICON) if MAC_ICON.exists() else None,
        bundle_identifier="com.achir.xiaokeyoutube",
        version=version,
        info_plist={
            "CFBundleName": "小柯YT下載",
            "CFBundleDisplayName": "小柯YT下載",
            "CFBundleShortVersionString": version,
            "CFBundleVersion": version,
            "LSMinimumSystemVersion": "11.0",
            "NSHighResolutionCapable": True,
            # 視窗載入的是本機後端的 http 頁面，要允許區域網路的明文連線
            "NSAppTransportSecurity": {"NSAllowsLocalNetworking": True},
            "NSLocalNetworkUsageDescription": "讓同一個 Wi-Fi 裡的手機可以連到這台 Mac 下載影片。",
        },
    )
