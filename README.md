# 小柯機器人 YouTube 下載工具

MP4／MP3、自選解析度、支援播放清單、附下載進度條的 YouTube 下載工具。
由 [yt-dlp](https://github.com/yt-dlp/yt-dlp) + ffmpeg 驅動。

> 目前完成：**線上版（網頁介面 + 本機／自架後端）**
> 規劃中：Windows 11、macOS、Android、iPhone、Linux 桌面版，以及 YouTube 頁面上的常駐下載小圖示。

## 功能

- 貼上網址即可解析影片或**播放清單**（可逐部勾選、全選／反選）
- 選 **MP4 影片** 或 **MP3 音樂**（MP3 自動嵌入封面與曲目資訊）
- MP4 可選解析度：360p／480p／720p／1080p／1440p／2160p（依該影片實際可用的畫質動態列出，優先選 H.264 以求相容性）
- 總進度條 + 單部影片進度條，顯示速度與剩餘時間，可中途取消
- 下載完成後可直接存到瀏覽器所在的裝置，檔案同時留在後端的下載資料夾
- 網址列小圖示、可「建立捷徑／加到主畫面」當成 App 使用（PWA）

## 為什麼需要後端？

瀏覽器沒辦法自己把 YouTube 影片抓下來（跨來源限制、簽章解密、串流合併都要在伺服器端做）。
所以網頁是介面，實際下載由後端服務執行 —— 後端可以跑在你自己的電腦上，也可以跑在你的 NAS／伺服器上。

## 快速開始（Windows）

1. 先確認已安裝 Python 3.9+ 與 ffmpeg：
   ```
   winget install Python.Python.3.12
   winget install Gyan.FFmpeg
   ```
2. 連點兩下 `啟動小柯YouTube下載工具.bat`
   － 第一次會自動安裝 flask／yt-dlp／waitress
   － 自動開啟 <http://127.0.0.1:8787/>
   － 關掉那個黑色視窗，服務就停止

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
| `POST` | `/api/jobs` | `{url, mode:"mp4"\|"mp3", quality, items:[1,3,5], title}` → `job_id` |
| `GET` | `/api/jobs/<id>` | 進度、階段、速度、剩餘時間、完成檔案 |
| `POST` | `/api/jobs/<id>/cancel` | 取消下載 |
| `GET` | `/api/files/<id>/<n>` | 把下載好的檔案傳給瀏覽器 |

## 專案結構

```
server/server.py        後端服務（單檔 Flask + yt-dlp）
web/                    網頁介面（可單獨部署為靜態網站）
tools/make_icons.py     產生 favicon／捷徑圖示
啟動小柯YouTube下載工具.bat  Windows 一鍵啟動
```

## 注意

請只下載你有權利取得的內容，並遵守 YouTube 服務條款與當地法規。
