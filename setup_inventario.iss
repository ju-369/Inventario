; ----------------------------------------------------------
; Instalador del Sistema de Inventario - Versión Mejorada
; Compatible con Inno Setup 6.5.4
; ----------------------------------------------------------

[Setup]
AppId={{E3B4E1C4-1234-4B5A-98E7-000INVENTARIOAPP}}   ; ID único de la app
AppName=Sistema de Inventario
AppVersion=1.0
AppPublisher=jufelch
AppPublisherURL=https://tusitio.com
DefaultDirName={autopf}\Inventario
DefaultGroupName=Inventario
AllowNoIcons=yes
OutputDir=dist_installer
OutputBaseFilename=Instalador_Inventario
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=images\icon.ico
UninstallDisplayIcon={app}\main.exe
PrivilegesRequired=lowest
LanguageDetectionMethod=locale
ArchitecturesInstallIn64BitMode=x64

; 👇 Permitir reinstalar sobre versiones anteriores (actualización manual)
AlwaysUsePersonalGroup=true
Uninstallable=yes
DisableDirPage=no
DisableProgramGroupPage=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el escritorio"; GroupDescription: "Accesos directos:"
Name: "startmenuicon"; Description: "Crear icono en el menú Inicio"; GroupDescription: "Accesos directos:"

[Files]
; 👇 Archivos principales del programa
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "database.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "ui_utils.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "tabs\*"; DestDir: "{app}\tabs"; Flags: recursesubdirs ignoreversion
Source: "images\icon.ico"; DestDir: "{app}\images"; Flags: ignoreversion

; 👇 Solo copia la base de datos si no existe, así no se pierde en actualizaciones
Source: "inventario.db"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

[Icons]
Name: "{userprograms}\Inventario"; Filename: "{app}\main.exe"
Name: "{userdesktop}\Inventario"; Filename: "{app}\main.exe"; Tasks: desktopicon
Name: "{userstartmenu}\Inventario"; Filename: "{app}\main.exe"; Tasks: startmenuicon


[Run]
Filename: "{app}\main.exe"; Description: "Iniciar Inventario"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; No borrar la base de datos al desinstalar, para conservar registros
Type: files; Name: "{app}\database.db"
