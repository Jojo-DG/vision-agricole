@echo off
REM Garde la fenetre ouverte quoi qu'il arrive (meme en cas d'erreur
REM inattendue), pour pouvoir lire les messages.
if /i not "%~1"=="--dans-console" (
    cmd /k ""%~f0" --dans-console"
    exit /b
)
cd /d "%~dp0"

REM ============================================================
REM  Construit un INSTALLATEUR Windows (VisionAgricole_Installation.exe)
REM  a partir du code. Methode alternative a build_exe.bat.
REM
REM  Pourquoi un installateur ? Le mode "fichier unique" de
REM  build_exe.bat est plus souvent signale a tort par les
REM  antivirus et SmartScreen. Ici on construit un DOSSIER
REM  (PyInstaller --onedir), qu'on emballe dans un seul fichier
REM  d'installation (Inno Setup). Moins de faux positifs, et
REM  l'application demarre plus vite.
REM
REM  Prerequis : Python et les dependances (voir README.md,
REM  section 2.2) et Inno Setup 6 (gratuit, jrsoftware.org).
REM  A lancer DEPUIS le dossier qui contient main.py.
REM ============================================================

if not exist "main.py" (
    echo ERREUR : lancez ce script depuis le dossier qui contient main.py.
    echo Dossier actuel : %cd%
    pause
    exit /b 1
)

echo Nettoyage des anciennes constructions...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "dist_installateur" rmdir /s /q "dist_installateur"

echo.
echo Installation des dependances...
echo Les telechargements s'affichent ci-dessous en temps reel : nom du paquet,
echo taille, barre de progression, debit et temps restant. Un paquet deja
echo installe apparait comme "Requirement already satisfied".
python -m pip install --progress-bar on --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo ERREUR : installation des dependances echouee.
    echo Essayez d'abord build_exe.bat, qui installe module par module
    echo et indique precisement lequel pose probleme.
    pause
    exit /b 1
)
python -m pip install --progress-bar on --disable-pip-version-check pyinstaller
if errorlevel 1 (
    echo ERREUR : installation de PyInstaller echouee.
    pause
    exit /b 1
)

echo.
echo Etape 1/2 : construction du dossier de l'application (plusieurs minutes)...
python -m PyInstaller --noconfirm --windowed --onedir --noupx ^
    --name "Vision Agricole" ^
    --icon "assets\vision_agricole.ico" ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.filedialog ^
    --hidden-import tkinter.messagebox ^
    --hidden-import tkinter.constants ^
    --collect-all rasterio ^
    --collect-all matplotlib ^
    --collect-all sklearn ^
    --collect-all reportlab ^
    --collect-all pypdf ^
    --collect-all pyodm ^
    --collect-all customtkinter ^
    --collect-all ezdxf ^
    --collect-all contourpy ^
    --collect-all webview ^
    --hidden-import clr ^
    --collect-all pythonnet ^
    --collect-all clr_loader ^
    --add-data "app\web_ui;app\web_ui" ^
    main.py
if errorlevel 1 (
    echo ERREUR : PyInstaller a echoue. Lisez le message ci-dessus.
    pause
    exit /b 1
)
if not exist "dist\Vision Agricole\Vision Agricole.exe" (
    echo ERREUR : dist\Vision Agricole\Vision Agricole.exe est introuvable.
    echo Verifiez si un antivirus a bloque des fichiers.
    pause
    exit /b 1
)

echo.
echo Etape 2/2 : creation de l'installateur avec Inno Setup...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" (
    echo.
    echo Inno Setup 6 est introuvable. Installez-le depuis jrsoftware.org,
    echo puis relancez ce script. Le dossier dist\Vision Agricole\ est
    echo deja pret et utilisable tel quel.
    pause
    exit /b 1
)
"%ISCC%" "installer\vision_agricole.iss"
if errorlevel 1 (
    echo ERREUR : Inno Setup a echoue. Lisez le message ci-dessus.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  TERMINE.
echo  Installateur : dist_installateur\VisionAgricole_Installation.exe
echo  Calculez son empreinte avant publication :
echo     certutil -hashfile "dist_installateur\VisionAgricole_Installation.exe" SHA256
echo  Puis testez-le sur un PC propre (voir le plan de test).
echo ============================================================
pause
