"""
raster_processing.py

Calcule les livrables agricoles a partir de l'orthomosaïque RGB et du MNT
produits par le moteur photogrammetrique, en suivant le cahier des charges :

- Le M3E ne possède pas de capteur multispectral -> pas de vrai NDVI possible.
- On utilise donc VARI et ExG (indices calculables en RGB visible) comme
  indicateurs approximatifs de vigueur végétale (section 3.2 du cahier).
- Un zonage de gestion différenciée (3 a 4 classes) est dérive de la carte VARI
  par classification k-means, pour guider la modulation des intrants.
- Le MNT est transformé en carte de pentes + ombrage (hillshade) pour
  l'analyse de drainage/topographie (section 4.5, livrable "Courbes niveau").

Toutes les fonctions retournent des chemins de fichiers PNG (aperçus visuels
destinés au rapport PDF) ainsi que quelques statistiques résumées.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import rasterio
from rasterio.enums import Resampling
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


# ----------------------------------------------------------------------------
# Indices de végétation RGB (pas de proche infrarouge disponible sur le M3E)
# ----------------------------------------------------------------------------

def zone_palette(n_zones: int) -> list:
    """Palette rouge (stress fort) -> vert foncé (végétation saine) pour n zones.
    Pour 4 zones, ce sont exactement les 4 couleurs d'origine ; pour 2, 3, 5 ou 6
    zones (l'interface en propose de 2 à 6), on interpole entre ces repères."""
    anchors = [(168, 50, 50), (217, 140, 52), (159, 217, 52), (47, 143, 47)]
    if n_zones <= 1:
        return ["#%02x%02x%02x" % anchors[0]]
    colors = []
    for i in range(n_zones):
        pos = i / (n_zones - 1) * (len(anchors) - 1)
        lo = int(np.floor(pos))
        hi = min(lo + 1, len(anchors) - 1)
        frac = pos - lo
        rgb = tuple(int(round(anchors[lo][k] * (1 - frac) + anchors[hi][k] * frac)) for k in range(3))
        colors.append("#%02x%02x%02x" % rgb)
    return colors


@dataclass
class VegetationIndexResult:
    vari_png: Path
    exg_png: Path
    zoning_png: Path
    vari_tif: Path  # export GeoTIFF geo-référence (livrable du cahier des charges)
    mean_vari: float
    pct_stress_severe: float   # VARI très faible -> stress sévère
    pct_stress_leger: float
    pct_vegetation_saine: float
    zone_class_count: dict
    pct_image_vegetation: float  # % de l'image classée comme végétation (hors sol nu/batiments/eau)
    # Données transportées pour l'export QGIS (zonage en SHP / GeoTIFF)
    zone_map: Optional[np.ndarray] = None   # classes 0..n-1, NaN hors végétation
    zone_transform: object = None           # géoréférence de zone_map
    zone_crs: object = None
    vari_array: Optional[np.ndarray] = None
    n_zones: int = 0


def _read_rgb(orthophoto_path: str, max_size: int = 2000) -> tuple[np.ndarray, dict, np.ndarray]:
    """Lit les 3 premières bandes (R,V,B) de l'orthomosaïque, sous-échantillonnée
    pour rester rapide (les orthomosaïques drone peuvent faire plusieurs Go)."""
    with rasterio.open(orthophoto_path) as src:
        scale = min(1.0, max_size / max(src.width, src.height))
        out_w = max(1, int(src.width * scale))
        out_h = max(1, int(src.height * scale))
        data = src.read(
            out_shape=(min(src.count, 4), out_h, out_w),
            resampling=Resampling.average,
        )
        # transform ajuste a la résolution réduite, sinon la géoréférence du
        # GeoTIFF exporté (carte_vari.tif) serait fausse
        scaled_transform = src.transform * src.transform.scale(
            src.width / out_w, src.height / out_h
        )
        meta = {
            "transform": scaled_transform,
            "crs": src.crs,
            "nodata": src.nodata,
            "width": out_w,
            "height": out_h,
        }

    data = data.astype("float32")
    if data.shape[0] >= 3:
        r, g, b = data[0], data[1], data[2]
    else:
        raise ValueError("L'orthomosaïque doit contenir au moins 3 bandes (RVB).")

    # masque des pixels "nodata" / noirs (bordures de l'orthomosaïque)
    mask = (r + g + b) <= 1e-6
    return np.stack([r, g, b]), meta, mask


def _otsu_threshold(values: np.ndarray, nbins: int = 256) -> float:
    """Seuillage d'Otsu (implémentation numpy simple, sans dépendance
    supplémentaire) : séparé automatiquement une distribution bimodale en
    deux groupes en maximisant la variance inter-classe. Utilise ici pour
    distinguer la végétation (ExG élevé) du sol nu / batiments / eau
    (ExG faible ou négatif)."""
    hist, bin_edges = np.histogram(values, bins=nbins)
    bin_mids = (bin_edges[:-1] + bin_edges[1:]) / 2.0
    weight1 = np.cumsum(hist).astype("float64")
    weight2 = np.cumsum(hist[::-1])[::-1].astype("float64")

    # évite les divisions par zéro sur les classes vides en bord d'histogramme
    with np.errstate(divide="ignore", invalid="ignore"):
        mean1 = np.cumsum(hist * bin_mids) / weight1
        mean2 = (np.cumsum((hist * bin_mids)[::-1])[::-1]) / weight2

    inter_class_variance = weight1[:-1] * weight2[1:] * (mean1[:-1] - mean2[1:]) ** 2
    inter_class_variance = np.nan_to_num(inter_class_variance, nan=-1.0)
    idx = int(np.argmax(inter_class_variance))
    return float(bin_mids[idx])


def _vegetation_mask(exg_raw: np.ndarray, nodata_mask: np.ndarray) -> np.ndarray:
    """Détermine quels pixels correspondent a de la végétation, pour exclure
    sol nu, eau, routes et toits de batiments des cartes de vigueur et du
    zonage (sans cette exclusion, certains toits/matériaux prennent par
    hasard une teinte proche du vert et sont classes a tort comme
    'végétation saine')."""
    valid_values = exg_raw[~nodata_mask]
    if valid_values.size < 100:
        # pas assez de données pour un seuillage fiable : on ne masque rien
        return ~nodata_mask
    threshold = _otsu_threshold(valid_values)
    return (exg_raw > threshold) & (~nodata_mask)



def compute_vegetation_indices(
    orthophoto_path: str,
    output_dir: str,
    n_zones: int = 4,
) -> VegetationIndexResult:
    from sklearn.cluster import KMeans

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (r, g, b), meta, nodata_mask = _read_rgb(orthophoto_path)

    eps = 1e-6
    vari = (g - r) / (g + r - b + eps)
    exg = 2 * g - r - b

    # exclut sol nu / batiments / eau des cartes de vigueur et du zonage
    veg_mask = _vegetation_mask(exg, nodata_mask)
    exclude_mask = nodata_mask | (~veg_mask)
    pct_image_vegetation = float(100 * np.mean(veg_mask))

    vari_clipped = np.clip(vari, -1, 1)
    vari_clipped[exclude_mask] = np.nan

    # --- export GeoTIFF geo-référence (livrable explicite du cahier des charges,
    # section 4.5 : "Carte VARI / ExG - GeoTIFF") ---
    vari_tif = out_dir / "carte_vari.tif"
    vari_for_export = np.where(np.isnan(vari_clipped), -9999.0, vari_clipped).astype("float32")
    with rasterio.open(
        vari_tif, "w", driver="GTiff",
        height=meta["height"], width=meta["width"], count=1,
        dtype="float32", crs=meta["crs"], transform=meta["transform"],
        nodata=-9999.0,
    ) as dst:
        dst.write(vari_for_export, 1)

    exg_norm = (exg - np.nanmin(exg)) / (np.nanmax(exg) - np.nanmin(exg) + eps)
    exg_norm[exclude_mask] = np.nan

    # --- carte VARI ---
    vari_png = out_dir / "carte_vari.png"
    fig, ax = plt.subplots(figsize=(8, 8))
    cmap_vari = plt.get_cmap("RdYlGn").copy()
    cmap_vari.set_bad(color="#d9d9d9")  # gris = hors végétation (sol, bâti, eau)
    im = ax.imshow(vari_clipped, cmap=cmap_vari, vmin=-0.3, vmax=0.5)
    ax.set_title("Carte de vigueur végétale (VARI - approximation RGB)")
    ax.axis("off")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("VARI (faible -> stress, élevé -> végétation saine)")
    fig.tight_layout()
    fig.savefig(vari_png, dpi=150)
    plt.close(fig)

    # --- carte ExG ---
    exg_png = out_dir / "carte_exg.png"
    fig, ax = plt.subplots(figsize=(8, 8))
    cmap_exg = plt.get_cmap("YlGn").copy()
    cmap_exg.set_bad(color="#d9d9d9")
    im = ax.imshow(exg_norm, cmap=cmap_exg)
    ax.set_title("Carte de vigueur végétale (ExG - Excess Green)")
    ax.axis("off")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(exg_png, dpi=150)
    plt.close(fig)

    # --- zonage de gestion différenciée (k-means sur VARI) ---
    valid = ~np.isnan(vari_clipped)
    values = vari_clipped[valid].reshape(-1, 1)
    zoning_png = out_dir / "carte_zonage.png"
    zone_class_count: dict = {}
    zone_map_export = None

    if values.size > 100:
        km = KMeans(n_clusters=n_zones, n_init=4, random_state=42)
        labels = km.fit_predict(values)

        # ordonne les classes de la moins vigoureuse a la plus vigoureuse
        order = np.argsort(km.cluster_centers_.flatten())
        remap = {old: new for new, old in enumerate(order)}
        labels_remapped = np.vectorize(remap.get)(labels)

        zone_map = np.full(vari_clipped.shape, np.nan)
        zone_map[valid] = labels_remapped
        zone_map_export = zone_map

        colors = zone_palette(n_zones)
        cmap = ListedColormap(colors)
        cmap.set_bad(color="#d9d9d9")

        fig, ax = plt.subplots(figsize=(8, 8))
        im = ax.imshow(zone_map, cmap=cmap, vmin=-0.5, vmax=n_zones - 0.5)
        ax.set_title(f"Zonage de gestion différenciée ({n_zones} classes)")
        ax.axis("off")
        cbar = fig.colorbar(im, ax=ax, ticks=range(n_zones), fraction=0.046, pad=0.04)
        cbar.set_label("Classe (0 = stress fort -> {} = végétation saine)".format(n_zones - 1))
        fig.tight_layout()
        fig.savefig(zoning_png, dpi=150)
        plt.close(fig)

        unique, counts = np.unique(labels_remapped, return_counts=True)
        total = counts.sum()
        for u, c in zip(unique, counts):
            zone_class_count[int(u)] = round(100 * c / total, 1)
    else:
        # pas assez de pixels valides : on génère une image vide informative
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(0.5, 0.5, "Données insuffisantes pour le zonage", ha="center", va="center")
        ax.axis("off")
        fig.savefig(zoning_png, dpi=150)
        plt.close(fig)

    vari_values = vari_clipped[valid]
    if vari_values.size > 0:
        mean_vari = float(np.mean(vari_values))
        pct_severe = float(100 * np.mean(vari_values < 0.0))
        pct_leger = float(100 * np.mean((vari_values >= 0.0) & (vari_values < 0.15)))
        pct_sain = float(100 * np.mean(vari_values >= 0.15))
    else:
        mean_vari, pct_severe, pct_leger, pct_sain = float("nan"), 0.0, 0.0, 0.0

    return VegetationIndexResult(
        vari_png=vari_png,
        exg_png=exg_png,
        zoning_png=zoning_png,
        vari_tif=vari_tif,
        mean_vari=mean_vari,
        pct_stress_severe=pct_severe,
        pct_stress_leger=pct_leger,
        pct_vegetation_saine=pct_sain,
        zone_class_count=zone_class_count,
        pct_image_vegetation=pct_image_vegetation,
        zone_map=zone_map_export,
        zone_transform=meta["transform"],
        zone_crs=meta["crs"],
        vari_array=vari_clipped,
        n_zones=n_zones,
    )


# ----------------------------------------------------------------------------
# Topographie (MNT -> pentes + ombrage)
# ----------------------------------------------------------------------------

@dataclass
class TopographyResult:
    hillshade_png: Path
    slope_png: Path
    low_zones_png: Path
    min_alt: float
    max_alt: float
    mean_slope_pct: float
    pct_low_zones: float


def compute_topography(dtm_path: str, output_dir: str) -> TopographyResult:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with rasterio.open(dtm_path) as src:
        scale = min(1.0, 1500 / max(src.width, src.height))
        out_w = max(1, int(src.width * scale))
        out_h = max(1, int(src.height * scale))
        z = src.read(1, out_shape=(out_h, out_w), resampling=Resampling.average).astype("float32")
        nodata = src.nodata
        px_size_x = src.transform.a * (src.width / out_w)
        px_size_y = -src.transform.e * (src.height / out_h)

    if nodata is not None:
        z = np.where(z == nodata, np.nan, z)

    # pentes via gradient
    dzdx, dzdy = np.gradient(z, px_size_x, px_size_y)
    slope_pct = np.sqrt(dzdx ** 2 + dzdy ** 2) * 100

    # ombrage (hillshade) simplifié, azimut 315 deg, altitude 45 deg
    az = np.radians(315)
    alt = np.radians(45)
    slope_rad = np.arctan(np.sqrt(dzdx ** 2 + dzdy ** 2))
    aspect = np.arctan2(-dzdx, dzdy)
    hillshade = (np.sin(alt) * np.cos(slope_rad) +
                 np.cos(alt) * np.sin(slope_rad) * np.cos(az - aspect))
    hillshade = np.clip(hillshade, 0, 1)

    hillshade_png = out_dir / "mnt_ombrage.png"
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(hillshade, cmap="gray")
    ax.set_title("Modèle Numérique de Terrain (relief ombre)")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(hillshade_png, dpi=150)
    plt.close(fig)

    slope_png = out_dir / "carte_pentes.png"
    fig, ax = plt.subplots(figsize=(8, 8))
    im = ax.imshow(slope_pct, cmap="YlOrRd", vmax=np.nanpercentile(slope_pct, 95))
    ax.set_title("Carte des pentes (%) - drainage")
    ax.axis("off")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Pente (%)")
    fig.tight_layout()
    fig.savefig(slope_png, dpi=150)
    plt.close(fig)

    # --- carte des zones basses (livrable explicite du cahier des charges,
    # section 3.2 "Application 2 : Topographie et Drainage") : identifié le
    # 20% des altitudes les plus basses, sujettes a l'accumulation d'eau ---
    low_threshold = float(np.nanpercentile(z, 20))
    low_zone_mask = z <= low_threshold
    pct_low_zones = float(100 * np.nanmean(low_zone_mask))

    low_zones_png = out_dir / "carte_zones_basses.png"
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(hillshade, cmap="gray")
    overlay = np.where(low_zone_mask, 1.0, np.nan)
    ax.imshow(overlay, cmap=ListedColormap(["#1E6FD9"]), alpha=0.55)
    ax.set_title("Zones basses (risque d'accumulation d'eau)")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(low_zones_png, dpi=150)
    plt.close(fig)

    return TopographyResult(
        hillshade_png=hillshade_png,
        slope_png=slope_png,
        low_zones_png=low_zones_png,
        min_alt=float(np.nanmin(z)),
        max_alt=float(np.nanmax(z)),
        mean_slope_pct=float(np.nanmean(slope_pct)),
        pct_low_zones=pct_low_zones,
    )


def get_center_latlon(orthophoto_path: str) -> Optional[tuple]:
    """Retourne (latitude, longitude) du centre de l'orthomosaïque, en
    reprojetant depuis le CRS du fichier vers EPSG:4326 si nécessaire.
    Utilise pour interroger une source externe (SoilGrids) par
    géolocalisation. Retourne None en cas d'échec plutôt que de lever une
    exception : cette donnée est secondaire, elle ne doit jamais faire
    échouer le traitement principal."""
    try:
        from rasterio.warp import transform as warp_transform

        with rasterio.open(orthophoto_path) as src:
            cx, cy = src.transform * (src.width / 2, src.height / 2)
            if src.crs is None:
                return None
            if src.crs.to_epsg() == 4326:
                return float(cy), float(cx)
            lon, lat = warp_transform(src.crs, "EPSG:4326", [cx], [cy])
            return float(lat[0]), float(lon[0])
    except Exception:
        return None


def compute_surveyed_area_ha(orthophoto_path: str) -> Optional[float]:
    """Calcule la surface réellement couverte par l'orthomosaïque (en excluant
    les bordures nodata), en hectares. Répond au cahier des charges, section
    3.2 'Application 4' : calcul précis des surfaces (ex. déclaration PAC).

    Ne capture plus ses propres exceptions : en cas d'échec, l'appelant
    (gui.py) doit journaliser l'erreur réelle avant de retomber sur None,
    plutôt que de la faire disparaître silencieusement."""
    import math

    with rasterio.open(orthophoto_path) as src:
        scale = min(1.0, 1500 / max(src.width, src.height))
        out_w = max(1, int(src.width * scale))
        out_h = max(1, int(src.height * scale))
        data = src.read(
            out_shape=(min(src.count, 3), out_h, out_w),
            resampling=Resampling.average,
        )
        crs = src.crs
        px_w = src.transform.a * (src.width / out_w)
        px_h = -src.transform.e * (src.height / out_h)
        # centre approximatif de l'emprise, pour la conversion degrés -> mètres
        center_lon, center_lat = src.transform * (src.width / 2, src.height / 2)

    valid_pixel_count = int(np.sum((data[0] + data[1] + data[2]) > 1e-6)) if data.shape[0] >= 3 else int(data[0].size)

    if crs is not None and crs.is_geographic:
        # transform en degrés : conversion approximative en mètres
        meters_per_deg_lat = 111_320.0
        meters_per_deg_lon = 111_320.0 * math.cos(math.radians(center_lat))
        pixel_area_m2 = (px_w * meters_per_deg_lon) * (px_h * meters_per_deg_lat)
    else:
        # CRS projeté (ex. UTM) : unités déjà en mètres dans la grande majorité des cas
        pixel_area_m2 = px_w * px_h

    area_ha = (valid_pixel_count * pixel_area_m2) / 10_000.0
    return round(float(area_ha), 2)



def make_orthophoto_preview(orthophoto_path: str, output_dir: str) -> Path:
    """Genere un simple aperçu JPEG/PNG de l'orthomosaïque pour le rapport."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (r, g, b), meta, nodata_mask = _read_rgb(orthophoto_path)

    rgb = np.stack([r, g, b], axis=-1)
    p2, p98 = np.nanpercentile(rgb[~nodata_mask], (2, 98)) if (~nodata_mask).any() else (0, 255)
    rgb_stretched = np.clip((rgb - p2) / (p98 - p2 + 1e-6), 0, 1)

    preview_png = out_dir / "orthomosaique_apercu.png"
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(rgb_stretched)
    ax.set_title("Orthomosaïque")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(preview_png, dpi=150)
    plt.close(fig)
    return preview_png
