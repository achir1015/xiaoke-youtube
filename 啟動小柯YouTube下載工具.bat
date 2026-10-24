@echo off
chcp 65001 >nul
title 小柯機器人 YouTube 下載工具
cd /d "%~dp0server"

echo [小柯] 檢查相依套件...
python -c "import flask, yt_dlp, waitress" >nul 2>&1
if errorlevel 1 (
  echo [小柯] 第一次啟動，正在安裝 flask / yt-dlp / waitress...
  python -m pip install --quiet --disable-pip-version-check -r requirements.txt
)

where ffmpeg >nul 2>&1
if errorlevel 1 (
  echo [小柯] 警告：找不到 ffmpeg，MP3 轉檔與高畫質合併會失敗。
  echo        請執行： winget install Gyan.FFmpeg
)

echo [小柯] 啟動後端並開啟網頁...
start "" /min cmd /c "timeout /t 2 >nul & start """" http://127.0.0.1:8787/"
python server.py

echo.
echo [小柯] 服務已停止。
pause
