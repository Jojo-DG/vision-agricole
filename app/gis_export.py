"""
gis_export.py

Exports « prêts pour QGIS » (et pour tout SIG ou logiciel de CAO), produits
directement en Python, sans installer QGIS :

  - zonage_gestion.tif : zonage de gestion en GeoTIFF (couleurs intégrées)
  - zonage_gestion.shp : mêmes zones en polygones (Shapefile), avec surface,
    part de la parcelle et vigueur moyenne (VARI) de chaque zone
  - courbes_niveau.shp / .dxf : courbes de niveau issues du MNT
  - LISEZMOI_QGIS.txt : mode d'emploi

Ces fichiers répondent aux livrables « Carte de zonage (SHP / PDF) » et
« Plan topographique (DXF / PDF) » du cahier des charges.

Choix techniques : bibliothèques Python légères (pyshp, ezdxf, contourpy) plutôt
que geopandas/fiona, lourdes et risquées à embarquer dans un exécutable unique.
Chaque export est indépendant : l'échec de l'un n'empêche pas les autres, et ne
fait jamais échouer le traitement principal.
"""

from __future__ import annotations

import math
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import rasterio
from rasterio import features
from rasterio.enums import Resampling

# La classification du zonage se fait pixel par pixel : sur une image à quelques
# centimètres de résolution, elle est parsemée de fragments d'un ou deux pixels
# (« sel et poivre »). Pour obtenir des zones de gestion exploitables :
#   1. filtre de majorité : chaque pixel prend la zone dominante de son voisinage
#      (rayon SMOOTH_RADIUS_M) ;
#   2. fusion des fragments restants de moins de MIN_ZONE_M2 avec leur voisin.
# On garde la part « brute » de chaque zone (champ PCT_BRUT) et on avertit si le
# lissage la modifie fortement.
SMOOTH_RADIUS_M = 0.3
MIN_ZONE_M2 = 5.0
MAX_SIEVE_PIXELS = 20000
SMOOTH_WARN_POINTS = 3.0     # écart minimal (en points de %) pour avertir
SMOOTH_WARN_RATIO = 0.5      # et variation relative minimale (50 %)

# Échelon des courbes de niveau : on retient le plus petit pas « rond » qui
# donne au plus MAX_CONTOUR_LEVELS courbes (le cahier des charges demande des
# courbes de 10 à 50 cm quand le relief le permet).
CONTOUR_STEPS_M = (0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0)
MAX_CONTOUR_LEVELS = 60
MAJOR_EVERY = 5   # une courbe « maîtresse » tous les 5 échelons
MIN_CONTOUR_POINTS = 6


@dataclass
class QgisExportResult:
    folder: Path
    zoning_tif: Optional[Path] = None
    zoning_shp: Optional[Path] = None
    contours_shp: Optional[Path] = None
    contours_dxf: Optional[Path] = None
    zones: list = field(default_factory=list)        # une entrée par zone
    n_zone_polygons: int = 0
    contour_interval_m: Optional[float] = None
    n_contour_lines: int = 0
    crs_label: str = ""
    warnings: list = field(default_factory=list)     # points à signaler à l'utilisateur
    errors: list = field(default_factory=list)       # traces techniques pour le journal

    @property
    def has_zoning(self) -> bool:
        return self.zoning_shp is not None

    @property
    def has_contours(self) -> bool:
        return self.contours_dxf is not None and self.contours_shp is not None


# ----------------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------------

def _pixel_area_m2(transform, crs, height: int) -> float:
    dx, dy = abs(transform.a), abs(transform.e)
    if crs is not None and crs.is_geographic:
        lat = transform.f + transform.e * (height / 2)
        return (dx * 111_320.0 * math.cos(math.radians(lat))) * (dy * 111_320.0)
    return dx * dy   # CRS projeté en mètres (cas général : UTM issu d'ODM)


def _crs_label(crs) -> str:
    if crs is None:
        return "inconnu"
    try:
        epsg = crs.to_epsg()
    except Exception:
        epsg = None
    return f"EPSG:{epsg}" if epsg else (crs.to_string() or "défini dans le fichier .prj")


def _write_sidecars(shp_path: Path, crs) -> None:
    """Écrit le .prj (projection, dialecte ESRI) et le .cpg (UTF-8) à côté du .shp."""
    if crs is not None:
        try:
            wkt = crs.to_wkt(version="WKT1_ESRI")
        except Exception:
            wkt = crs.to_wkt()
        shp_path.with_suffix(".prj").write_text(wkt, encoding="utf-8")
    shp_path.with_suffix(".cpg").write_text("UTF-8", encoding="ascii")


def _box_sum(a: np.ndarray, r: int) -> np.ndarray:
    """Somme sur une fenêtre de (2r+1)² cases, par image intégrale."""
    p = np.pad(a, r + 1, mode="constant").astype("float64")
    c = p.cumsum(0).cumsum(1)
    k = 2 * r + 1
    h, w = a.shape
    return c[k:k + h, k:k + w] - c[:h, k:k + w] - c[k:k + h, :w] + c[:h, :w]


def _majority_filter(zone_u8: np.ndarray, valid: np.ndarray, n_zones: int, r: int) -> np.ndarray:
    best = np.full(zone_u8.shape, -1.0)
    out = np.zeros(zone_u8.shape, dtype="uint8")
    for zone in range(n_zones):
        votes = _box_sum(((zone_u8 == zone) & valid).astype("float32"), r)
        better = votes > best
        out[better] = zone
        best[better] = votes[better]
    return np.where(valid, out, 255).astype("uint8")


def _zone_label(index: int, n_zones: int) -> str:
    if index == 0:
        return "Zone 0 - stress fort"
    if index == n_zones - 1:
        return f"Zone {index} - végétation saine"
    return f"Zone {index} - intermédiaire"


# ----------------------------------------------------------------------------
# Zonage : GeoTIFF + polygones Shapefile
# ----------------------------------------------------------------------------

def export_zoning(zone_map: np.ndarray, vari: Optional[np.ndarray], transform, crs,
                  out_dir: Path, n_zones: int, palette: list, result: QgisExportResult) -> None:
    import shapefile  # pyshp

    valid = np.isfinite(zone_map)
    if not valid.any():
        result.warnings.append("Zonage non exporté : aucune zone de végétation exploitable.")
        return

    zone_u8 = np.where(valid, zone_map, 255).astype("uint8")
    height, width = zone_u8.shape
    pix_m2 = _pixel_area_m2(transform, crs, height)

    raw_counts = np.bincount(zone_u8[valid], minlength=n_zones).astype(float)
    raw_pct = 100.0 * raw_counts / raw_counts.sum()

    # Nettoyage : majorité locale, puis fusion des fragments de moins de MIN_ZONE_M2.
    # (la fusion se fait sans masque : avec masque, GDAL ne fusionne plus rien.)
    pix_side = math.sqrt(pix_m2) if pix_m2 > 0 else 0.1
    radius_px = int(min(8, max(1, round(SMOOTH_RADIUS_M / pix_side))))
    smoothed = _majority_filter(zone_u8, valid, n_zones, radius_px)
    size_px = int(min(MAX_SIEVE_PIXELS, max(25, round(MIN_ZONE_M2 / pix_m2)))) if pix_m2 > 0 else 25
    merged = features.sieve(smoothed, size=size_px, connectivity=4)
    sieved = np.where(valid, np.where(merged == 255, smoothed, merged), 255).astype("uint8")

    # --- GeoTIFF avec table de couleurs (QGIS l'affiche directement colorié) ---
    tif_path = out_dir / "zonage_gestion.tif"
    colormap = {255: (0, 0, 0, 0)}
    for i, hex_color in enumerate(palette[:n_zones]):
        colormap[i] = (int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16), 255)
    with rasterio.open(
        tif_path, "w", driver="GTiff", height=height, width=width, count=1, dtype="uint8",
        crs=crs, transform=transform, nodata=255, compress="deflate",
    ) as dst:
        dst.write(sieved, 1)
        dst.write_colormap(1, colormap)
        dst.set_band_description(1, "Zone de gestion (0 = stress fort)")
    result.zoning_tif = tif_path

    # --- Polygones : une entité (multi-polygone) par zone ---
    polys_by_zone: dict = {}
    for geom, value in features.shapes(sieved, mask=valid.astype("uint8"),
                                       transform=transform, connectivity=4):
        polys_by_zone.setdefault(int(value), []).append(geom["coordinates"])

    shp_path = out_dir / "zonage_gestion.shp"
    total_valid = int(np.count_nonzero(sieved != 255))
    writer = shapefile.Writer(str(shp_path), shapeType=shapefile.POLYGON, encoding="utf-8")
    writer.field("ZONE", "N", 3, 0)
    writer.field("LIBELLE", "C", 40)
    writer.field("SURF_HA", "N", 12, 3)
    writer.field("PCT_SURF", "N", 6, 1)
    writer.field("PCT_BRUT", "N", 6, 1)
    writer.field("VARI_MOY", "N", 8, 3)
    n_polygons = 0
    for zone in sorted(polys_by_zone):
        count = int(np.count_nonzero(sieved == zone))
        surf_ha = count * pix_m2 / 10_000.0
        pct = 100.0 * count / total_valid if total_valid else 0.0
        vari_mean = None
        if vari is not None and vari.shape == sieved.shape:
            sel = vari[(sieved == zone) & np.isfinite(vari)]
            vari_mean = float(np.mean(sel)) if sel.size else None
        writer.shape({"type": "MultiPolygon", "coordinates": polys_by_zone[zone]})
        writer.record(zone, _zone_label(zone, n_zones), round(surf_ha, 3), round(pct, 1),
                      round(float(raw_pct[zone]), 1),
                      round(vari_mean, 3) if vari_mean is not None else None)
        n_polygons += len(polys_by_zone[zone])
        result.zones.append({
            "zone": zone, "libelle": _zone_label(zone, n_zones),
            "surf_ha": surf_ha, "pct": pct, "pct_brut": float(raw_pct[zone]), "vari_moy": vari_mean,
        })
        if abs(pct - raw_pct[zone]) >= SMOOTH_WARN_POINTS and \
                abs(pct - raw_pct[zone]) >= SMOOTH_WARN_RATIO * max(raw_pct[zone], 1e-9):
            result.warnings.append(
                f"Zone {zone} : {raw_pct[zone]:.1f} % de la végétation avant lissage, "
                f"{pct:.1f} % après. Le lissage a fortement modifié cette zone (image très "
                "bruitée ou zone très éparpillée) : vérifiez-la visuellement.")
    writer.close()
    _write_sidecars(shp_path, crs)
    for zone in range(n_zones):
        if zone not in polys_by_zone and raw_counts[zone] > 0:
            result.warnings.append(
                f"Zone {zone} : présente avant lissage ({raw_pct[zone]:.1f} %), "
                "absente après : elle n'apparaît donc pas dans le fichier de zonage.")
    result.zoning_shp = shp_path
    result.n_zone_polygons = n_polygons


# ----------------------------------------------------------------------------
# Courbes de niveau : Shapefile + DXF
# ----------------------------------------------------------------------------

def _nan_box_smooth(z: np.ndarray) -> np.ndarray:
    """Lissage 3x3 qui ignore les cases sans donnée (adoucit l'effet d'escalier)."""
    valid = np.isfinite(z)
    zf = np.where(valid, z, 0.0)
    cf = valid.astype(float)
    pz, pc = np.pad(zf, 1), np.pad(cf, 1)
    h, w = z.shape
    s = np.zeros_like(zf)
    c = np.zeros_like(zf)
    for dy in range(3):
        for dx in range(3):
            s += pz[dy:dy + h, dx:dx + w]
            c += pc[dy:dy + h, dx:dx + w]
    out = np.where(c > 0, s / np.maximum(c, 1), np.nan)
    out[~valid] = np.nan
    return out


def _choose_interval(z_min: float, z_max: float) -> float:
    span = max(z_max - z_min, 0.0)
    for step in CONTOUR_STEPS_M:
        if span / step <= MAX_CONTOUR_LEVELS:
            return step
    return CONTOUR_STEPS_M[-1]


def export_contours(dtm_path: str, out_dir: Path, result: QgisExportResult, max_size: int = 1500) -> None:
    import contourpy
    import ezdxf
    import shapefile  # pyshp

    with rasterio.open(dtm_path) as src:
        scale = min(1.0, max_size / max(src.width, src.height))
        out_w = max(2, int(src.width * scale))
        out_h = max(2, int(src.height * scale))
        z = src.read(1, out_shape=(out_h, out_w), resampling=Resampling.average).astype("float64")
        nodata = src.nodata
        crs = src.crs
        # transform ajusté à la résolution réduite
        transform = src.transform * src.transform.scale(src.width / out_w, src.height / out_h)

    bad = ~np.isfinite(z) | (z < -500)
    if nodata is not None:
        bad |= np.isclose(z, nodata)
    z[bad] = np.nan
    if np.count_nonzero(np.isfinite(z)) < 100:
        result.warnings.append("Courbes de niveau non exportées : MNT sans données exploitables.")
        return
    z = _nan_box_smooth(z)

    z_min, z_max = float(np.nanmin(z)), float(np.nanmax(z))
    interval = _choose_interval(z_min, z_max)
    first = math.floor(z_min / interval) * interval + interval
    levels = [round(v, 3) for v in np.arange(first, z_max, interval)]
    if not levels:
        result.warnings.append("Courbes de niveau non exportées : relief trop plat pour tracer des courbes.")
        return

    # Coordonnées des centres de pixels ; y croissant exigé par contourpy
    xs = transform.c + (np.arange(out_w) + 0.5) * transform.a
    ys = transform.f + (np.arange(out_h) + 0.5) * transform.e
    z_up = np.ma.masked_invalid(z[::-1])
    gen = contourpy.contour_generator(xs, ys[::-1], z_up, line_type=contourpy.LineType.Separate)

    lines_by_level = []
    for level in levels:
        kept = [np.asarray(line) for line in gen.lines(level) if len(line) >= MIN_CONTOUR_POINTS]
        if kept:
            lines_by_level.append((level, kept))
    n_lines = sum(len(k) for _, k in lines_by_level)
    if n_lines == 0:
        result.warnings.append("Courbes de niveau non exportées : aucune courbe significative.")
        return

    major_step = interval * MAJOR_EVERY

    def is_major(level: float) -> bool:
        return abs(level / major_step - round(level / major_step)) < 1e-6

    # --- Shapefile ---
    shp_path = out_dir / "courbes_niveau.shp"
    writer = shapefile.Writer(str(shp_path), shapeType=shapefile.POLYLINE, encoding="utf-8")
    writer.field("ALTITUDE", "N", 9, 2)
    writer.field("MAITRESSE", "N", 1, 0)
    for level, lines in lines_by_level:
        for line in lines:
            writer.line([line.tolist()])
            writer.record(level, 1 if is_major(level) else 0)
    writer.close()
    _write_sidecars(shp_path, crs)

    # --- DXF (CAO) : une couche pour les courbes, une pour les maîtresses ---
    dxf_path = out_dir / "courbes_niveau.dxf"
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.M
    doc.layers.add("COURBES", color=8)
    doc.layers.add("COURBES_MAITRESSES", color=1)
    msp = doc.modelspace()
    for level, lines in lines_by_level:
        layer = "COURBES_MAITRESSES" if is_major(level) else "COURBES"
        for line in lines:
            msp.add_lwpolyline(line.tolist(), format="xy",
                               dxfattribs={"layer": layer, "elevation": float(level)})
    doc.saveas(dxf_path)

    result.contours_shp = shp_path
    result.contours_dxf = dxf_path
    result.contour_interval_m = interval
    result.n_contour_lines = n_lines
    if crs is not None and crs.is_geographic:
        result.warnings.append(
            "Le MNT est en coordonnées géographiques (degrés) : le DXF est donc en degrés, "
            "pas en mètres. Les altitudes, elles, sont bien en mètres.")


# ----------------------------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------------------------

def _write_readme(result: QgisExportResult) -> None:
    lines = [
        "COUCHES PRÊTES POUR QGIS - Vision Agricole",
        "=" * 46,
        "",
        f"Système de coordonnées : {result.crs_label}",
        "(toutes les couches ci-dessous partagent ce système ; QGIS les superpose",
        "correctement sans réglage. Les fichiers .prj le décrivent.)",
        "",
        "Fichiers de ce dossier :",
    ]
    if result.zoning_tif:
        lines.append("  - zonage_gestion.tif : zonage en GeoTIFF, couleurs déjà intégrées.")
    if result.zoning_shp:
        lines.append("  - zonage_gestion.shp : zones de gestion en polygones (une entité par zone).")
        lines.append("      Champs : ZONE, LIBELLE, SURF_HA (hectares), PCT_SURF (%), PCT_BRUT (%), VARI_MOY.")
        lines.append(f"      Zonage lissé : filtre de majorité (rayon ~{SMOOTH_RADIUS_M:g} m) puis fusion des")
        lines.append(f"      fragments de moins de {MIN_ZONE_M2:g} m² avec leur voisin. Il est donc plus net que")
        lines.append("      l'image du rapport PDF. PCT_BRUT donne la part de chaque zone avant lissage,")
        lines.append("      PCT_SURF après lissage (même base : surface de végétation détectée).")
    if result.contours_shp:
        lines.append("  - courbes_niveau.shp : courbes de niveau (champs ALTITUDE et MAITRESSE).")
    if result.contours_dxf:
        lines.append("  - courbes_niveau.dxf : mêmes courbes pour AutoCAD, LibreCAD, etc.")
        lines.append(f"      Échelon : {result.contour_interval_m:g} m ; une courbe maîtresse tous les {MAJOR_EVERY} échelons.")
    lines += [
        "",
        "Dans QGIS :",
        "  1. Couche > Ajouter une couche > ... ou glissez les fichiers dans la fenêtre.",
        "  2. Le dossier parent contient aussi orthomosaique.tif, mnt.tif et carte_vari.tif,",
        "     à glisser dans le même projet.",
        "  3. Pour colorier zonage_gestion.shp : double-clic sur la couche > Symbologie >",
        "     « Catégorisé » > Valeur : ZONE > Classer > OK.",
        "",
        "Remarques :",
        "  - Ces couches sont calculées sur une image réduite (au plus 2000 px de côté pour",
        "    le zonage, 1500 px pour le MNT) : elles servent à décider, pas à borner un titre foncier.",
        "  - Le zonage est une classification automatique de la vigueur (VARI, RVB) ;",
        "    il n'a pas été validé sur le terrain.",
    ]
    if result.warnings:
        lines += ["", "Points à noter :"] + [f"  - {w}" for w in result.warnings]
    (result.folder / "LISEZMOI_QGIS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def export_qgis_package(
    out_dir: Path,
    zone_map: Optional[np.ndarray],
    vari: Optional[np.ndarray],
    zone_transform,
    zone_crs,
    n_zones: int,
    palette: list,
    dtm_path: Optional[str],
) -> QgisExportResult:
    """Produit tous les exports QGIS dans `out_dir`. Ne lève jamais d'exception :
    les erreurs sont rangées dans `result.errors` (traces) pour le journal."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = QgisExportResult(folder=out_dir)
    result.crs_label = _crs_label(zone_crs)

    if zone_map is not None and zone_transform is not None:
        try:
            export_zoning(zone_map, vari, zone_transform, zone_crs, out_dir, n_zones, palette, result)
        except Exception:
            result.errors.append("Export du zonage échoué :\n" + traceback.format_exc())
    else:
        result.warnings.append("Zonage non exporté : pas assez de végétation détectée pour un zonage.")

    if dtm_path:
        try:
            with rasterio.open(dtm_path) as src:
                dtm_crs = src.crs
            if not result.crs_label or result.crs_label == "inconnu":
                result.crs_label = _crs_label(dtm_crs)
            export_contours(str(dtm_path), out_dir, result)
        except Exception:
            result.errors.append("Export des courbes de niveau échoué :\n" + traceback.format_exc())
    else:
        result.warnings.append("Courbes de niveau non exportées : aucun MNT produit par le moteur.")

    try:
        _write_readme(result)
    except Exception:
        result.errors.append("Écriture du LISEZMOI échouée :\n" + traceback.format_exc())
    return result
