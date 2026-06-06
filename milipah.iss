[Setup]
AppName=Milipah
AppVersion=1.0.0
DefaultDirName={autopf}\Milipah
DefaultGroupName=Milipah
OutputDir=installer
OutputBaseFilename=Milipah-Setup
Compression=lzma2
SolidCompression=yes
SetupIconFile=assets\setup_icon.ico
UninstallDisplayIcon={app}\Milipah.exe

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\Milipah\Milipah.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Milipah\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Milipah"; Filename: "{app}\Milipah.exe"
Name: "{group}\Uninstall Milipah"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Milipah"; Filename: "{app}\Milipah.exe"; Tasks: desktopicon
