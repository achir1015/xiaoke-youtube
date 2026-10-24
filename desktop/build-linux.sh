#!/usr/bin/env bash
# 小柯機器人 YouTube 下載工具 - Linux 桌面版建置腳本
# 用法（在專案根目錄）： bash desktop/build-linux.sh [--with-ffmpeg]
# 產出： dist/XiaokeYouTube-linux-x86_64-v<版本>.tar.gz

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WITH_FFMPEG=0
[ "${1:-}" = "--with-ffmpeg" ] && WITH_FFMPEG=1

VERSION="$(python3 -c "import json;print(json.load(open('version.json',encoding='utf-8'))['version'])")"
echo "[小柯] 建置版本 $VERSION"

echo "[小柯] 安裝相依套件..."
python3 -m pip install --quiet --disable-pip-version-check \
  -r server/requirements.txt -r server/requirements-stt.txt \
  pyinstaller "pywebview[qt]"

if [ "$WITH_FFMPEG" = "1" ] && [ ! -x ffmpeg/ffmpeg ]; then
  echo "[小柯] 下載 ffmpeg..."
  mkdir -p ffmpeg
  tmp="$(mktemp -d)"
  curl -sL "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz" \
    -o "$tmp/ff.tar.xz"
  tar -xJf "$tmp/ff.tar.xz" -C "$tmp"
  find "$tmp" -maxdepth 2 -type f \( -name ffmpeg -o -name ffprobe \) -exec cp {} ffmpeg/ \;
  chmod +x ffmpeg/ffmpeg ffmpeg/ffprobe
  rm -rf "$tmp"
fi

echo "[小柯] 打包中..."
rm -rf dist/XiaokeYouTube
python3 -m PyInstaller desktop/app.spec --noconfirm --distpath dist --workpath build
[ -x dist/XiaokeYouTube/XiaokeYouTube ] || { echo "打包失敗"; exit 1; }

echo "[小柯] 組裝安裝包..."
cp desktop/install.sh desktop/xiaoke-youtube.desktop dist/XiaokeYouTube/
cp web/icon-512.png dist/XiaokeYouTube/
chmod +x dist/XiaokeYouTube/install.sh

TARBALL="dist/XiaokeYouTube-linux-x86_64-v${VERSION}.tar.gz"
rm -f "$TARBALL"
tar -czf "$TARBALL" -C dist XiaokeYouTube

echo "[小柯] 完成：$TARBALL"
echo "      解壓後執行 ./install.sh 即可安裝到應用程式選單。"
