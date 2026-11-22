#!/bin/bash
# ============================================================
#  Construit l'application Vision Agricole pour macOS
#  (équivalent de build_exe.bat pour Windows).
#
#  À lancer UNE FOIS, sur un Mac (PyInstaller ne sait pas
#  construire une app Mac depuis Windows ou Linux) :
#
#      chmod +x build_mac.sh
#      ./build_mac.sh
#
#  Résultat : dist/Vision Agricole.app  (un seul « fichier » pour
#  l'utilisateur dans le Finder, mais en réalité un dossier : c'est
#  la forme normale d'une app Mac, le mode fichier unique de Windows
#  n'existe pas pour les apps graphiques sur Mac).
#
#  Docker Desktop + le moteur NodeODM restent nécessaires sur le Mac
#  qui fait le traitement (voir README.md).
# ============================================================
set -e
cd "$(dirname "$0")"

echo "Vérification de Python 3..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERREUR : Python 3 est introuvable."
    echo "Installez-le depuis https://www.python.org/downloads/macos/"
    exit 1
fi

echo "Vérification de Tkinter (interface graphique)..."
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "ERREUR : Tkinter est absent de ce Python."
    echo "Installez Python depuis https://www.python.org/downloads/macos/"
    echo "(ou, avec Homebrew : brew install python-tk)"
    exit 1
fi

echo "Nettoyage des anciennes constructions..."
rm -rf dist build "Vision Agricole.spec"

echo "Création d'un environnement de construction isolé (.venv_build)..."
python3 -m venv .venv_build
# shellcheck disable=SC1091
source .venv_build/bin/activate

echo "Installation des dépendances (une seule commande)..."
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt pyinstaller

echo "Vérification des imports..."
python -c "import pyodm, rasterio, numpy, sklearn, matplotlib, reportlab, pypdf, PIL, tkinter, customtkinter, shapefile, ezdxf, contourpy" || {
    echo "ERREUR : une dépendance s'installe mais ne s'importe pas."
    exit 1
}

echo
echo "Construction de l'application (plusieurs minutes)..."
python -m PyInstaller --noconfirm --windowed --onedir \
    --name "Vision Agricole" \
    --collect-all rasterio \
    --collect-all matplotlib \
    --collect-all sklearn \
    --collect-all reportlab \
    --collect-all pypdf \
    --collect-all pyodm \
    --collect-all customtkinter \
    --collect-all ezdxf \
    --collect-all contourpy \
    main.py

if [ ! -d "dist/Vision Agricole.app" ]; then
    echo "ERREUR : dist/Vision Agricole.app n'a pas été créé."
    exit 1
fi

echo
echo "============================================================"
echo " SUCCÈS !"
echo "   $(pwd)/dist/Vision Agricole.app"
echo
echo " Premier lancement : macOS peut refuser d'ouvrir une app non"
echo " signée. Faites un clic droit sur l'app > Ouvrir > Ouvrir."
echo " Si l'app vous a été envoyée par e-mail ou téléchargée, lancez"
echo " d'abord dans le Terminal :"
echo "   xattr -dr com.apple.quarantine \"Vision Agricole.app\""
echo "============================================================"
