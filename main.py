#!/usr/bin/env python3
"""
Point d'entrée de l'application.

Lancement (mode développement) :
    python3 main.py

Construit en exécutable Windows unique (--onefile) par build_exe.bat : le
dossier "app/" est intégré à l'intérieur de Vision Agricole.exe au moment
de la construction, comme le reste du code. Un correctif futur demande donc
de relancer build_exe.bat en entier — il n'y a plus de fichier .py externe
à remplacer à côté de l'exe (contrepartie du fichier unique demandé).

Installation des dépendances
-----------------------------
Toutes les dépendances (pyodm, rasterio, scikit-learn, reportlab, pypdf,
matplotlib, Pillow) doivent être installées AVANT de lancer ce script ou de
construire l'exécutable. C'est build_exe.bat qui s'en charge automatiquement,
module par module, avec vérification explicite de chacun avant de procéder
à la construction (voir README.md, section "Construire la version portable").
"""
import sys

try:
    from app.gui import run_app
except ModuleNotFoundError as exc:
    # Ne devrait normalement jamais arriver : build_exe.bat vérifie toutes
    # les dépendances avant de construire. Si ça arrive quand même (version
    # de l'exe construite avec un ancien script, par exemple), on affiche un
    # message clair au lieu de laisser l'application disparaître en silence.
    message = (
        "L'application n'a pas pu démarrer car un composant manque dans "
        f"cette version installée ({exc.name or exc}).\n\n"
        "Il faut reconstruire l'exécutable avec la dernière version de "
        "build_exe.bat, qui installe et vérifie toutes les dépendances "
        "avant de construire.\n\n"
        "Contactez le support technique avec ce message."
    )
    try:
        import tkinter
        from tkinter import messagebox
        _root = tkinter.Tk()
        _root.withdraw()
        messagebox.showerror("Erreur de démarrage", message)
    except Exception:
        print(message, file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    run_app()
