[Setup]
AppName=ThKiosk Helper
AppVersion=1.0.0
DefaultDirName={pf}\ThKiosk Helper
OutputDir=.
OutputBaseFilename=ThKioskHelperInstaller
SetupIconFile=icons\app.ico

[Files]
Source="dist\thkiosk-helper.exe"; DestDir="{app}"

[Registry]
Root: HKCR; Subkey: "thkiosk"; ValueType: string; ValueName: ""; ValueData: "URL:ThKiosk Protocol"
Root: HKCR; Subkey: "thkiosk"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""
Root: HKCR; Subkey: "thkiosk\shell\open\command"; ValueType: string; ValueData: """{app}\thkiosk-helper.exe"" ""%1"""
