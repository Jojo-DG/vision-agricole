"""
soil_data.py

Caractéristiques du sol, pour orienter une liste de cultures possibles par
zone. Le drone (photos RGB) ne mesure PAS le sol lui-même : ce module
récupère cette donnée par deux voies distinctes, dans cet ordre de priorité :

  1. Saisie manuelle par l'utilisateur (la plus fiable si elle est
     disponible : un vrai résultat d'analyse de sol, même partiel).
  2. A défaut, une estimation par géolocalisation via l'API publique
     SoilGrids (ISRIC) : une estimation régionale a environ 250m de
     résolution, PAS une mesure de la parcelle elle-même. Nécessite une
     connexion internet ; échoue silencieusement (retourne None) si hors
     ligne ou en cas d'erreur, sans jamais bloquer le traitement (cohérent
     avec le fonctionnement hors-ligne de l'application le reste du temps).

Aucune des deux sources ne remplace une vraie analyse de sol en laboratoire.
La suggestion de cultures qui en découle (voir suggest_crops) reste une
orientation indicative fondée sur des règles simples de tolérance, jamais
une prescription agronomique.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SoilData:
    ph: Optional[float] = None
    texture: Optional[str] = None       # ex: "Argileux", "Limoneux", "Sableux"
    azote_note: Optional[str] = None    # note qualitative libre (saisie manuelle uniquement)
    source: str = ""                    # "Saisie manuelle" ou "Estimation SoilGrids (ISRIC)"
    source_detail: str = ""             # précision affichée dans le rapport


def soil_data_from_manual(ph: Optional[float], texture: str, azote_note: str) -> Optional[SoilData]:
    """Construit un SoilData a partir des champs saisis dans l'interface.
    Retourne None si rien n'a été renseigne (permet le repli SoilGrids)."""
    texture = (texture or "").strip()
    azote_note = (azote_note or "").strip()
    if ph is None and not texture and not azote_note:
        return None
    return SoilData(
        ph=ph,
        texture=texture or None,
        azote_note=azote_note or None,
        source="Saisie manuelle",
        source_detail="Donnée renseignée par l'utilisateur (ex : analyse de sol de terrain).",
    )


def fetch_soilgrids_estimate(lat: float, lon: float, timeout: int = 6) -> Optional[SoilData]:
    """Interroge l'API publique SoilGrids (ISRIC) pour une estimation du sol
    a cette position (surface, 0-5cm). Ne leve jamais d'exception vers
    l'appelant : retourne None si hors ligne, si l'API ne répond pas a
    temps, ou si la réponse est inexploitable."""
    url = (
        "https://rest.isric.org/soilgrids/v2.0/properties/query"
        f"?lon={lon}&lat={lat}"
        "&property=phh2o&property=clay&property=sand&property=silt"
        "&depth=0-5cm&value=mean"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "drone-report-app/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None

    try:
        layers = {layer["name"]: layer for layer in data["properties"]["layers"]}

        def _val(name: str, divisor: float) -> Optional[float]:
            layer = layers.get(name)
            if not layer or not layer.get("depths"):
                return None
            raw = layer["depths"][0]["values"].get("mean")
            return (raw / divisor) if raw is not None else None

        ph = _val("phh2o", 10.0)     # SoilGrids encode le pH x10
        clay = _val("clay", 10.0)    # g/kg -> % (/10)
        sand = _val("sand", 10.0)
        silt = _val("silt", 10.0)

        if ph is None and None in (clay, sand, silt):
            return None

        texture = _classify_texture(sand, silt, clay) if None not in (sand, silt, clay) else None

        return SoilData(
            ph=ph,
            texture=texture,
            source="Estimation SoilGrids (ISRIC)",
            source_detail=(
                "Estimation régionale par géolocalisation (résolution ~250m), "
                "PAS une mesure réalisée sur cette parcelle. A confirmer par une "
                "analyse de sol de terrain avant toute décision d'investissement."
            ),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _classify_texture(sand: float, silt: float, clay: float) -> str:
    """Classification simplifiée a 4 classes (pas le triangle textural USDA
    complet, volontairement, pour rester lisible dans le rapport)."""
    if clay >= 40:
        return "Argileux"
    if sand >= 60:
        return "Sableux"
    if silt >= 50:
        return "Limoneux"
    return "Limono-argilo-sableux (mixte)"


# ----------------------------------------------------------------------------
# Base indicative de cultures courantes (Afrique de l'Ouest / Benin) et de
# leurs tolérances usuelles. Volontairement simple (règles, pas de modele) :
# chaque seuil est une indication générale, pas une norme agronomique
# absolue, et doit rester présente comme telle dans le rapport.
# ----------------------------------------------------------------------------
CROP_DATABASE = [
    {"nom": "Mais", "ph_min": 5.5, "ph_max": 7.5,
     "textures": ["Limoneux", "Limono-argilo-sableux (mixte)", "Sableux"],
     "tolère_pente_forte": False, "tolère_zone_humide": False},
    {"nom": "Manioc", "ph_min": 4.5, "ph_max": 7.0,
     "textures": ["Sableux", "Limono-argilo-sableux (mixte)"],
     "tolère_pente_forte": True, "tolère_zone_humide": False},
    {"nom": "Niebe (haricot local)", "ph_min": 5.5, "ph_max": 7.5,
     "textures": ["Sableux", "Limoneux", "Limono-argilo-sableux (mixte)"],
     "tolère_pente_forte": False, "tolère_zone_humide": False},
    {"nom": "Arachide", "ph_min": 5.5, "ph_max": 7.0,
     "textures": ["Sableux", "Limono-argilo-sableux (mixte)"],
     "tolère_pente_forte": False, "tolère_zone_humide": False},
    {"nom": "Riz (bas-fond)", "ph_min": 5.0, "ph_max": 7.0,
     "textures": ["Argileux", "Limoneux"],
     "tolère_pente_forte": False, "tolère_zone_humide": True},
    {"nom": "Palmier a huile", "ph_min": 4.5, "ph_max": 6.5,
     "textures": ["Argileux", "Limoneux", "Limono-argilo-sableux (mixte)"],
     "tolère_pente_forte": True, "tolère_zone_humide": True},
    {"nom": "Piment / tomate", "ph_min": 6.0, "ph_max": 7.5,
     "textures": ["Limoneux", "Limono-argilo-sableux (mixte)"],
     "tolère_pente_forte": False, "tolère_zone_humide": False},
    {"nom": "Coton", "ph_min": 5.5, "ph_max": 8.0,
     "textures": ["Limoneux", "Limono-argilo-sableux (mixte)", "Sableux"],
     "tolère_pente_forte": False, "tolère_zone_humide": False},
]


@dataclass
class CropSuggestion:
    nom: str
    adaptee: bool
    raisons: list = field(default_factory=list)  # critères qui écartent ou confirment la culture


def suggest_crops(
    soil: Optional[SoilData],
    mean_slope_pct: Optional[float],
    pct_low_zones: Optional[float],
    pente_forte_seuil: float = 15.0,
    zone_humide_seuil: float = 25.0,
) -> list:
    """Croise le sol (si disponible) et la topographie déjà calculee par
    l'application pour proposer une liste de cultures indicatives par
    parcelle. Ne renvoie jamais une seule réponse tranchée : chaque culture
    est accompagnée des critères qui l'écartent ou la confirment, pour que
    la lecture reste transparente plutôt qu'une boîte noire."""
    pente_forte = bool(mean_slope_pct is not None and mean_slope_pct > pente_forte_seuil)
    zone_humide = bool(pct_low_zones is not None and pct_low_zones > zone_humide_seuil)

    results = []
    for crop in CROP_DATABASE:
        raisons = []
        ok = True

        if soil and soil.ph is not None:
            if not (crop["ph_min"] <= soil.ph <= crop["ph_max"]):
                ok = False
                raisons.append(
                    f"pH du sol ({soil.ph:.1f}) hors de la plage habituelle "
                    f"({crop['ph_min']}-{crop['ph_max']})"
                )
        if soil and soil.texture:
            if soil.texture not in crop["textures"]:
                ok = False
                raisons.append(f"texture du sol ({soil.texture}) peu habituelle pour cette culture")
        if pente_forte and not crop["tolère_pente_forte"]:
            ok = False
            raisons.append(f"pente moyenne élevée ({mean_slope_pct:.0f}%) peu adaptee")
        if zone_humide and not crop["tolère_zone_humide"]:
            ok = False
            raisons.append(f"proportion importante de zones basses/humides ({pct_low_zones:.0f}%)")

        if not raisons:
            raisons.append("aucun critère disponible ne l'écarte")

        results.append(CropSuggestion(nom=crop["nom"], adaptee=ok, raisons=raisons))

    # cultures adaptees d'abord, puis les autres, ordre alphabetique dans chaque groupe
    results.sort(key=lambda c: (not c.adaptee, c.nom))
    return results
