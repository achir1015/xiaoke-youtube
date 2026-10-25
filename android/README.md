# 小柯機器人 YouTube 下載工具 — Android 版

手機上的小柯：**從 YouTube App 按「分享」就能選小柯**，網址會自動帶進去並開始解析，
選好格式、解析度、字幕語言後交給後端下載。

## 它是怎麼運作的

手機上跑不了 yt-dlp 與 ffmpeg（要嘛裝不下，要嘛跑不動），所以 Android 版跟
瀏覽器擴充功能是同一個思路：**手機當介面，實際下載交給你的後端**
（家裡的電腦或 NAS）。好處是手機不耗電、不佔空間，下載完的檔案留在後端，
需要時再按「存到這台裝置」拉回手機。

## 安裝與設定

1. 電腦上打開「小柯YT下載」桌面版（第一次開啟時，若詢問是否允許網路連線，選「允許」）
2. 手機連上**跟電腦同一個 Wi-Fi**
3. 安裝並打開 App——**它會自動找到家裡的電腦並連上，什麼都不用填**

| 情況 | App 的行為 |
| --- | --- |
| 找到 1 台電腦 | 自動連上，直接進入主畫面 |
| 找到好幾台 | 列出電腦名稱，點一下就好 |
| 一台都沒找到 | 用白話說明可能原因，並可按「重新尋找」 |
| 原本的電腦連不上（關機、換了 IP） | 自動重新尋找，不會卡在空白畫面；若是從 YouTube 分享過來的，換好電腦後會接著處理那支影片 |

要換一台電腦，按主畫面左下角的「**換一台電腦**」。手動輸入網址收在設定畫面的「進階」裡，
而且要先連得上才會儲存。

> 原理：App 會詢問手機所在網段的每個位址（埠 8787）是不是小柯，大約 3～5 秒。

## 用法

- **從 YouTube App 分享**：影片頁 → 分享 → 選「小柯YT下載」，自動帶入並解析
- **直接開 App**：貼上網址，跟網頁版完全一樣的介面
- **存到手機**：下載完成後按檔案旁的「存到這台裝置」，交給 Android 下載管理員
  存進手機的「下載」資料夾
- **換電腦**：左下角的「換一台電腦」

## 自己建置

需要 JDK 17 與 Android SDK（compileSdk 35）：

```bash
cd android
gradle assembleDebug          # 產出 app/build/outputs/apk/debug/
```

專案沒有附 Gradle wrapper，請用系統安裝的 Gradle 8.9 以上，或用 Android Studio 開啟。
每次推上 `main` 時 CI 都會自動編譯一次（`.github/workflows/android.yml`），
APK 會留在該次執行的 artifact 裡。

### 正式簽章

發行流程會找這幾個 repository secret，有設定才會用正式金鑰簽，否則是 debug 簽章：

| Secret | 內容 |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | keystore 檔案的 base64 |
| `ANDROID_KEYSTORE_PASSWORD` | keystore 密碼 |
| `ANDROID_KEY_ALIAS` | 金鑰別名 |
| `ANDROID_KEY_PASSWORD` | 金鑰密碼 |

版本號會自動從專案根目錄的 `version.json` 讀，不用在這裡另外改。

## 檔案

| 檔案 | 作用 |
| --- | --- |
| `MainActivity.kt` | WebView 主畫面、分享接收、檔案下載 |
| `SetupActivity.kt` | 後端網址設定與連線測試 |
| `Prefs.kt` | 記住後端網址 |
| `app/build.gradle.kts` | 版本號同步、簽章設定 |
