# 小柯機器人 YouTube 下載工具 — 桌面版（Windows 11／Linux）

把後端服務包進一個原生視窗：**點開就是一個獨立的應用程式**，不是瀏覽器分頁，
使用者不必知道背後有服務在跑、也不用自己開任何網址；關掉視窗就停止所有執行。

打包版**不需要使用者先安裝 Python 或 ffmpeg**：

| 元件 | 怎麼來的 |
| --- | --- |
| Python 直譯器 | PyInstaller 直接包進執行檔，使用者的電腦上完全不需要 Python |
| ffmpeg／ffprobe | 建置時下載、放在程式旁邊，啟動時優先用自己這份，找不到才退回系統 PATH |
| 語音辨識（faster-whisper） | 一起打包，只有辨識模型會在第一次使用時自動下載 |
| flask／yt-dlp 等套件 | 一起打包 |

## 直接執行（開發用，這條才需要自己裝 Python 與 ffmpeg）

```
pip install -r server/requirements.txt pywebview
python desktop/app.py
```

## Linux

**安裝**：從 Release 下載 `XiaokeYouTube-linux-x86_64-v<版本>.tar.gz`，解壓後：

```bash
tar -xzf XiaokeYouTube-linux-x86_64-v1.0.0.tar.gz
cd XiaokeYouTube
./install.sh            # 裝到 ~/.local，不需要 root
```

裝完會出現在應用程式選單，終端機也可以直接打 `xiaoke-youtube`。
`sudo ./install.sh -g` 可以裝到 `/opt` 給全系統用，`./install.sh -u` 移除。

**自己建置**：

```bash
bash desktop/build-linux.sh --with-ffmpeg
```

Linux 版用 Qt 當視窗後端（`pywebview[qt]`），執行時需要這些系統函式庫，
多數桌面發行版已內建，缺的話：

```bash
sudo apt install libnss3 libxkbcommon-x11-0 libxcb-cursor0 libegl1 ffmpeg
```

## 建置成 exe（Windows）

```powershell
powershell -ExecutionPolicy Bypass -File desktop\build.ps1
```

| 參數 | 作用 |
| --- | --- |
| `-WithFfmpeg` | 一併下載 ffmpeg 打包進去，使用者就不用自己安裝 |
| `-WithInstaller` | 建置完再用 Inno Setup 產生安裝檔（需先 `winget install JRSoftware.InnoSetup`） |

輸出：

- `dist\XiaokeYouTube\XiaokeYouTube.exe`（免安裝版，約 290 MB；含 ffmpeg 約 490 MB，
  安裝檔會壓縮過所以下載小很多）
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
