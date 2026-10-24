#!/usr/bin/env bash
# 小柯機器人 YouTube 下載工具 - macOS 版建置腳本（要在 Mac 上執行）
# 用法（在專案根目錄）： bash desktop/build-mac.sh
# 產出： dist/XiaokeYouTube-mac-<arm64|x86_64>-v<版本>.dmg
#        打開 dmg，把「小柯YT下載」拖進「應用程式」就裝好了

set -euo pipefail

# 在 CI 上失敗時，把錯誤寫到不用登入就看得到的地方（log 要登入才能看）：
#   1. ::error 註記（顯示在執行頁面上）
#   2. 執行摘要（$GITHUB_STEP_SUMMARY，可放完整 40 行）
# 兩者都直接寫到原始輸出（fd 3），不經過 tee——腳本一結束 GitHub 會把 tee 一起收掉，經過它的輸出會遺失
# 用 EXIT 而不是只用 ERR：明寫的 exit 1 和 set -u（變數未定義）造成的中斷都不會觸發 ERR，
# 但一定會觸發 EXIT。ERR 只負責記下最後失敗的那一行。
STAGE_NAME="開始"
FAIL_LINE="?"
FAIL_CMD="?"
stage() {
  STAGE_NAME="$1"
  echo "[小柯] $1"
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then echo "- $1" >> "$GITHUB_STEP_SUMMARY"; fi
}
if [ -n "${GITHUB_ACTIONS:-}" ]; then
  LOG="$(mktemp)"
  exec 3>&1
  exec > >(tee "$LOG") 2>&1
  trap 'FAIL_LINE="$LINENO"; FAIL_CMD="$BASH_COMMAND"' ERR
  on_exit() {
    local rc=$?
    [ "$rc" -eq 0 ] && return 0
    sleep 1
    local msg
    msg="$(tail -n 20 "$LOG" | tr -d '\r' | sed -e 's/%/%25/g' | awk 1 ORS='%0A')"
    echo "::error title=macOS 建置失敗：${STAGE_NAME}（第 ${FAIL_LINE} 行）::指令：${FAIL_CMD}%0A${msg}" >&3
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
      { echo ""
        echo "### ❌ 失敗於：${STAGE_NAME}（第 ${FAIL_LINE} 行，結束碼 ${rc}）"
        echo ""
        echo "指令：\`${FAIL_CMD}\`"
        echo ""
        echo '```'
        tail -n 40 "$LOG" | tr -d '\r'
        echo '```'
      } >> "$GITHUB_STEP_SUMMARY"
    fi
  }
  trap on_exit EXIT
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    { echo "### macOS 建置進度"; echo "bash ${BASH_VERSION}、$(sw_vers -productVersion 2>/dev/null || echo ?)"; } >> "$GITHUB_STEP_SUMMARY"
  fi
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ARCH="$(uname -m)"     # Apple 晶片是 arm64，Intel 是 x86_64
VERSION="$(python3 -c "import json;print(json.load(open('version.json',encoding='utf-8'))['version'])")"
APP_NAME="小柯YT下載"
stage "建置 macOS $ARCH 版本 $VERSION"

stage "安裝相依套件"
python3 -m pip install --quiet --disable-pip-version-check \
  -r server/requirements.txt -r server/requirements-stt.txt pyinstaller pywebview

if [ ! -x ffmpeg/ffmpeg ]; then
  stage "下載 ffmpeg"
  mkdir -p ffmpeg
  tmp="$(mktemp -d)"
  # 「最新版」捷徑網址只對 ffmpeg.zip 有效（ffprobe 會 404），
  # 所以先解析出 ffmpeg 實際所在的版本目錄，再從同一個目錄抓兩個，版本也一定一致
  # 注意：這個網站對 HEAD 請求不穩定（常回 404），要用 GET 並只讀轉址目標、不跟過去
  LOC="$(curl -fsS -o /dev/null -w '%{redirect_url}' \
    "https://ffmpeg.martin-riedl.de/redirect/latest/macos/${ARCH}/release/ffmpeg.zip")"
  [ -n "$LOC" ] || { echo "找不到 ffmpeg 最新版的下載位置（下載站回應：$(curl -s -o /dev/null -w '%{http_code}' "https://ffmpeg.martin-riedl.de/redirect/latest/macos/${ARCH}/release/ffmpeg.zip")）"; exit 1; }
  FF_DIR="${LOC%/ffmpeg.zip}"
  echo "[小柯] ffmpeg 版本目錄：$FF_DIR"
  for tool in ffmpeg ffprobe; do
    curl -fsSL -o "$tmp/$tool.zip" "$FF_DIR/$tool.zip"
    unzip -o -q "$tmp/$tool.zip" -d "$tmp/$tool"
    find "$tmp/$tool" -type f -name "$tool" -exec cp {} ffmpeg/ \;
  done
  rm -rf "$tmp"
  chmod +x ffmpeg/ffmpeg ffmpeg/ffprobe
fi
# 用 sed 而不是 head：head 提早關管線會讓 ffmpeg 收到 SIGPIPE，在 pipefail 下整支腳本會中斷
./ffmpeg/ffmpeg -hide_banner -version | sed -n 1p

stage "產生 App 圖示"
rm -rf build/icon.iconset && mkdir -p build/icon.iconset
for s in 16 32 128 256 512; do
  sips -z "$s" "$s" web/icon-512.png --out "build/icon.iconset/icon_${s}x${s}.png" > /dev/null
  d=$((s * 2))
  sips -z "$d" "$d" web/icon-512.png --out "build/icon.iconset/icon_${s}x${s}@2x.png" > /dev/null
done
iconutil -c icns build/icon.iconset -o build/XiaokeYouTube.icns

stage "PyInstaller 打包"
rm -rf "dist/$APP_NAME.app" dist/XiaokeYouTube
python3 -m PyInstaller desktop/app.spec --noconfirm --distpath dist --workpath build/pyi
[ -d "dist/$APP_NAME.app" ] || { echo "打包失敗：找不到 $APP_NAME.app"; exit 1; }

# 沒有 Apple 開發者帳號，只能做「臨時簽章」（ad-hoc）。
# Apple 晶片上沒簽章的程式完全不能執行，臨時簽章至少能讓使用者在「隱私權與安全性」按「仍要打開」。
stage "臨時簽章"
codesign --force --deep --sign - "dist/$APP_NAME.app"
codesign --verify --deep --strict "dist/$APP_NAME.app"
echo "[小柯] 簽章檢查通過"

stage "製作 dmg"
STAGE="build/dmg"
rm -rf "$STAGE" && mkdir -p "$STAGE"
cp -R "dist/$APP_NAME.app" "$STAGE/"
ln -s /Applications "$STAGE/應用程式"          # 打開 dmg 就看得到，直接拖過去
DMG="dist/XiaokeYouTube-mac-${ARCH}-v${VERSION}.dmg"
rm -f "$DMG"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" -ov -format UDZO "$DMG" > /dev/null

stage "完成：$DMG（$(du -h "$DMG" | cut -f1)）"
