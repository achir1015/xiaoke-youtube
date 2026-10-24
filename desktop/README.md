# 小柯機器人 YouTube 下載工具 — Windows 11 桌面版

把後端服務包進一個原生視窗：**打開就能用，不用命令列；關掉視窗就停止所有執行**。

## 直接執行（開發用）

```
pip install -r server/requirements.txt pywebview
python desktop/app.py
```

## 建置成 exe

```powershell
powershell -ExecutionPolicy Bypass -File desktop\build.ps1
```

| 參數 | 作用 |
| --- | --- |
| `-WithFfmpeg` | 一併下載 ffmpeg 打包進去，使用者就不用自己安裝 |
| `-WithInstaller` | 建置完再用 Inno Setup 產生安裝檔（需先 `winget install JRSoftware.InnoSetup`） |

輸出：

- `dist\XiaokeYouTube\XiaokeYouTube.exe`（免安裝版，約 290 MB；含 ffmpeg 約 390 MB）
- `dist\XiaokeYouTube-Setup-v<版本>.exe`（安裝檔，會建立開始功能表與桌面捷徑）

## 桌面版多了什麼

打開右上角 ⚙ 會出現「桌面版」區塊：

- **開啟下載資料夾** — 直接用檔案總管打開
- **變更資料夾** — 原生資料夾選擇視窗，之後的下載都會存到新位置
- **檢查更新** — 比對 GitHub 上的 `version.json`，有新版就開啟下載頁

另外：

- **語音轉文字已內建**，不必另外安裝；第一次用某個辨識模型時會自動下載模型檔，
  存在 `%LOCALAPPDATA%\xiaoke-youtube\whisper`
- 後端只綁 `127.0.0.1`，不對外開放
- 8787 被佔用時會自動換一個可用的埠號，不會跟已經在跑的命令列版打架
- 會優先使用放在程式旁邊 `ffmpeg\` 的 ffmpeg，找不到才用系統 PATH 上的

## 發行新版

1. 改 `version.json` 的 `version`
2. 同步改 `desktop/app.py` 的 `APP_VERSION`（兩邊不一致 CI 會直接失敗）
3. 推上 `main`

GitHub Actions（`.github/workflows/release.yml`）會自動打包、產生安裝檔與免安裝 zip，
並發一版 `v<版本>` 的 Release；App 內的「檢查更新」就會看到。

## 檔案

| 檔案 | 作用 |
| --- | --- |
| `app.py` | 桌面主程式（pywebview 視窗 + 內嵌後端 + 桌面專屬 API） |
| `app.spec` | PyInstaller 打包設定 |
| `build.ps1` | 本機建置腳本 |
| `installer.iss` | Inno Setup 安裝檔腳本 |
