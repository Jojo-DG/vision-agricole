@echo off
REM ============================================================
REM  Construit un executable Windows autonome (.exe) de
REM  l'application, a lancer UNE SEULE FOIS sur un PC qui a
REM  deja Python installe (voir README.md, section 2.2).
REM
REM  Le fichier .exe genere (dist\Vision Agricole.exe) est un
REM  fichier UNIQUE, autonome : il peut etre copie tel quel sur
REM  n'importe quel autre PC Windows, meme sans Python installe
REM  dessus. Pas de dossier a copier autour.
REM
REM  Contrepartie de ce mode "fichier unique" : le code de
REM  l'application est integre a l'interieur de l'exe (plus de
REM  dossier app\ modifiable a cote). Le moindre correctif futur
REM  demande de relancer ce script en entier.
REM
REM  Docker + le moteur NodeODM restent necessaires sur le PC
REM  qui fait le traitement (voir README.md, section 2.3) : ca
REM  ne peut pas etre integre dans l'exe.
REM ============================================================

echo Verification du dossier courant...
if not exist "main.py" (
    echo.
    echo ============================================================
    echo  ERREUR : main.py introuvable dans ce dossier.
    echo  Vous devez lancer ce script DEPUIS le dossier
    echo  drone_report_app ^(celui qui contient main.py^).
    echo  Dossier actuel : %cd%
    echo ============================================================
    pause
    exit /b 1
)

echo Nettoyage des anciennes constructions (dist, build)...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo.
echo Installation des dependances (une seule commande, plus rapide)...
python -m pip install --quiet -r requirements.txt
if errorlevel 1 goto :install_par_module

echo Verification de l'ensemble des dependances...
python -c "import pyodm, rasterio, numpy, sklearn, matplotlib, reportlab, pypdf, PIL, customtkinter, shapefile, ezdxf, contourpy" 2>nul
if errorlevel 1 goto :install_par_module

echo     OK - toutes les dependances sont installees et verifiees.
goto :install_pyinstaller

:install_par_module
echo.
echo ============================================================
echo  Installation groupee incomplete. Installation module par
echo  module pour identifier precisement lequel pose probleme...
echo ============================================================
echo.

echo   - pyodm ...
python -m pip install --quiet pyodm
if errorlevel 1 (
    echo ERREUR : installation de pyodm echouee.
    pause
    exit /b 1
)
python -c "import pyodm" 2>nul
if errorlevel 1 (
    echo ERREUR : pyodm installe mais introuvable a l'import.
    pause
    exit /b 1
)
echo     OK

echo   - rasterio ...
python -m pip install --quiet rasterio
if errorlevel 1 (
    echo ERREUR : installation de rasterio echouee.
    pause
    exit /b 1
)
python -c "import rasterio" 2>nul
if errorlevel 1 (
    echo ERREUR : rasterio installe mais introuvable a l'import.
    pause
    exit /b 1
)
echo     OK

echo   - scikit-learn ...
python -m pip install --quiet scikit-learn
if errorlevel 1 (
    echo ERREUR : installation de scikit-learn echouee.
    pause
    exit /b 1
)
python -c "import sklearn" 2>nul
if errorlevel 1 (
    echo ERREUR : scikit-learn installe mais introuvable a l'import ^(module sklearn^).
    pause
    exit /b 1
)
echo     OK

echo   - reportlab ...
python -m pip install --quiet reportlab
if errorlevel 1 (
    echo ERREUR : installation de reportlab echouee.
    pause
    exit /b 1
)
python -c "import reportlab" 2>nul
if errorlevel 1 (
    echo ERREUR : reportlab installe mais introuvable a l'import.
    pause
    exit /b 1
)
echo     OK

echo   - pypdf ...
python -m pip install --quiet pypdf
if errorlevel 1 (
    echo ERREUR : installation de pypdf echouee.
    pause
    exit /b 1
)
python -c "import pypdf" 2>nul
if errorlevel 1 (
    echo ERREUR : pypdf installe mais introuvable a l'import.
    pause
    exit /b 1
)
echo     OK

echo   - matplotlib ...
python -m pip install --quiet matplotlib
if errorlevel 1 (
    echo ERREUR : installation de matplotlib echouee.
    pause
    exit /b 1
)
python -c "import matplotlib" 2>nul
if errorlevel 1 (
    echo ERREUR : matplotlib installe mais introuvable a l'import.
    pause
    exit /b 1
)
echo     OK

echo   - Pillow ...
python -m pip install --quiet Pillow
if errorlevel 1 (
    echo ERREUR : installation de Pillow echouee.
    pause
    exit /b 1
)
python -c "import PIL" 2>nul
if errorlevel 1 (
    echo ERREUR : Pillow installe mais introuvable a l'import ^(module PIL^).
    pause
    exit /b 1
)
echo     OK

echo   - numpy ...
python -m pip install --quiet numpy
if errorlevel 1 (
    echo ERREUR : installation de numpy echouee.
    pause
    exit /b 1
)
python -c "import numpy" 2>nul
if errorlevel 1 (
    echo ERREUR : numpy installe mais introuvable a l'import.
    pause
    exit /b 1
)
echo     OK

echo   - customtkinter ...
python -m pip install --quiet customtkinter
if errorlevel 1 (
    echo ERREUR : installation de customtkinter echouee.
    pause
    exit /b 1
)
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo ERREUR : customtkinter installe mais introuvable a l'import.
    pause
    exit /b 1
)
echo     OK

echo   - pyshp ...
python -m pip install --quiet pyshp
if errorlevel 1 (
    echo ERREUR : installation de pyshp echouee.
    pause
    exit /b 1
)
python -c "import shapefile" 2>nul
if errorlevel 1 (
    echo ERREUR : pyshp installe mais introuvable a l'import.
    pause
    exit /b 1
)
echo     OK

echo   - ezdxf ...
python -m pip install --quiet ezdxf
if errorlevel 1 (
    echo ERREUR : installation de ezdxf echouee.
    pause
    exit /b 1
)
python -c "import ezdxf" 2>nul
if errorlevel 1 (
    echo ERREUR : ezdxf installe mais introuvable a l'import.
    pause
    exit /b 1
)
echo     OK

echo   - contourpy ...
python -m pip install --quiet contourpy
if errorlevel 1 (
    echo ERREUR : installation de contourpy echouee.
    pause
    exit /b 1
)
python -c "import contourpy" 2>nul
if errorlevel 1 (
    echo ERREUR : contourpy installe mais introuvable a l'import.
    pause
    exit /b 1
)
echo     OK

echo.
echo Toutes les dependances sont installees et verifiees.

:install_pyinstaller

echo Installation de PyInstaller...
python -m pip install --quiet pyinstaller
if errorlevel 1 (
    echo.
    echo ============================================================
    echo  ERREUR : l'installation de PyInstaller a echoue.
    echo  Verifiez que Python et pip fonctionnent ^(python --version^)
    echo  et que vous avez une connexion internet.
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo Construction de l'executable (peut prendre plusieurs minutes)...
python -m PyInstaller --noconfirm --windowed --onefile --noupx ^
    --name "Vision Agricole" ^
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
    main.py
if errorlevel 1 (
    echo.
    echo ============================================================
    echo  ERREUR : PyInstaller a echoue. Faites defiler vers le haut
    echo  pour lire le message d'erreur exact ^(souvent en rouge^),
    echo  et transmettez-le pour diagnostic.
    echo ============================================================
    pause
    exit /b 1
)

if not exist "dist\Vision Agricole.exe" (
    echo.
    echo ============================================================
    echo  ERREUR : PyInstaller s'est termine sans erreur visible mais
    echo  dist\Vision Agricole.exe n'existe pas.
    echo  Verifiez si un antivirus a bloque ou mis en quarantaine
    echo  des fichiers pendant la construction.
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  SUCCES CONFIRME !
echo  L'application est prete, en un seul fichier :
echo    %cd%\dist\Vision Agricole.exe
echo.
echo  Ce seul fichier suffit : copiez-le directement sur les
echo  autres PC, aucun dossier a transporter autour.
echo  ^(Premier lancement un peu plus lent que les suivants : le
echo  fichier se decompresse dans un dossier temporaire a chaque
echo  demarrage.^)
echo ============================================================
pause
