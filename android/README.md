# 小柯機器人 YouTube 下載工具 — Android 版

手機上的小柯：**從 YouTube App 按「分享」就能選小柯**，網址會自動帶進去並開始解析，
選好格式、解析度、字幕語言後交給後端下載。

## 它是怎麼運作的

手機上跑不了 yt-dlp 與 ffmpeg（要嘛裝不下，要嘛跑不動），所以 Android 版跟
瀏覽器擴充功能是同一個思路：**手機當介面，實際下載交給你的後端**
（家裡的電腦或 NAS）。好處是手機不耗電、不佔空間，下載完的檔案留在後端，
需要時再按「存到這台裝置」拉回手機。

## 安裝與設定

1. 先讓後端跑起來（電腦上的桌面版或 `python server/server.py` 都可以）
2. 確認後端監聽的是 `0.0.0.0`（預設就是），而且手機跟電腦在同一個 Wi-Fi
3. 從 Release 下載 `XiaokeYouTube-v<版本>.apk` 安裝
4. 第一次開啟會要你填後端網址，例如 `http://192.168.1.10:8787`
   — 按「測試連線」確認看得到 yt-dlp 版本再儲存

> 電腦的區域網路 IP：Windows 用 `ipconfig`，Linux／macOS 用 `ip addr` 或 `ifconfig` 查。

## 用法

- **從 YouTube App 分享**：影片頁 → 分享 → 選「小柯YT下載」，自動帶入並解析
- **直接開 App**：貼上網址，跟網頁版完全一樣的介面
- **存到手機**：下載完成後按檔案旁的「存到這台裝置」，交給 Android 下載管理員
  存進手機的「下載」資料夾
- **換後端**：左下角的「後端設定」

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
