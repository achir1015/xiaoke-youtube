; 小柯機器人 YouTube 下載工具 - Windows 安裝檔
; 建置： ISCC.exe /DMyAppVersion=1.0.0 desktop\installer.iss

#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

#define MyAppName "小柯機器人 YouTube 下載工具"
#define MyAppExe "XiaokeYouTube.exe"
#define MyAppPublisher "achir1015"
#define MyAppURL "https://github.com/achir1015/xiaoke-youtube"

[Setup]
AppId={{9C1D6B2E-4A77-4C1B-9E2A-7B5F0D31C0A1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\XiaokeYouTube
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=XiaokeYouTube-Setup-v{#MyAppVersion}
SetupIconFile=..\web\favicon.ico
UninstallDisplayIcon={app}\{#MyAppExe}
UninstallDisplayName={#MyAppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
; 預設裝在使用者自己的資料夾，不跳 UAC；需要時仍可選擇安裝給所有使用者
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline

[Languages]
Name: "default"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut（建立桌面捷徑）"; GroupDescription: "Shortcuts:"

[Files]
Source: "..\dist\XiaokeYouTube\{#MyAppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\XiaokeYouTube\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Launch now（立即啟動）"; Flags: nowait postinstall skipifsilent
