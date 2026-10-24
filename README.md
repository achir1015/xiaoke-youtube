# 小柯機器人 YouTube 下載工具

MP4／MP3、自選解析度、支援播放清單、附下載進度條的 YouTube 下載工具。
由 [yt-dlp](https://github.com/yt-dlp/yt-dlp) + ffmpeg 驅動。

> 目前完成：**線上版（網頁介面 + 本機／自架後端）**、**YouTube 常駐下載小圖示（瀏覽器擴充功能）**、
> **Windows 11 桌面版**、**Linux 桌面版**、**Android 版**
> 規劃中：macOS 桌面版、iPhone。

## 功能

- 貼上網址即可解析影片或**播放清單**（可逐部勾選、全選／反選）
- 選 **MP4 影片** 或 **MP3 音樂**（MP3 自動嵌入封面與曲目資訊）
- MP4 可選解析度：360p／480p／720p／1080p／1440p／2160p（依該影片實際可用的畫質動態列出，優先選 H.264 以求相容性）
- **語音轉文字 SRT 字幕**：在本機辨識語音產生字幕，可選繁體中文、簡體中文、英文、越南語、
  日語、韓語、印尼語，也可以自動偵測；可以單獨只要字幕，或下載影片／音樂時順便產生
- 總進度條 + 單部影片進度條，顯示速度與剩餘時間，可中途取消
- 下載完成後可直接存到瀏覽器所在的裝置，檔案同時留在後端的下載資料夾
- 網址列小圖示、可「建立捷徑／加到主畫面」當成 App 使用（PWA）

## 為什麼需要後端？

瀏覽器沒辦法自己把 YouTube 影片抓下來（跨來源限制、簽章解密、串流合併都要在伺服器端做）。
所以網頁是介面，實際下載由後端服務執行 —— 後端可以跑在你自己的電腦上，也可以跑在你的 NAS／伺服器上。

## 快速開始（Windows）

到 [Releases](https://github.com/achir1015/xiaoke-youtube/releases/latest) 下載
`XiaokeYouTube-Setup-v<版本>.exe`，安裝完就能用。

**不需要先裝 Python，也不需要先裝 ffmpeg** —— 兩者（還有語音辨識）都已經包在裡面。
裝完是一個獨立的應用程式：開始功能表與桌面都有捷徑，點開是一個原生視窗，
不是瀏覽器分頁，也不用自己去開什麼網址。關掉視窗就停止所有執行。

<details>
<summary>進階：不想安裝，直接從原始碼跑</summary>

這條路才需要自備 Python 3.9+ 與 ffmpeg：

```
winget install Python.Python.3.12
winget install Gyan.FFmpeg
```

然後連點兩下 `啟動小柯YouTube下載工具.bat`，第一次會自動安裝 flask／yt-dlp／waitress，
並開啟 <http://127.0.0.1:8787/>；關掉那個黑色視窗，服務就停止。

</details>

## 手動啟動（macOS／Linux／NAS）

```bash
cd server
pip install -r requirements.txt
python server.py          # 預設 http://0.0.0.0:8787
```

環境變數：

| 變數 | 預設 | 說明 |
| --- | --- | --- |
| `XK_PORT` | `8787` | 服務埠號 |
| `XK_DOWNLOAD_DIR` | `~/Downloads/小柯YouTube` | 下載檔案存放位置 |

## 線上版（GitHub Pages）怎麼搭配

`web/` 這個資料夾就是純靜態網頁，可以直接放上 GitHub Pages。
打開網頁後按右上角 ⚙，把「後端網址」填成你的後端位置即可：

- 本機後端：`http://127.0.0.1:8787`
- 自架後端（建議加上 HTTPS，例如 ngrok／反向代理）：`https://你的網域`

> 從 https 網頁連本機 `127.0.0.1` 的後端，Chrome／Edge 可以直接運作（後端已送出 Private Network Access 標頭）；
> Firefox 則請改用後端自己提供的頁面 <http://127.0.0.1:8787/>。

## API

| 方法 | 路徑 | 說明 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康檢查、yt-dlp 版本、下載資料夾 |
| `POST` | `/api/info` | `{url}` → 影片／播放清單資訊與可用解析度 |
| `POST` | `/api/jobs` | `{url, mode:"mp4"\|"mp3"\|"srt", quality, items:[1,3,5], title, want_srt, srt_lang, srt_model}` → `job_id` |
| `GET` | `/api/jobs/<id>` | 進度、階段、速度、剩餘時間、完成檔案 |
| `POST` | `/api/jobs/<id>/cancel` | 取消下載 |
| `GET` | `/api/files/<id>/<n>` | 把下載好的檔案傳給瀏覽器 |
| `GET` | `/api/stt` | 語音辨識是否可用、支援語言、模型清單 |
| `POST` | `/api/stt/install` | 在這台後端上安裝語音辨識套件 |
| `GET`／`POST` | `/api/settings` | 讀取或切換下載資料夾 |

## 專案結構

```
server/server.py        後端服務（單檔 Flask + yt-dlp）
server/stt.py           語音轉文字 → SRT（faster-whisper + OpenCC 繁簡轉換）
web/                    網頁介面（可單獨部署為靜態網站）
extension/              YouTube 常駐下載小圖示（Chrome／Edge 擴充功能）
desktop/                桌面版（pywebview + PyInstaller；Windows 用 Inno Setup，Linux 出 tar.gz）
android/                Android 版（Kotlin + WebView，可接收 YouTube App 的分享）
tools/make_icons.py     產生 favicon／捷徑圖示／擴充功能圖示
version.json            發行版本號（改這裡並推上 main 就會自動發 Release）
啟動小柯YouTube下載工具.bat  Windows 一鍵啟動（不打包的輕量用法）
```

## 語音轉文字字幕（SRT）

用 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 在**你自己的後端**上辨識，
影片不會送到任何外部服務；中文再用 OpenCC 轉換，確保「繁體」真的是繁體（連「軟件→軟體」
這類用語都會轉）。

- 支援語言：自動偵測、繁體中文、簡體中文、英文、越南語、日語、韓語、印尼語
- 模型：tiny（75 MB）／base（145 MB）／small（484 MB，預設）／medium（1.5 GB），
  第一次使用該模型會自動下載，存在 `%LOCALAPPDATA%\xiaoke-youtube\whisper`
- 用法：檔案格式選「SRT 字幕」只產生字幕；或選 MP4／MP3 時勾「同時產生字幕」，
  字幕會存成跟影片同名的 `.srt`
- 桌面版已內建；網頁版／自架後端可在設定裡按一下「安裝語音辨識」，
  或自己執行 `pip install -r server/requirements-stt.txt`

> 辨識在 CPU 上跑，速度大約是影片長度的三分之一到一倍（看模型大小與機器）。

## Android 版

`android/` 是一個 Kotlin App：**從 YouTube App 按「分享」就能選小柯**，網址自動帶入並解析。
手機當介面、下載交給你的後端（電腦或 NAS），所以手機不耗電也不佔空間；需要時再按
「存到這台裝置」把檔案拉回手機。安裝與設定見 [android/README.md](android/README.md)。

## 桌面版（Windows 11／Linux）

`desktop/` 把後端包進一個原生視窗：打開就能用、不用命令列、關掉視窗就停止所有執行，
並多了「開啟／變更下載資料夾」與「檢查更新」，語音辨識也直接內建。

- Windows：安裝檔（開始功能表＋桌面捷徑）或免安裝 zip
- Linux：`tar.gz` 解壓後執行 `./install.sh`，會進應用程式選單

建置與發行方式見 [desktop/README.md](desktop/README.md)。

## YouTube 常駐下載小圖示

`extension/` 是一個 Manifest V3 擴充功能：在 YouTube 影片頁與播放清單頁右下角常駐一個
小柯機器人圖示，點開可以選格式、解析度、下載範圍，並**分派到你設定的任一下載平台**
（這台電腦、NAS、工作電腦……）。安裝與使用方式見 [extension/README.md](extension/README.md)。

## 注意

請只下載你有權利取得的內容，並遵守 YouTube 服務條款與當地法規。
