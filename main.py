#!/usr/bin/env python3
"""
Point d'entrée de Vision Agricole.

    python main.py              -> nouvelle interface (page web dans une fenêtre, PyWebView)
    python main.py --classique  -> ancienne interface CustomTkinter

Si la nouvelle interface ne peut pas démarrer (PyWebView absent, ou moteur
d'affichage WebView2 manquant sur un vieux Windows), l'application bascule
automatiquement sur l'interface classique au lieu de ne rien afficher.

Diagnostic : chaque démarrage écrit un journal dans
    %LOCALAPPDATA%\\VisionAgricole\\demarrage.log   (Windows)
    ~/.vision_agricole/demarrage.log                (Mac/Linux)
y compris les plantages brutaux (grâce à faulthandler). Si l'application
s'ouvre puis se ferme aussitôt, c'est ce fichier qu'il faut lire.
"""
import os
import sys
import time
import traceback
from pathlib import Path


def _log_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    d = Path(base) / "VisionAgricole" if base else Path.home() / ".vision_agricole"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


LOG_PATH = _log_dir() / "demarrage.log"
_log_file = None


def log(message: str) -> None:
    try:
        _log_file.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")
        _log_file.flush()
    except Exception:
        pass


def _open_log() -> None:
    global _log_file
    try:
        _log_file = open(LOG_PATH, "w", encoding="utf-8", buffering=1)
        log(f"Démarrage de Vision Agricole — Python {sys.version.split()[0]}, "
            f"{sys.platform}, exécutable figé : {getattr(sys, 'frozen', False)}")
        import faulthandler  # trace même les plantages hors Python (DLL, WebView2...)
        faulthandler.enable(file=_log_file, all_threads=True)
    except Exception:
        _log_file = None


def _show_fatal(message: str) -> None:
    log("ERREUR FATALE : " + message)
    try:
        import tkinter
        from tkinter import messagebox
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror("Vision Agricole — erreur de démarrage", message)
        root.destroy()
        return
    except Exception:
        pass
    if os.name == "nt":  # dernier recours : boîte de message Windows native
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "Vision Agricole — erreur de démarrage", 0x10)
        except Exception:
            pass
    print(message, file=sys.stderr)


def run_classic() -> None:
    log("Lancement de l'interface classique (CustomTkinter)...")
    from app.gui import run_app
    run_app()


def main() -> None:
    _open_log()
    if "--classique" in sys.argv:
        run_classic()
        return
    try:
        log("Lancement de la nouvelle interface (PyWebView)...")
        from app.webview_app import run_app as run_web
        run_web()
        log("Fenêtre fermée normalement.")
    except Exception:
        log("Échec de la nouvelle interface :\n" + traceback.format_exc())
        run_classic()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:
        trace = traceback.format_exc()
        log(trace)
        _show_fatal(
            "L'application n'a pas pu démarrer.\n\n"
            f"{trace.strip().splitlines()[-1]}\n\n"
            f"Le détail est enregistré dans :\n{LOG_PATH}"
        )
        sys.exit(1)
