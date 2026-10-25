# 小柯機器人 YouTube 下載工具
<img width="991" height="814" alt="image" src="https://github.com/user-attachments/assets/89a26704-a5ab-424d-ad58-cd026cf9e370" />

把 YouTube 影片存成 **MP4 影片**或 **MP3 音樂**，可以選畫質、整份播放清單一次下載，
還能自動產生**字幕（SRT）**並翻譯成 7 種語言。不用打指令、不用另外裝任何東西。

**👉 [到這裡下載最新版](https://github.com/achir1015/xiaoke-youtube/releases/latest)**　｜　
線上版：<https://achir1015.github.io/xiaoke-youtube/>

---

# 使用說明

## 1. 我該下載哪個檔案？

打開上面的「下載最新版」，往下捲到 **Assets**，依你的裝置挑一個：

| 你的裝置 | 下載這個檔案 |
| --- | --- |
| Windows 10／11 電腦 | `XiaokeYouTube-Setup-v…exe`（安裝版，建議） |
| Windows，不想安裝 | `XiaokeYouTube-portable-v…zip`（解壓縮後直接執行） |
| Mac（M1／M2／M3／M4 等 Apple 晶片） | `XiaokeYouTube-mac-arm64-v…dmg` |
| Mac（舊款 Intel 處理器） | `XiaokeYouTube-mac-x86_64-v…dmg` |
| Linux | `XiaokeYouTube-linux-x86_64-v…tar.gz` |
| Android 手機／平板 | `XiaokeYouTube-v…apk` |

> 不確定 Mac 是哪一種？點左上角  →「關於這台 Mac」，「晶片」寫 Apple M 開頭的選 arm64，
> 寫「處理器 Intel」的選 x86_64。
>
> 電腦版裡面已經包好 Python、ffmpeg 和語音辨識，**不需要另外安裝任何軟體**。

## 2. 安裝

**Windows**
1. 連點兩下 `XiaokeYouTube-Setup-v…exe`
2. 如果出現藍色的「Windows 已保護您的電腦」，按「**其他資訊**」→「**仍要執行**」
3. 一路按「下一步」，完成後桌面與開始功能表會有「小柯YT下載」

**Mac**
1. 打開下載的 `.dmg`，把「小柯YT下載」拖進「**應用程式**」資料夾
2. 第一次打開如果說「無法驗證開發者」：
   到「**系統設定 → 隱私權與安全性**」，捲到最下面按「**仍要打開**」，再按一次「打開」
   （舊版 macOS 也可以在 App 上按右鍵 →「打開」）
3. 問「是否允許尋找區域網路上的裝置」時按「**允許**」，手機才找得到這台 Mac

**Android**
1. 用手機瀏覽器下載 `.apk`，下載完點一下開啟
2. 如果說「為了安全，手機已設定為禁止安裝不明來源的 App」，按「**設定**」→ 打開「**允許這個來源**」→ 返回按「安裝」
3. Android 版是**遙控器**：實際下載由家裡的電腦執行，所以電腦要先裝好電腦版並開著（見下面第 4 點）

**Linux**：解壓縮 `tar.gz`，在資料夾裡執行 `./install.sh`，之後應用程式選單就有「小柯YT下載」。

## 3. 開始下載

1. 打開「小柯YT下載」
2. 把 YouTube 網址貼進輸入框（影片或播放清單都可以），按「**解析**」
3. 選 **MP4**（影片）或 **MP3**（音樂）；MP4 再選畫質，例如 1080p
4. 播放清單可以勾選要哪幾部
5. 按「**開始下載**」，看進度條跑完就好

檔案會存在電腦的「**下載 › 小柯YouTube**」資料夾，按「開啟下載資料夾」就能看到，也可以換位置。

**更簡單的方法：邊看邊下載**　按主畫面的「**📺 瀏覽 YouTube**」，會開一個內建的 YouTube，
看影片時播放器右上角有「**▶ 下載這個視訊**」，點一下選畫質就開始下載。

## 4. 用手機下載（Android）

1. 電腦打開「小柯YT下載」，手機和電腦**連同一個 Wi-Fi**
2. 手機打開小柯 App，它會**自動找到家裡的電腦**，不用輸入任何網址
3. 在 YouTube App 看到想要的影片，按「**分享**」→ 選「**小柯**」，網址會自動帶入
   也可以在小柯 App 裡按「📺 瀏覽 YouTube」邊看邊下載
4. 下載完按「**存到這台裝置**」（內建 YouTube 裡是「**存到手機**」），檔案會進手機的「下載」資料夾

> 找不到電腦？確認電腦上的小柯有開著、兩邊是同一個 Wi-Fi，然後在 App 裡按「**換一台電腦**」重新搜尋。

## 5. 字幕（SRT）與翻譯

- 檔案格式選「**SRT 字幕**」只要字幕；或選 MP4／MP3 時勾「**同時產生字幕**」
- 語言可選自動偵測、繁體中文、簡體中文、英文、越南語、日語、韓語、印尼語
- 「**翻譯成**」可以再翻成上面 7 種語言之一，另外輸出一個字幕檔；勾「**雙語字幕**」則上面原文、下面譯文
- 全部在你自己的電腦上處理，影片不會傳到別的地方
- 第一次使用會自動下載語音／翻譯模型（翻譯模型約 2.8 GB），之後就不用再下載

## 6. 更新

程式會自己檢查新版，有新版時按「**檢查更新**」→ 下載新的安裝檔，照第 2 點再裝一次即可（設定與檔案都會保留）。

## 常見問題

| 問題 | 解決方法 |
| --- | --- |
| 某支影片下載失敗 | 會員限定、私人或需要登入的影片無法下載；其他影片可以稍後再試，或按「檢查更新」更新到最新版 |
| 手機找不到電腦 | 電腦上的小柯要開著、同一個 Wi-Fi；Mac 要在「系統設定 → 隱私權與安全性 → 區域網路」允許小柯 |
| 字幕做很久 | 語音辨識用電腦的處理器運算，大約是影片長度的三分之一到一倍時間；可改用較小的模型加快 |
| Mac 打不開 | 見上面「安裝 → Mac」第 2 步 |

---

# 開發者資訊

以下是給想自己架設或修改程式的人看的。

## 功能一覽

- 貼上網址即可解析影片或**播放清單**（可逐部勾選、全選／反選）
- 選 **MP4 影片** 或 **MP3 音樂**（MP3 自動嵌入封面與曲目資訊）
- MP4 可選解析度：360p／480p／720p／1080p／1440p／2160p（依該影片實際可用的畫質動態列出，優先選 H.264 以求相容性）
- **語音轉文字 SRT 字幕**：在本機辨識語音產生字幕，可選繁體中文、簡體中文、英文、越南語、
  日語、韓語、印尼語，也可以自動偵測；可以單獨只要字幕，或下載影片／音樂時順便產生
- **字幕翻譯**：字幕可再翻成上述 7 種語言之一，另外輸出一個 SRT（時間軸不變），
  也可以選「雙語字幕」（每段上面原文、下面譯文）
- **內建 YouTube 瀏覽（邊看邊下載）**：桌面版與 Android 版按「📺 瀏覽 YouTube」，
  看影片時播放器右上角會出現「▶ 下載這個視訊」，點一下選畫質就下載，不用安裝任何外掛
- 總進度條 + 單部影片進度條，顯示速度與剩餘時間，可中途取消
- 下載完成後可直接存到瀏覽器所在的裝置，檔案同時留在後端的下載資料夾
- 網址列小圖示、可「建立捷徑／加到主畫面」當成 App 使用（PWA）

## 為什麼需要後端？

瀏覽器沒辦法自己把 YouTube 影片抓下來（跨來源限制、簽章解密、串流合併都要在伺服器端做）。
所以網頁是介面，實際下載由後端服務執行 —— 後端可以跑在你自己的電腦上，也可以跑在你的 NAS／伺服器上。

## 從原始碼執行（Windows）

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

### 字幕翻譯

字幕可以再翻成 7 種語言之一，輸出成**另一個 SRT 檔**，時間軸跟原文完全一致：

- 檔名例如 `影片.srt`（原文）→ `影片.英文.srt`（譯文）
- 勾「雙語字幕」則輸出 `影片.雙語(英文).srt`，每段上面是原文、下面是譯文

翻譯同樣在本機進行，用 Google 的 [MADLAD-400](https://huggingface.co/google/madlad400-3b-mt)
（Apache 2.0 授權），跟語音辨識共用 CTranslate2 引擎。第一次翻譯會先下載約 2.8 GB 的模型，
建議電腦至少有 8 GB 記憶體。一支 2～3 分鐘的影片，翻譯大約多花 1 分鐘。

為什麼選它：實測比較過 NLLB-200（詞彙表缺很多中文字，中日韓譯文會出現 ⁇）和
M2M100（日文仍有缺字、韓文會誤譯），MADLAD 的譯文最自然、完全沒有缺字。

## Android 版

`android/` 是一個 Kotlin App：**從 YouTube App 按「分享」就能選小柯**，網址自動帶入並解析。
手機當介面、下載交給你的後端（電腦或 NAS），所以手機不耗電也不佔空間；需要時再按
「存到這台裝置」把檔案拉回手機。安裝與設定見 [android/README.md](android/README.md)。

## 桌面版（Windows 11／macOS／Linux）

`desktop/` 把後端包進一個原生視窗：打開就能用、不用命令列、關掉視窗就停止所有執行，
並多了「開啟／變更下載資料夾」與「檢查更新」，語音辨識也直接內建。

- Windows：安裝檔（開始功能表＋桌面捷徑）或免安裝 zip
- macOS（Apple 晶片）：下載 `.dmg`，打開後把「小柯YT下載」拖進「應用程式」
- Linux：`tar.gz` 解壓後執行 `./install.sh`，會進應用程式選單

桌面版會對區域網路開放，手機和電腦連同一個 Wi-Fi 時，Android App 會自動找到這台電腦。

建置與發行方式見 [desktop/README.md](desktop/README.md)。

## 內建 YouTube 瀏覽（邊看邊下載）

一般使用者不必安裝瀏覽器擴充功能：桌面版與 Android 版的主畫面有「📺 瀏覽 YouTube」，
會開一個內建的 YouTube 視窗，**每支影片的播放器右上角都有「▶ 下載這個視訊」**，
點下去會列出這支影片實際有的畫質（1080p、720p…）、MP3 與 SRT 字幕，點一個就開始下載，
標籤上直接顯示進度；完成後桌面版可開啟資料夾，Android 可「存到手機」。

- 標籤腳本只有一份（`web/yt-overlay.js`），桌面版與 Android 共用
- YouTube 開了 Trusted Types，腳本全部用 DOM API 建立元素，不用 innerHTML
- 影片頁是 https，不能直接連本機 http 的小柯，所以一律透過程式本身的橋接轉送
  （桌面版 pywebview js_api、Android `addJavascriptInterface`）
- 內建視窗沒辦法登入 Google 帳號，會員限定、需要登入的影片無法下載

## YouTube 常駐下載小圖示（進階：Chrome 擴充功能）

`extension/` 是一個 Manifest V3 擴充功能：在 YouTube 影片頁與播放清單頁右下角常駐一個
小柯機器人圖示，點開可以選格式、解析度、下載範圍，並**分派到你設定的任一下載平台**
（這台電腦、NAS、工作電腦……）。安裝與使用方式見 [extension/README.md](extension/README.md)。

## 注意

請只下載你有權利取得的內容，並遵守 YouTube 服務條款與當地法規。
