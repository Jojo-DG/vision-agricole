"""
Cœur du traitement d'une mission, indépendant de toute interface graphique.

Le contenu reprend à l'identique les étapes de calcul de l'interface
CustomTkinter (app/gui.py, _run_pipeline) : seules les entrées (un
dictionnaire de paramètres) et les sorties (des rappels de progression et
un dictionnaire de résultats) changent, pour pouvoir être pilotées par
n'importe quelle interface (fenêtre web PyWebView, tests automatiques...).
"""

from __future__ import annotations

import glob
import os
import shutil
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from app.odm_client import ODMClient, ODMProcessingError
from app.raster_processing import (
    compute_vegetation_indices, compute_topography, make_orthophoto_preview,
    compute_surveyed_area_ha, get_center_latlon, zone_palette,
)
from app.report_generator import MissionMetadata, generate_pdf_report
from app.gis_export import export_qgis_package, QgisExportResult
from app.soil_data import soil_data_from_manual, fetch_soilgrids_estimate, suggest_crops

IMAGE_EXTENSIONS = ("*.jpg", "*.jpeg", "*.JPG", "*.JPEG", "*.png", "*.PNG")

# Niveaux de qualité proposés à l'utilisateur. "rapide" garde les valeurs par
# défaut d'ODMClient (medium/medium), adaptées à un PC de 8 Go de RAM.
QUALITY_PRESETS = {
    "rapide": {},
    "equilibre": {"pc-quality": "high", "feature-quality": "high"},
    "precis": {"pc-quality": "ultra", "feature-quality": "ultra"},
}
DEFAULT_QUALITY = "rapide"

# Étapes affichées à l'utilisateur pendant le traitement (indices 0 à 4).
STAGES = (
    "Envoi des photos au moteur",
    "Assemblage de la carte de la parcelle",
    "Analyse de la santé des plantes",
    "Calcul du relief et des pentes",
    "Rédaction du rapport",
)

# Fichiers PNG produits par raster_processing, par clé de carte.
MAP_FILES = {
    "ortho": "orthomosaique_apercu.png",
    "vari": "carte_vari.png",
    "exg": "carte_exg.png",
    "zoning": "carte_zonage.png",
    "hillshade": "mnt_ombrage.png",
    "slope": "carte_pentes.png",
    "low_zones": "carte_zones_basses.png",
}

ProgressCallback = Callable[[int, str, float], None]


def unique_paths(paths):
    """Retire les doublons en conservant l'ordre (insensible à la casse
    sous Windows) : évite de compter deux fois *.jpg et *.JPG."""
    seen = set()
    result = []
    for p in sorted(paths):
        key = os.path.normcase(os.path.abspath(p))
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result


def scan_images(folder: str) -> list[str]:
    found = []
    for ext in IMAGE_EXTENSIONS:
        found.extend(glob.glob(os.path.join(folder, ext)))
    return unique_paths(found)


def write_error_log(exc_text: str, out_dir: Optional[str]) -> str:
    """Enregistre le détail technique d'une erreur ; ne lève jamais."""
    try:
        base = Path(out_dir) if out_dir else Path.home() / "Documents" / "rapports_drone"
        logs_dir = base / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = logs_dir / f"erreur_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_path.write_text(exc_text, encoding="utf-8")
        return str(log_path)
    except Exception:
        return ""


def _copy_if_exists(src, dst):
    try:
        if src is None:
            return
        src = Path(src)
        if src.exists():
            shutil.copy2(src, dst)
    except Exception:
        pass


def health_verdict(pct_severe: float, pct_leger: float) -> tuple[str, str, str]:
    """Phrase de synthèse affichée en tête des résultats.

    Retourne (niveau, titre, détail). Les seuils sont volontairement simples
    et prudents : la phrase invite à vérifier, elle ne prescrit rien.
    Les pourcentages portent sur la surface végétalisée.
    """
    if pct_severe < 10 and pct_leger < 25:
        level, title = "ok", "Votre parcelle est globalement en bonne santé"
    elif pct_severe < 25:
        level, title = "watch", "Votre parcelle montre des signes de stress localisés"
    else:
        level, title = "alert", "Une part importante de la parcelle montre un stress végétal"
    if pct_severe >= 1:
        detail = (f"{pct_severe:.0f} % de la végétation présente un stress marqué : "
                  "une vérification sur place de ces zones est utile.")
    elif pct_leger >= 25:
        detail = (f"Pas de stress marqué, mais {pct_leger:.0f} % de la végétation montre "
                  "un stress léger : ces zones sont à surveiller.")
    else:
        detail = "Aucune zone de stress marqué n'a été détectée sur la végétation."
    return level, title, detail


@dataclass
class MissionParams:
    images_dir: str = ""
    output_dir: str = ""
    nom_parcelle: str = ""
    exploitant: str = ""
    date_vol: str = ""
    altitude_vol: str = ""
    pilote: str = ""
    equipe: str = ""
    n_zones: int = 4
    quality: str = DEFAULT_QUALITY
    soil_ph: str = ""
    soil_texture: str = ""
    soil_note: str = ""
    allow_soilgrids: bool = False
    node_host: str = "localhost"
    node_port: int = 3000

    @classmethod
    def from_dict(cls, d: dict) -> "MissionParams":
        known = {f for f in cls.__dataclass_fields__}
        p = cls(**{k: v for k, v in d.items() if k in known})
        p.n_zones = int(p.n_zones)
        p.node_port = int(p.node_port)
        p.allow_soilgrids = bool(p.allow_soilgrids)
        return p


def validate(params: MissionParams) -> list[tuple[str, str]]:
    """Retourne la liste des erreurs (champ, message) ; vide si tout va bien."""
    errors = []
    if not params.images_dir or not Path(params.images_dir).is_dir():
        errors.append(("images_dir", "Choisissez un dossier de photos valide."))
    elif not scan_images(params.images_dir):
        errors.append(("images_dir", "Aucune photo (.jpg/.png) trouvée dans ce dossier."))
    for name, label in (("nom_parcelle", "le nom de la parcelle"),
                        ("exploitant", "l'exploitant ou la coopérative"),
                        ("date_vol", "la date du vol")):
        if not str(getattr(params, name)).strip():
            errors.append((name, f"Indiquez {label}."))
    alt = params.altitude_vol.strip()
    if alt:
        try:
            float(alt.replace(",", "."))
        except ValueError:
            errors.append(("altitude_vol", "L'altitude doit être un nombre (ex : 90)."))
    if params.soil_ph.strip():
        try:
            v = float(params.soil_ph.replace(",", "."))
            if not 0 < v < 14:
                errors.append(("soil_ph", "Le pH doit être compris entre 0 et 14."))
        except ValueError:
            errors.append(("soil_ph", "Le pH doit être un nombre (ex : 6,5)."))
    if not 2 <= params.n_zones <= 6:
        errors.append(("n_zones", "Le nombre de zones doit être compris entre 2 et 6."))
    if params.quality not in QUALITY_PRESETS:
        errors.append(("quality", "Niveau de qualité inconnu."))
    return errors


def run_mission(params: MissionParams, on_progress: ProgressCallback,
                client_factory=ODMClient) -> dict:
    """Exécute toute la mission. Lève ODMProcessingError ou une autre
    exception en cas d'échec ; retourne un dictionnaire de résultats."""
    out_dir = params.output_dir or str(Path.home() / "Documents" / "rapports_drone")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    image_paths = scan_images(params.images_dir)
    analyses_dir = os.path.join(out_dir, "analyses")

    on_progress(0, f"{len(image_paths)} photos. Connexion au moteur de traitement...", 1)
    client = client_factory(params.node_host, int(params.node_port))
    client.connect()

    def odm_progress(step, pct):
        overall = pct * 0.65
        stage = 0 if pct < 15 else 1
        on_progress(stage, step, overall)

    result = client.process_images(
        image_paths, os.path.join(out_dir, "odm_output"),
        extra_options=QUALITY_PRESETS.get(params.quality, {}),
        progress_callback=odm_progress,
    )
    if result.orthophoto_path is None:
        raise ODMProcessingError(
            "Le traitement s'est terminé mais aucune carte de la parcelle n'a été "
            "produite. Vérifiez que les photos se recouvrent suffisamment (au moins 75 %)."
        )

    on_progress(2, "Calcul des indices de vigueur végétale (VARI/ExG)...", 68)
    veg = compute_vegetation_indices(str(result.orthophoto_path), analyses_dir,
                                     n_zones=int(params.n_zones))
    on_progress(2, "Préparation de l'aperçu de la parcelle...", 76)
    ortho_preview = make_orthophoto_preview(str(result.orthophoto_path), analyses_dir)

    topo = None
    if result.dtm_path is not None:
        on_progress(3, "Analyse du relief, des pentes et du drainage...", 84)
        topo = compute_topography(str(result.dtm_path), analyses_dir)
    else:
        on_progress(3, "Relief non disponible dans les résultats, étape ignorée.", 84)

    on_progress(3, "Organisation des fichiers géoréférencés...", 90)
    livrables = os.path.join(out_dir, "livrables")
    os.makedirs(livrables, exist_ok=True)
    _copy_if_exists(result.orthophoto_path, os.path.join(livrables, "orthomosaique.tif"))
    _copy_if_exists(result.dtm_path, os.path.join(livrables, "mnt.tif"))
    _copy_if_exists(result.dsm_path, os.path.join(livrables, "mns.tif"))
    _copy_if_exists(veg.vari_tif, os.path.join(livrables, "carte_vari.tif"))
    if result.point_cloud_path is not None:
        _copy_if_exists(result.point_cloud_path,
                        os.path.join(livrables, "nuage_points" + Path(result.point_cloud_path).suffix))

    on_progress(3, "Export des couches pour QGIS (zonage, courbes de niveau)...", 90.5)
    try:
        qgis_export = export_qgis_package(
            Path(livrables) / "qgis",
            veg.zone_map, veg.vari_array, veg.zone_transform, veg.zone_crs,
            veg.n_zones, zone_palette(veg.n_zones or int(params.n_zones)),
            str(result.dtm_path) if result.dtm_path else None,
        )
        for trace in qgis_export.errors:
            write_error_log(trace, out_dir)
    except Exception:
        trace = traceback.format_exc()
        write_error_log(trace, out_dir)
        qgis_export = QgisExportResult(folder=Path(livrables) / "qgis", errors=[trace])

    on_progress(3, "Calcul de la surface survolée...", 91)
    try:
        surface_ha = compute_surveyed_area_ha(str(result.orthophoto_path))
    except Exception:
        write_error_log(traceback.format_exc(), out_dir)
        surface_ha = None

    on_progress(4, "Analyse du sol et des cultures possibles...", 91.5)
    soil, crops = None, None
    try:
        ph = float(params.soil_ph.replace(",", ".")) if params.soil_ph.strip() else None
        soil = soil_data_from_manual(ph, params.soil_texture, params.soil_note)
        if soil is None and params.allow_soilgrids:
            latlon = get_center_latlon(str(result.orthophoto_path))
            if latlon:
                soil = fetch_soilgrids_estimate(latlon[0], latlon[1])
        if soil is not None:
            crops = suggest_crops(soil,
                                  topo.mean_slope_pct if topo else None,
                                  topo.pct_low_zones if topo else None)
    except Exception:
        write_error_log(traceback.format_exc(), out_dir)
        soil, crops = None, None

    on_progress(4, "Rédaction du rapport PDF...", 92)
    alt = params.altitude_vol.strip().replace(",", ".")
    meta = MissionMetadata(
        nom_parcelle=params.nom_parcelle or "Parcelle non renseignée",
        exploitant=params.exploitant,
        date_vol=params.date_vol or "-",
        altitude_vol_m=float(alt) if alt else None,
        surface_ha=surface_ha,
        nombre_photos=len(image_paths),
        pilote=params.pilote,
        equipe=params.equipe,
    )
    pdf_path = os.path.join(out_dir, "rapport_mission_drone.pdf")
    generate_pdf_report(
        pdf_path, meta,
        orthophoto_preview=ortho_preview,
        vari_png=veg.vari_png, exg_png=veg.exg_png, zoning_png=veg.zoning_png,
        hillshade_png=topo.hillshade_png if topo else None,
        slope_png=topo.slope_png if topo else None,
        low_zones_png=topo.low_zones_png if topo else None,
        veg_stats={
            "mean_vari": veg.mean_vari,
            "pct_stress_severe": veg.pct_stress_severe,
            "pct_stress_leger": veg.pct_stress_leger,
            "pct_vegetation_saine": veg.pct_vegetation_saine,
            "pct_image_vegetation": veg.pct_image_vegetation,
        },
        topo_stats={
            "min_alt": topo.min_alt, "max_alt": topo.max_alt,
            "mean_slope_pct": topo.mean_slope_pct, "pct_low_zones": topo.pct_low_zones,
        } if topo else None,
        soil=soil, crop_suggestions=crops, qgis_export=qgis_export,
        odm_report_pdf=result.report_pdf_path,
    )
    on_progress(4, "Rapport terminé.", 100)

    return {
        "pdf_path": pdf_path,
        "out_dir": out_dir,
        "nom_parcelle": meta.nom_parcelle,
        "n_photos": len(image_paths),
        "n_zones": int(veg.n_zones or params.n_zones),
        "surface_ha": surface_ha,
        "pct_couverture": veg.pct_image_vegetation,
        "pct_saine": veg.pct_vegetation_saine,
        "pct_leger": veg.pct_stress_leger,
        "pct_severe": veg.pct_stress_severe,
        "pct_low_zones": topo.pct_low_zones if topo else None,
        "mean_slope_pct": topo.mean_slope_pct if topo else None,
        "maps": find_maps(out_dir),
    }


def find_maps(out_dir: str) -> dict[str, str]:
    """Cartes PNG présentes dans <out_dir>/analyses (ou out_dir lui-même)."""
    base = Path(out_dir)
    analyses = base / "analyses" if (base / "analyses").is_dir() else base
    return {k: str(analyses / f) for k, f in MAP_FILES.items() if (analyses / f).exists()}
