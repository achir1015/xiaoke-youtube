#!/usr/bin/env bash
# 小柯機器人 YouTube 下載工具 - macOS 版建置腳本（要在 Mac 上執行）
# 用法（在專案根目錄）： bash desktop/build-mac.sh
# 產出： dist/XiaokeYouTube-mac-<arm64|x86_64>-v<版本>.dmg
#        打開 dmg，把「小柯YT下載」拖進「應用程式」就裝好了

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ARCH="$(uname -m)"     # Apple 晶片是 arm64，Intel 是 x86_64
VERSION="$(python3 -c "import json;print(json.load(open('version.json',encoding='utf-8'))['version'])")"
APP_NAME="小柯YT下載"
echo "[小柯] 建置 macOS $ARCH 版本 $VERSION"

echo "[小柯] 安裝相依套件..."
python3 -m pip install --quiet --disable-pip-version-check \
  -r server/requirements.txt -r server/requirements-stt.txt pyinstaller pywebview

if [ ! -x ffmpeg/ffmpeg ]; then
  echo "[小柯] 下載 ffmpeg（靜態編譯版，不依賴 Homebrew）..."
  mkdir -p ffmpeg
  tmp="$(mktemp -d)"
  for tool in ffmpeg ffprobe; do
    curl -fsSL -o "$tmp/$tool.zip" \
      "https://ffmpeg.martin-riedl.de/redirect/latest/macos/${ARCH}/release/${tool}.zip"
    unzip -o -q "$tmp/$tool.zip" -d "$tmp/$tool"
    find "$tmp/$tool" -type f -name "$tool" -exec cp {} ffmpeg/ \;
  done
  rm -rf "$tmp"
  chmod +x ffmpeg/ffmpeg ffmpeg/ffprobe
fi
./ffmpeg/ffmpeg -hide_banner -version | head -1

echo "[小柯] 產生 App 圖示..."
rm -rf build/icon.iconset && mkdir -p build/icon.iconset
for s in 16 32 128 256 512; do
  sips -z "$s" "$s" web/icon-512.png --out "build/icon.iconset/icon_${s}x${s}.png" > /dev/null
  d=$((s * 2))
  sips -z "$d" "$d" web/icon-512.png --out "build/icon.iconset/icon_${s}x${s}@2x.png" > /dev/null
done
iconutil -c icns build/icon.iconset -o build/XiaokeYouTube.icns

echo "[小柯] 打包中..."
rm -rf "dist/$APP_NAME.app" dist/XiaokeYouTube
python3 -m PyInstaller desktop/app.spec --noconfirm --distpath dist --workpath build/pyi
[ -d "dist/$APP_NAME.app" ] || { echo "打包失敗：找不到 $APP_NAME.app"; exit 1; }

# 沒有 Apple 開發者帳號，只能做「臨時簽章」（ad-hoc）。
# Apple 晶片上沒簽章的程式完全不能執行，臨時簽章至少能讓使用者在「隱私權與安全性」按「仍要打開」。
codesign --force --deep --sign - "dist/$APP_NAME.app"
codesign --verify --deep --strict "dist/$APP_NAME.app"
echo "[小柯] 簽章檢查通過"

echo "[小柯] 製作 dmg..."
STAGE="build/dmg"
rm -rf "$STAGE" && mkdir -p "$STAGE"
cp -R "dist/$APP_NAME.app" "$STAGE/"
ln -s /Applications "$STAGE/應用程式"          # 打開 dmg 就看得到，直接拖過去
DMG="dist/XiaokeYouTube-mac-${ARCH}-v${VERSION}.dmg"
rm -f "$DMG"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" -ov -format UDZO "$DMG" > /dev/null

echo "[小柯] 完成：$DMG（$(du -h "$DMG" | cut -f1)）"
