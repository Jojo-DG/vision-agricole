"""
Interface « web » de Vision Agricole : une page HTML (app/web_ui/index.html)
affichée dans une fenêtre de bureau par PyWebView (moteur WebView2 d'Edge
sous Windows). Le calcul reste celui de app/pipeline.py.

La classe Api est exposée au JavaScript : chaque méthode publique est
appelable depuis la page via window.pywebview.api.<méthode>(...).
"""

from __future__ import annotations

import base64
import io
import json
import os
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

from app.odm_client import ODMClient, ODMProcessingError
from app import pipeline

APP_VERSION = "1.1.0"
SETTINGS_PATH = Path.home() / ".vision_agricole" / "reglages.json"
RESULT_FILE = "resultats_mission.json"
DEFAULT_SETTINGS = {
    "node_host": "localhost",
    "node_port": 3000,
    "output_dir": str(Path.home() / "Documents" / "rapports_drone"),
    "default_quality": pipeline.DEFAULT_QUALITY,
}


def resource_path(relative: str) -> Path:
    """Chemin d'un fichier embarqué, en développement comme dans l'.exe."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / relative


def open_path(path: str) -> bool:
    try:
        if not path or not Path(path).exists():
            return False
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False


def _thumbnail_data_url(path: str, size: int = 320) -> str:
    from PIL import Image
    with Image.open(path) as im:
        try:
            im.draft("RGB", (size * 2, size * 2))  # décodage JPEG réduit : rapide
        except Exception:
            pass
        im = im.convert("RGB")
        im.thumbnail((size, size))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _friendly_error(exc: BaseException) -> tuple[str, str]:
    """Message simple + piste de solution, sans jargon."""
    text = str(exc)
    low = text.lower()
    if isinstance(exc, ODMProcessingError):
        if "connect" in low or "refus" in low or "joindre" in low or "connexion" in low:
            return ("Le moteur de traitement ne répond plus.",
                    "Vérifiez dans Docker Desktop que le conteneur nodeodm est toujours démarré, puis réessayez.")
        if "failed" in low or "échou" in low or "memory" in low or "mémoire" in low:
            return ("Le moteur de traitement a interrompu le calcul.",
                    "C'est souvent un manque de mémoire : choisissez la qualité « Rapide », fermez les autres "
                    "programmes et vérifiez la mémoire accordée à Docker (4 à 5 Go sur un PC de 8 Go).")
        return (text or "Le moteur de traitement a signalé un problème.",
                "Vérifiez que les photos se recouvrent suffisamment, puis réessayez.")
    return ("Une erreur inattendue s'est produite pendant l'analyse.",
            "Réessayez. Si le problème revient, transmettez le fichier journal indiqué dans le détail technique.")


class Api:
    def __init__(self):
        self._window = None
        self._lock = threading.Lock()
        self._job = {"running": False, "stage": 0, "text": "", "pct": 0.0,
                     "start": 0.0, "end": 0.0, "error": None, "result": None}
        self._settings = self._load_settings()

    # Le préfixe "_" empêche PyWebView d'exposer ces attributs au JavaScript.
    def _set_window(self, window):
        self._window = window

    # ------------------------------------------------------------ réglages
    @staticmethod
    def _load_settings() -> dict:
        s = dict(DEFAULT_SETTINGS)
        try:
            s.update(json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
        if s.get("default_quality") not in pipeline.QUALITY_PRESETS:
            s["default_quality"] = pipeline.DEFAULT_QUALITY
        return s

    def get_settings(self):
        return {"settings": self._settings, "version": APP_VERSION}

    def save_settings(self, s: dict):
        merged = dict(self._settings)
        for k in DEFAULT_SETTINGS:
            if k in s and s[k] not in (None, ""):
                merged[k] = s[k]
        try:
            merged["node_port"] = int(merged["node_port"])
        except Exception:
            merged["node_port"] = DEFAULT_SETTINGS["node_port"]
        if merged["default_quality"] not in pipeline.QUALITY_PRESETS:
            merged["default_quality"] = pipeline.DEFAULT_QUALITY
        self._settings = merged
        try:
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        return merged

    # ------------------------------------------------------------ moteur
    def check_engine(self, host, port):
        try:
            ODMClient(str(host or "localhost"), int(port)).connect()
            return {"ok": True, "message": "Le moteur répond."}
        except (ValueError, TypeError):
            return {"ok": False, "message": "Le port doit être un nombre entier (ex : 3000)."}
        except ODMProcessingError:
            return {"ok": False, "message": "Le moteur ne répond pas à cette adresse. Est-il démarré dans Docker ?"}
        except Exception as exc:
            return {"ok": False, "message": f"Connexion impossible : {exc}"}

    # ------------------------------------------------------------ dossiers
    def _folder_dialog(self, title: str):
        import webview
        kind = getattr(getattr(webview, "FileDialog", None), "FOLDER", None)
        if kind is None:
            kind = getattr(webview, "FOLDER_DIALOG")
        res = self._window.create_file_dialog(kind)
        if not res:
            return None
        return res[0] if isinstance(res, (list, tuple)) else res

    def choose_folder(self, title: str = "Choisir un dossier"):
        return self._folder_dialog(title)

    def choose_images_dir(self):
        d = self._folder_dialog("Choisir le dossier des photos du drone")
        if not d:
            return None
        return self.describe_images_dir(d)

    def describe_images_dir(self, d: str):
        images = pipeline.scan_images(d)
        thumbs = []
        for p in images[:5]:
            try:
                thumbs.append({"name": Path(p).name, "src": _thumbnail_data_url(p)})
            except Exception:
                thumbs.append({"name": Path(p).name, "src": ""})
        return {"path": d, "count": len(images), "thumbs": thumbs}

    # ------------------------------------------------------------ mission
    def start_mission(self, params: dict):
        with self._lock:
            if self._job["running"]:
                return {"ok": False, "errors": [["", "Un traitement est déjà en cours."]]}
            try:
                p = pipeline.MissionParams.from_dict(params)
            except Exception as exc:
                return {"ok": False, "errors": [["", f"Paramètres invalides : {exc}"]]}
            if not p.output_dir:
                p.output_dir = self._settings["output_dir"]
            errors = pipeline.validate(p)
            if errors:
                return {"ok": False, "errors": [list(e) for e in errors]}
            try:
                Path(p.output_dir).mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                return {"ok": False, "errors": [["images_dir", f"Impossible d'utiliser le dossier de sortie {p.output_dir} : {exc}"]]}
            self._job = {"running": True, "stage": 0, "text": "Démarrage…", "pct": 0.0,
                         "start": time.time(), "end": 0.0, "error": None, "result": None}
        threading.Thread(target=self._run, args=(p,), daemon=True).start()
        return {"ok": True}

    def _progress(self, stage: int, text: str, pct: float):
        with self._lock:
            self._job["stage"] = max(self._job["stage"], int(stage))
            self._job["text"] = text
            self._job["pct"] = max(self._job["pct"], float(pct))

    def _run(self, p: "pipeline.MissionParams"):
        try:
            result = pipeline.run_mission(p, self._progress)
            level, title, detail = pipeline.health_verdict(result["pct_severe"], result["pct_leger"])
            result.update(verdict_level=level, verdict_title=title, verdict_detail=detail)
            try:
                Path(result["out_dir"], RESULT_FILE).write_text(
                    json.dumps({k: v for k, v in result.items() if k != "maps"},
                               ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
            with self._lock:
                self._job.update(running=False, result=result, end=time.time(), pct=100.0)
        except BaseException as exc:  # noqa: BLE001 - tout doit revenir à l'écran
            trace = traceback.format_exc()
            log = pipeline.write_error_log(trace, p.output_dir)
            message, hint = _friendly_error(exc)
            with self._lock:
                self._job.update(running=False, end=time.time(), error={
                    "message": message, "hint": hint, "detail": trace, "log_path": log})

    def get_progress(self):
        with self._lock:
            j = dict(self._job)
        end = j["end"] or time.time()
        j["elapsed"] = (end - j["start"]) if j["start"] else 0
        return j

    def is_running(self) -> bool:
        return bool(self._job["running"])

    # ------------------------------------------------------------ résultats
    def get_map_image(self, path: str):
        try:
            data = Path(path).read_bytes()
            return "data:image/png;base64," + base64.b64encode(data).decode()
        except Exception:
            return None

    def open_path(self, path: str):
        return open_path(path)

    def open_qgis_folder(self, out_dir: str):
        return open_path(str(Path(out_dir) / "livrables" / "qgis"))

    def load_previous_mission(self):
        d = self._folder_dialog("Choisir le dossier d'une mission (ex : rapports_drone)")
        if not d:
            return None
        return self.read_mission_folder(d)

    def read_mission_folder(self, d: str):
        base = Path(d)
        if base.name == "analyses":
            base = base.parent
        maps = pipeline.find_maps(str(base))
        if not maps:
            return {"error": "Aucune carte de mission n'a été trouvée dans ce dossier."}
        info = {}
        try:
            info = json.loads((base / RESULT_FILE).read_text(encoding="utf-8"))
        except Exception:
            pass
        pdf = base / "rapport_mission_drone.pdf"
        info.update(out_dir=str(base), maps=maps,
                    pdf_path=str(pdf) if pdf.exists() else info.get("pdf_path"))
        if "verdict_title" not in info:
            info["verdict_title"] = "Résultats d'une mission précédente"
            info["verdict_detail"] = "Les chiffres détaillés sont dans le rapport PDF."
            info["verdict_level"] = "ok"
        return info


def run_app() -> None:
    import webview

    api = Api()
    html = resource_path("app/web_ui/index.html")
    window = webview.create_window(
        "Vision Agricole — Agriculture de précision",
        url=str(html),
        js_api=api,
        width=1280, height=820, min_size=(960, 640),
        background_color="#F6F4EF",
    )
    api._set_window(window)

    def on_closing():
        # Empêche de fermer par erreur pendant un traitement.
        if api.is_running():
            try:
                return window.create_confirmation_dialog(
                    "Traitement en cours",
                    "Un traitement est en cours. Si vous fermez l'application, il sera perdu.\n\nFermer quand même ?",
                )
            except Exception:
                return True
        return True

    try:
        window.events.closing += on_closing
    except Exception:
        pass

    webview.start(debug=bool(os.environ.get("VISION_AGRICOLE_DEBUG")))
