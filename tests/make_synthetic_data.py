"""Genere une fausse orthomosaique RGB et un faux MNT (GeoTIFF) pour tester
raster_processing.py et report_generator.py sans avoir besoin de vraies photos
drone ni d'un moteur NodeODM en fonctionnement."""

import numpy as np
import rasterio
from rasterio.transform import from_origin


def make_fake_orthophoto(path, size=800):
    np.random.seed(0)
    yy, xx = np.mgrid[0:size, 0:size]
    # champ avec un gradient de vigueur + zone de stress circulaire
    vigor = 0.5 + 0.3 * np.sin(xx / 60) * np.cos(yy / 60)
    stress_zone = ((xx - size * 0.3) ** 2 + (yy - size * 0.7) ** 2) < (size * 0.12) ** 2
    vigor[stress_zone] -= 0.5
    vigor = np.clip(vigor, 0, 1)

    green = (100 + vigor * 120).astype("uint8")
    red = (90 - vigor * 40 + 60).astype("uint8")
    blue = (60 + (1 - vigor) * 20).astype("uint8")

    # bordure "nodata" noire pour simuler une orthomosaique reelle
    border = 20
    for arr in (red, green, blue):
        arr[:border, :] = 0
        arr[-border:, :] = 0
        arr[:, :border] = 0
        arr[:, -border:] = 0

    transform = from_origin(2.5, 6.4, 0.02, 0.02)  # coin (lon,lat) approx Benin, 2cm/px
    with rasterio.open(
        path, "w", driver="GTiff", height=size, width=size, count=3,
        dtype="uint8", crs="EPSG:4326", transform=transform, nodata=0,
    ) as dst:
        dst.write(red, 1)
        dst.write(green, 2)
        dst.write(blue, 3)


def make_fake_dtm(path, size=600):
    yy, xx = np.mgrid[0:size, 0:size]
    z = 45 + 3 * np.sin(xx / 150) + 2 * np.cos(yy / 100) + 0.002 * xx
    z = z.astype("float32")
    transform = from_origin(2.5, 6.4, 0.03, 0.03)
    with rasterio.open(
        path, "w", driver="GTiff", height=size, width=size, count=1,
        dtype="float32", crs="EPSG:4326", transform=transform, nodata=-9999,
    ) as dst:
        dst.write(z, 1)


if __name__ == "__main__":
    import sys
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    make_fake_orthophoto(f"{out_dir}/fake_orthophoto.tif")
    make_fake_dtm(f"{out_dir}/fake_dtm.tif")
    print("Fichiers synthetiques generes.")
