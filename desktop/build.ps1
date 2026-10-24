# 小柯機器人 YouTube 下載工具 - Windows 桌面版建置腳本
# 用法（在專案根目錄）：  powershell -ExecutionPolicy Bypass -File desktop\build.ps1
# 參數：
#   -WithFfmpeg   一併下載 ffmpeg 打包進去（使用者就不必自己裝）
#   -WithInstaller 建置完再用 Inno Setup 產生安裝檔

param(
  [switch]$WithFfmpeg,
  [switch]$WithInstaller
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# 一定要指定 UTF8，否則 Windows PowerShell 會用系統編碼讀，中文會壞掉
$version = (Get-Content "$root\version.json" -Raw -Encoding UTF8 | ConvertFrom-Json).version
Write-Host "[小柯] 建置版本 $version"

Write-Host "[小柯] 安裝相依套件..."
python -m pip install --quiet --disable-pip-version-check -r server\requirements.txt -r server\requirements-stt.txt pywebview pyinstaller

if ($WithFfmpeg) {
  $ffdir = "$root\ffmpeg"
  if (-not (Test-Path "$ffdir\ffmpeg.exe")) {
    Write-Host "[小柯] 下載 ffmpeg..."
    New-Item -ItemType Directory -Force $ffdir | Out-Null
    $zip = "$env:TEMP\ffmpeg-release.zip"
    Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zip
    $tmp = "$env:TEMP\ffmpeg-extract"
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
    Expand-Archive $zip -DestinationPath $tmp
    Get-ChildItem $tmp -Recurse -Include ffmpeg.exe, ffprobe.exe |
      ForEach-Object { Copy-Item $_.FullName $ffdir -Force }
    Remove-Item $zip -Force
  }
  Write-Host "[小柯] ffmpeg 已就緒"
}

Write-Host "[小柯] 打包中..."
Remove-Item -Recurse -Force "$root\dist\XiaokeYouTube" -ErrorAction SilentlyContinue
python -m PyInstaller desktop\app.spec --noconfirm --distpath dist --workpath build
if (-not (Test-Path "$root\dist\XiaokeYouTube\XiaokeYouTube.exe")) { throw "打包失敗" }

if ($WithInstaller) {
  $iscc = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
  ) | Where-Object { Test-Path $_ } | Select-Object -First 1
  if (-not $iscc) { throw "找不到 Inno Setup 6（ISCC.exe），請先安裝： winget install JRSoftware.InnoSetup" }
  Write-Host "[小柯] 產生安裝檔..."
  & $iscc "/DMyAppVersion=$version" "$root\desktop\installer.iss"
}

Write-Host "[小柯] 完成：dist\XiaokeYouTube\XiaokeYouTube.exe"
