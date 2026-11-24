; Script Inno Setup 6 - installateur de Vision Agricole.
; Genere par build_installer.bat (ne pas lancer a la main sans avoir
; d'abord construit dist\Vision Agricole\ avec PyInstaller --onedir).

#define AppName "Vision Agricole"
#define AppVersion "1.0.0"
#define AppPublisher "Groupe 2 - Impact Connexion"
#define AppExe "Vision Agricole.exe"

[Setup]
AppId={{B7C1F7A4-5D2E-4E3B-9A61-2F0C8D4E7A19}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Pas besoin des droits administrateur : installation pour l'utilisateur
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist_installateur
OutputBaseFilename=VisionAgricole_Installation
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\vision_agricole.ico
UninstallDisplayIcon={app}\{#AppExe}
ArchitecturesInstallIn64BitMode=x64compatible
; Si vous ajoutez un fichier LICENSE a la racine du depot, decommentez :
; LicenseFile=..\LICENSE

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Creer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: unchecked

[Files]
Source: "..\dist\Vision Agricole\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Lancer {#AppName}"; Flags: nowait postinstall skipifsilent
