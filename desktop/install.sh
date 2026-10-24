#!/usr/bin/env bash
# 小柯機器人 YouTube 下載工具 - Linux 安裝／移除腳本
# 用法：
#   ./install.sh            安裝到 ~/.local（不需要 root）
#   sudo ./install.sh -g    安裝到 /opt 與 /usr/local（全系統）
#   ./install.sh -u         移除

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ID="xiaoke-youtube"
BIN_NAME="XiaokeYouTube"

GLOBAL=0
UNINSTALL=0
while getopts "gu" opt; do
  case "$opt" in
    g) GLOBAL=1 ;;
    u) UNINSTALL=1 ;;
    *) echo "用法：$0 [-g 全系統安裝] [-u 移除]"; exit 1 ;;
  esac
done

if [ "$GLOBAL" = "1" ]; then
  APP_DIR="/opt/$APP_ID"
  DESKTOP_DIR="/usr/local/share/applications"
  ICON_DIR="/usr/local/share/icons/hicolor/512x512/apps"
  LINK_DIR="/usr/local/bin"
else
  APP_DIR="$HOME/.local/share/$APP_ID"
  DESKTOP_DIR="$HOME/.local/share/applications"
  ICON_DIR="$HOME/.local/share/icons/hicolor/512x512/apps"
  LINK_DIR="$HOME/.local/bin"
fi

if [ "$UNINSTALL" = "1" ]; then
  rm -rf "$APP_DIR"
  rm -f "$DESKTOP_DIR/$APP_ID.desktop" "$ICON_DIR/$APP_ID.png" "$LINK_DIR/$APP_ID"
  command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_DIR" || true
  echo "[小柯] 已移除。下載過的影片與語音模型不會動到。"
  exit 0
fi

echo "[小柯] 檢查 ffmpeg..."
if ! command -v ffmpeg >/dev/null 2>&1 && [ ! -x "$HERE/ffmpeg/ffmpeg" ]; then
  echo "[小柯] 警告：找不到 ffmpeg，MP3 轉檔、高畫質合併與字幕辨識都會失敗。"
  echo "        Debian/Ubuntu： sudo apt install ffmpeg"
  echo "        Fedora：        sudo dnf install ffmpeg"
  echo "        Arch：          sudo pacman -S ffmpeg"
fi

echo "[小柯] 安裝到 $APP_DIR"
mkdir -p "$APP_DIR" "$DESKTOP_DIR" "$ICON_DIR" "$LINK_DIR"
rm -rf "${APP_DIR:?}/"*
cp -r "$HERE/$BIN_NAME" "$HERE/_internal" "$APP_DIR"/ 2>/dev/null || cp -r "$HERE"/* "$APP_DIR"/
chmod +x "$APP_DIR/$BIN_NAME"

cp "$HERE/icon-512.png" "$ICON_DIR/$APP_ID.png" 2>/dev/null || true
sed "s|__EXEC__|$APP_DIR/$BIN_NAME|" "$HERE/$APP_ID.desktop" > "$DESKTOP_DIR/$APP_ID.desktop"
ln -sf "$APP_DIR/$BIN_NAME" "$LINK_DIR/$APP_ID"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_DIR" || true

echo "[小柯] 完成。可以從應用程式選單開啟，或在終端機執行： $APP_ID"
if [ "$GLOBAL" != "1" ] && ! echo "$PATH" | tr ':' '\n' | grep -qx "$LINK_DIR"; then
  echo "[小柯] 提醒：$LINK_DIR 不在 PATH 裡，終端機指令可能要加完整路徑。"
fi
