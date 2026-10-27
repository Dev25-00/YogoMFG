; Installeur YogoMFG. Compile avec : ISCC.exe scripts\installer.iss  (apres scripts\build.bat)
#define AppName "YogoMFG"
#define AppVer "0.6.1-beta"

[Setup]
AppId={{6E0B2C0A-5C1D-4B7B-9A55-59F0C0A0F0F1}
AppName={#AppName}
AppVersion={#AppVer}
AppPublisher=Yogo
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\YogoMFG.exe
SetupIconFile=..\assets\yogo.ico
OutputDir=..\dist
OutputBaseFilename=YogoMFG-Setup-{#AppVer}
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
InfoBeforeFile=ANTICHEAT.txt
DisableProgramGroupPage=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Flags: unchecked

[Files]
Source: "..\dist\YogoMFG.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\ANTICHEAT.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README-BETA.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\legal\*"; DestDir: "{app}\legal"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\YogoMFG"; Filename: "{app}\YogoMFG.exe"
Name: "{autodesktop}\YogoMFG"; Filename: "{app}\YogoMFG.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\YogoMFG.exe"; Description: "Lancer YogoMFG"; Flags: nowait postinstall skipifsilent shellexec
