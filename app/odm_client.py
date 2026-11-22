"""
odm_client.py

Communique avec un moteur NodeODM (le même moteur de traitement photogrammetrique
que celui utilise par WebODM en interne) pour transformer un dossier de photos
drone en orthomosaïque + MNT (DTM/DSM).

Pourquoi NodeODM et pas WebODM directement ?
---------------------------------------------
WebODM est une application web complète (interface, base de données Postgres,
gestion multi-utilisateurs...) qui délégué le calcul photogrammetrique a un ou
plusieurs "noeuds" NodeODM. Pour une application de bureau utilisée par une
seule équipe, faire tourner uniquement le conteneur NodeODM est beaucoup plus
léger a installer (un seul conteneur Docker, pas de base de données) tout en
utilisant EXACTEMENT le même moteur de traitement (OpenDroneMap) que WebODM.
La bibliothèque officielle "pyodm" (maintenue par OpenDroneMap) est conçue
pour parler a ce type de noeud.

Si l'équipe possède déjà une instance WebODM complète et souhaite l'utiliser
a la place, il suffit de pointer NODE_HOST/NODE_PORT vers le NodeODM interne
de WebODM (généralement accessible sur le port 3001 du conteneur webodm_node-odm_1).
"""

from __future__ import annotations

import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from pyodm import Node
from pyodm.exceptions import NodeConnectionError, NodeResponseError


@dataclass
class ODMTaskResult:
    """Chemins des livrables téléchargés apres traitement."""
    output_dir: Path
    orthophoto_path: Optional[Path] = None
    dsm_path: Optional[Path] = None
    dtm_path: Optional[Path] = None
    point_cloud_path: Optional[Path] = None  # nuage de points (livrable du cahier des charges)
    report_pdf_path: Optional[Path] = None  # rapport technique généré par ODM lui-même
    all_files: list = field(default_factory=list)


class ODMProcessingError(RuntimeError):
    pass


class ODMClient:
    """Enveloppe simple autour de pyodm.Node pour ce projet."""

    # Options de traitement adaptees a un M3E (RGB uniquement, pas de multispectral)
    # Options adaptees a une machine contrainte (8 Go RAM / 4 coeurs) : on
    # désactive les exports que l'application n'utilise pas du tout
    # (glTF 3D, tuiles web du nuage de points, conversion COG), qui
    # consomment de la RAM/CPU en plus sans apporter de livrable utile ici.
    # feature-quality abaisse de "high" a "medium" pour la même raison.
    DEFAULT_OPTIONS = {
        "dsm": True,           # modele de surface (avec végétation/batiments)
        "dtm": True,           # modele de terrain (sol nu) -> topographie/drainage
        "orthophoto-resolution": 2.0,   # cm/pixel, cohérent avec le cahier (2-3 cm)
        "auto-boundary": True,
        "pc-quality": "medium",
        "feature-quality": "medium",
        "pc-ept": False,        # tuiles web du nuage de points : non utilisées, lourd
        "cog": False,           # conversion Cloud-Optimized GeoTIFF : non utilisée, passe supplémentaire
        "gltf": False,          # export 3D glTF : non utilise, très gourmand en RAM
    }

    def __init__(self, host: str = "localhost", port: int = 3000, token: str = ""):
        self.host = host
        self.port = port
        self.token = token
        self._node: Optional[Node] = None

    def connect(self) -> None:
        try:
            self._node = Node(self.host, self.port, token=self.token or "")
            # ping simple : récupérer les infos du noeud
            info = self._node.info()
            if info is None:
                raise ODMProcessingError(
                    "Le noeud NodeODM a répondu mais sans informations valides."
                )
        except NodeConnectionError as exc:
            raise ODMProcessingError(
                f"Impossible de se connecter au moteur de traitement sur "
                f"{self.host}:{self.port}. Vérifiez que le conteneur Docker "
                f"NodeODM est bien demarre (voir README.md).\nDetail : {exc}"
            ) from exc

    def is_connected(self) -> bool:
        return self._node is not None

    def process_images(
        self,
        image_paths: list[str],
        output_dir: str,
        extra_options: Optional[dict] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> ODMTaskResult:
        """
        Envoie les images au moteur de traitement, attend la fin du traitement,
        puis télécharge et extrait les livrables (orthophoto, DSM, DTM, rapport).

        progress_callback(étape, pourcentage) est appelé régulièrement pour
        mettre a jour une barre de progression dans l'interface graphique.
        """
        if self._node is None:
            self.connect()

        if not image_paths:
            raise ODMProcessingError("Aucune image fournie pour le traitement.")

        options = dict(self.DEFAULT_OPTIONS)
        if extra_options:
            options.update(extra_options)

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        def _notify(step: str, pct: float) -> None:
            if progress_callback:
                progress_callback(step, pct)

        _notify("Envoi des images au moteur de traitement...", 0)
        try:
            task = self._node.create_task(
                image_paths,
                options,
                progress_callback=lambda p: _notify("Téléversement des images...", p * 0.15),
            )
        except NodeResponseError as exc:
            raise ODMProcessingError(f"Le moteur de traitement a refusé la tâche : {exc}") from exc

        _notify("Traitement photogrammetrique en cours (alignement, nuage de points, "
                "orthomosaïque, MNT)... Cette étape peut prendre de plusieurs dizaines "
                "de minutes a plusieurs heures selon le nombre de photos.", 15)

        last_pct = 15.0
        consecutive_errors = 0
        max_consecutive_errors = 12  # ~ jusqu'a 4 minutes de tentatives avant abandon
        while True:
            try:
                info = task.info()
                status = info.status.name.lower()
                consecutive_errors = 0
            except NodeConnectionError as exc:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    raise ODMProcessingError(
                        "La connexion au moteur de traitement a été perdue de façon "
                        "répétée pendant le traitement (probablement une coupure "
                        "réseau temporaire cote Docker). Vérifiez que Docker Desktop "
                        "tourne toujours et relancez le traitement.\n"
                        f"Détail : {exc}"
                    ) from exc
                _notify(
                    f"Connexion temporairement interrompue, nouvelle tentative "
                    f"({consecutive_errors}/{max_consecutive_errors})...",
                    last_pct,
                )
                time.sleep(20)
                continue

            if status == "completed":
                break
            if status in ("failed", "canceled"):
                raise ODMProcessingError(
                    f"Le traitement a échoue (statut moteur : {status}). "
                    f"Consultez les journaux du conteneur NodeODM pour le détail."
                )
            running_pct = getattr(info, "progress", None)
            if running_pct is not None:
                # la barre va de 15% (upload fini) a 90% (traitement quasi fini)
                last_pct = 15 + (running_pct * 0.75)
                _notify("Traitement photogrammetrique en cours...", last_pct)
            time.sleep(5)

        _notify("Téléchargement des résultats...", 92)
        zip_path = out_dir / "résultats_odm.zip"
        task.download_zip(str(out_dir), progress_callback=lambda p: _notify(
            "Téléchargement des résultats...", 92 + p * 0.06))

        # pyodm télécharge sous forme d'un zip nommé selon la tâche ; on le localise
        downloaded_zip = None
        for f in out_dir.glob("*.zip"):
            downloaded_zip = f
            break
        if downloaded_zip is None:
            raise ODMProcessingError("Le téléchargement des résultats a échoue (zip introuvable).")

        _notify("Extraction des fichiers...", 98)
        extract_dir = out_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(downloaded_zip, "r") as zf:
            zf.extractall(extract_dir)

        result = ODMTaskResult(output_dir=extract_dir)
        result.all_files = [str(p) for p in extract_dir.rglob("*") if p.is_file()]

        def _find(*name_fragments: str) -> Optional[Path]:
            for p in extract_dir.rglob("*.tif"):
                lname = p.name.lower()
                if all(frag in lname for frag in name_fragments):
                    return p
            return None

        result.orthophoto_path = _find("orthophoto")
        result.dsm_path = _find("dsm")
        result.dtm_path = _find("dtm")

        for p in extract_dir.rglob("report.pdf"):
            result.report_pdf_path = p
            break

        for ext in ("*.laz", "*.las"):
            found = list(extract_dir.rglob(ext))
            if found:
                result.point_cloud_path = found[0]
                break

        _notify("Traitement terminé.", 100)
        return result
