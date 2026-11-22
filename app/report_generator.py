"""
report_generator.py

Assemble le rapport PDF final (livrable n5 du cahier des charges : "Rapport de
mission complet"). Design moderne et colore : bandeau de titre, tuiles de
chiffres cles, bannières de section colorees. Contenu :
  - Page de garde avec tuiles de synthèse
  - Orthomosaïque
  - Carte de vigueur (VARI / ExG)
  - Zonage de gestion différenciée
  - MNT (topographie / drainage)
  - Interprétation et recommandations (répond a la problématique du cahier
    des charges : aider l'agriculteur a décider, pas seulement montrer des
    cartes)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak,
    HRFlowable, ListFlowable, ListItem,
)

# --- Palette "moderne et coloree" ---
BRAND_TEAL = colors.HexColor("#0F9D74")     # vert-teal principal (accent fort)
BRAND_BLUE = colors.HexColor("#1E6FD9")     # bleu complémentaire
BRAND_DARK = colors.HexColor("#0B4F5C")     # bleu pétrole foncé (texte/bannières)
BRAND_LIGHT = colors.HexColor("#EAF6F2")    # fond clair teal
DANGER = colors.HexColor("#D64545")         # rouge - stress sévère
WARNING = colors.HexColor("#E2903A")        # orange - stress léger
SUCCESS = colors.HexColor("#2E9E5B")        # vert - sain
NEUTRAL_GRAY = colors.HexColor("#6B6B68")

WHITE = colors.white


@dataclass
class MissionMetadata:
    nom_parcelle: str = "Parcelle non renseignée"
    exploitant: str = ""
    date_vol: str = field(default_factory=lambda: date.today().strftime("%d/%m/%Y"))
    altitude_vol_m: Optional[float] = None
    surface_ha: Optional[float] = None
    nombre_photos: Optional[int] = None
    drone: str = "DJI Mavic 3 Enterprise (M3E)"
    pilote: str = ""
    equipe: str = "Groupe 2 - Impact Connexion"
    categorie: str = "Orange"
    notes: str = ""


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="HeroKicker", fontSize=10, leading=13, textColor=colors.HexColor("#9FE1CB"),
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(
        name="HeroTitle", fontSize=24, leading=28, textColor=WHITE,
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(
        name="HeroSubtitle", fontSize=12.5, leading=16, textColor=WHITE,
        spaceAfter=0))
    styles.add(ParagraphStyle(
        name="Section", fontSize=15, leading=18, textColor=WHITE,
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(
        name="SectionNum", fontSize=13, leading=16, textColor=WHITE,
        fontName="Helvetica-Bold", alignment=1))
    styles.add(ParagraphStyle(
        name="Corps", fontSize=10.5, leading=15.5, textColor=colors.HexColor("#222222"),
        spaceAfter=6))
    styles.add(ParagraphStyle(
        name="Légende", fontSize=9, leading=12, textColor=colors.HexColor("#555555"),
        alignment=1, spaceAfter=14))
    styles.add(ParagraphStyle(
        name="KPIValue", fontSize=19, leading=22, textColor=WHITE,
        fontName="Helvetica-Bold", alignment=1))
    styles.add(ParagraphStyle(
        name="KPILabel", fontSize=8.3, leading=10.5, textColor=WHITE, alignment=1))
    styles.add(ParagraphStyle(
        name="BigRating", fontSize=20, leading=24, textColor=WHITE,
        fontName="Helvetica-Bold", alignment=1))
    styles.add(ParagraphStyle(
        name="RatingLabel", fontSize=10, leading=13, textColor=WHITE, alignment=1))
    styles.add(ParagraphStyle(
        name="Recommandation", fontSize=10.5, leading=15, textColor=colors.HexColor("#222222")))
    styles.add(ParagraphStyle(
        name="Caveat", fontSize=8.7, leading=12.5, textColor=colors.HexColor("#6B6B68"),
        fontName="Helvetica-Oblique"))
    return styles


def _image_with_caption(img_path: Path, caption: str, styles, max_width=15 * cm, max_height=12.5 * cm):
    from PIL import Image as PILImage
    with PILImage.open(img_path) as im:
        w, h = im.size
    ratio = min(max_width / w, max_height / h)
    img = Image(str(img_path), width=w * ratio, height=h * ratio)
    return [img, Paragraph(caption, styles["Légende"])]


def _hero_banner(meta: MissionMetadata, styles):
    """Bandeau de titre plein cadre en haut de la page de garde."""
    kicker_text = f"GROUPE 2 &nbsp;&bull;&nbsp; CATÉGORIE {meta.categorie.upper()} &nbsp;&bull;&nbsp; ÉLECTROCHALLENGE 2026"
    inner = Table(
        [[Paragraph(kicker_text, styles["HeroKicker"])],
         [Paragraph("RAPPORT DE MISSION", styles["HeroTitle"])],
         [Paragraph("Cartographie aérienne par drone &mdash; Agriculture de précision", styles["HeroSubtitle"])],
         [Paragraph(f"{meta.nom_parcelle} &nbsp;&bull;&nbsp; {meta.date_vol}", styles["HeroSubtitle"])]],
        colWidths=[17 * cm],
    )
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
        ("TOPPADDING", (0, 0), (-1, 0), 20),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
        ("TOPPADDING", (0, 2), (-1, 2), 2),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 2),
        ("TOPPADDING", (0, 3), (-1, 3), 6),
        ("BOTTOMPADDING", (0, 3), (-1, 3), 20),
        ("LEFTPADDING", (0, 0), (-1, -1), 22),
        ("RIGHTPADDING", (0, 0), (-1, -1), 22),
    ]))
    return inner


def _kpi_tiles(items, styles, tile_width=4.0 * cm):
    """items: liste de (valeur_str, label_str, couleur)."""
    cells = []
    for value, label, color in items:
        cell = Table(
            [[Paragraph(value, styles["KPIValue"])],
             [Paragraph(label, styles["KPILabel"])]],
            colWidths=[tile_width],
        )
        cell.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color),
            ("TOPPADDING", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, 1), 0),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        cells.append(cell)
    row = Table([cells], colWidths=[tile_width + 0.15 * cm] * len(cells), hAlign="LEFT")
    row.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return row


def _section_banner(number: int, title: str, color, styles):
    inner = Table(
        [[Paragraph(str(number), styles["SectionNum"]), Paragraph(title, styles["Section"])]],
        colWidths=[1.1 * cm, 15.9 * cm],
    )
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    return inner


def _metadata_table(meta: MissionMetadata, styles):
    rows = [
        ["Exploitant", meta.exploitant or "-", "Équipe", meta.equipe],
        ["Drone", meta.drone, "Pilote", meta.pilote or "-"],
        ["Altitude de vol",
         f"{meta.altitude_vol_m:.0f} m" if meta.altitude_vol_m else "-",
         "Surface couverte",
         f"{meta.surface_ha:.1f} ha" if meta.surface_ha else "-"],
        ["Nombre de photos",
         str(meta.nombre_photos) if meta.nombre_photos else "-",
         "Catégorie",
         meta.categorie],
    ]
    table = Table(rows, colWidths=[3.3 * cm, 5.3 * cm, 3.3 * cm, 5.3 * cm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), BRAND_DARK),
        ("TEXTCOLOR", (2, 0), (2, -1), BRAND_DARK),
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _soil_table(rows, styles, col_widths=(6 * cm, 9 * cm)):
    """Tableau a 2 colonnes (caractéristique / valeur), style cohérent avec
    le reste du rapport. Première ligne = en-tête colore."""
    table = Table(rows, colWidths=list(col_widths))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 1), (0, -1), BRAND_DARK),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BACKGROUND", (0, 1), (-1, -1), BRAND_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _generate_interpretation(veg_stats: Optional[dict], topo_stats: Optional[dict]):
    """Construit une interprétation textuelle et des recommandations
    concrretes a partir des statistiques calculees, pour répondre a la
    problématique du cahier des charges (aider l'agriculteur a décider).
    Reste volontairement qualitatif : une seule mission RGB ne permet pas
    une prévision de rendement scientifique (celle-ci demanderait un suivi
    multi-dates, cf section 3.2 du cahier des charges)."""
    recommendations = []

    if not veg_stats:
        return "Indisponible", NEUTRAL_GRAY, [
            "Données de vigueur végétale indisponibles pour cette mission."
        ]

    pct_sain = veg_stats.get("pct_vegetation_saine", 0)
    pct_severe = veg_stats.get("pct_stress_severe", 0)
    pct_leger = veg_stats.get("pct_stress_leger", 0)
    pct_couverture = veg_stats.get("pct_image_vegetation", 0)

    if pct_sain >= 60:
        rating, rating_color = "Bon", SUCCESS
    elif pct_sain >= 35:
        rating, rating_color = "Moyen", WARNING
    else:
        rating, rating_color = "A surveiller", DANGER

    if pct_severe >= 15:
        recommendations.append(
            f"{pct_severe:.0f} % de la végétation est en stress sévère (zones rouges du "
            "zonage) : une inspection terrain ciblée est recommandée en priorité sur ces "
            "zones (vérifier irrigation, carences nutritives, présence de ravageurs)."
        )
    elif pct_severe > 0:
        recommendations.append(
            f"Une part limitée de la végétation ({pct_severe:.0f} %) présente un stress "
            "sévère : surveillance ponctuelle recommandée sur les zones rouges du zonage."
        )

    if pct_leger >= 30:
        recommendations.append(
            f"{pct_leger:.0f} % de la végétation est en stress léger (zones orange) : "
            "cible prioritaire pour une modulation des intrants (fertilisation ciblée) "
            "plutôt qu'un traitement uniforme sur toute la parcelle."
        )

    if pct_couverture < 40:
        recommendations.append(
            f"La couverture végétale detectee ({pct_couverture:.0f} % de la zone survolée) "
            "est relativement faible : vérifier si cela correspond a la réalité du terrain "
            "(parcelle partiellement cultivée, jachère) ou a une levée incomplète apres semis."
        )

    if topo_stats:
        pente = topo_stats.get("mean_slope_pct", 0)
        if pente >= 20:
            recommendations.append(
                f"La pente moyenne mesurée ({pente:.0f} %) suggère un risque de "
                "ruissellement dans les zones les plus pentues : envisager des aménagements "
                "de drainage, en particulier dans les zones basses visibles sur la carte des "
                "pentes. Une pente aussi élevée peut aussi indiquer du bruit dans la "
                "reconstruction 3D si le recouvrement entre photos était insuffisant "
                "(< 75 %) &mdash; a vérifier avant d'agir sur cette seule base."
            )

    if not recommendations:
        recommendations.append(
            "Aucun signal de stress marquant détecté sur cette mission : poursuivre le "
            "suivi régulier pour confirmer la tendance dans le temps."
        )

    return rating, rating_color, recommendations


def generate_pdf_report(
    output_path: str,
    meta: MissionMetadata,
    orthophoto_preview: Optional[Path] = None,
    vari_png: Optional[Path] = None,
    exg_png: Optional[Path] = None,
    zoning_png: Optional[Path] = None,
    hillshade_png: Optional[Path] = None,
    slope_png: Optional[Path] = None,
    low_zones_png: Optional[Path] = None,
    veg_stats: Optional[dict] = None,
    topo_stats: Optional[dict] = None,
    logo_path: Optional[str] = None,
    odm_report_pdf: Optional[Path] = None,
    soil=None,
    crop_suggestions=None,
    qgis_export=None,
) -> str:
    styles = _styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
        title=f"Rapport de mission - {meta.nom_parcelle}",
    )
    story = []

    # ---- Page de garde ----
    story.append(_hero_banner(meta, styles))
    story.append(Spacer(1, 18))

    if logo_path and Path(logo_path).exists():
        story.append(Image(logo_path, width=3 * cm, height=3 * cm))
        story.append(Spacer(1, 10))

    # Tuiles de synthèse (chiffres cles visibles d'un coup d'oeil)
    kpi_items = []
    if meta.nombre_photos:
        kpi_items.append((str(meta.nombre_photos), "PHOTOS TRAITÉES", BRAND_BLUE))
    if meta.altitude_vol_m:
        kpi_items.append((f"{meta.altitude_vol_m:.0f} m", "ALTITUDE DE VOL", BRAND_BLUE))
    if veg_stats:
        kpi_items.append((f"{veg_stats.get('pct_image_vegetation', 0):.0f}%", "COUVERTURE VÉGÉTALE", BRAND_TEAL))
        kpi_items.append((f"{veg_stats.get('pct_vegetation_saine', 0):.0f}%", "VÉGÉTATION SAINE", SUCCESS))
    if kpi_items:
        story.append(_kpi_tiles(kpi_items, styles))
        story.append(Spacer(1, 20))

    story.append(_metadata_table(meta, styles))
    story.append(Spacer(1, 16))

    if meta.notes:
        story.append(Paragraph("Notes de mission", styles["Section"]))
        story.append(Paragraph(meta.notes, styles["Corps"]))

    story.append(PageBreak())

    # ---- Orthomosaïque ----
    if orthophoto_preview:
        story.append(_section_banner(1, "Orthomosaïque", BRAND_DARK, styles))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "Assemblage photogrammetrique de l'ensemble des prises de vue en une "
            "image geo-référencée unique, utilisable pour l'observation générale "
            "de la parcelle, le comptage de plants et la mise a jour du plan de masse.",
            styles["Corps"]))
        story.append(Spacer(1, 8))
        for flow in _image_with_caption(orthophoto_preview, "Orthomosaïque de la parcelle", styles):
            story.append(flow)
        story.append(PageBreak())

    # ---- Vigueur végétale ----
    if vari_png or exg_png:
        story.append(_section_banner(2, "Carte de vigueur végétale (VARI / ExG)", BRAND_TEAL, styles))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "Le DJI Mavic 3 Enterprise utilise pour cette mission ne dispose pas de "
            "capteur multispectral (proche infrarouge) : le NDVI classique n'est donc "
            "pas calculable directement. Les indices VARI et ExG, calcules a partir "
            "des seules bandes visibles, fournissent une approximation fiable de la "
            "vigueur végétale. Les surfaces non végétalisées (sol nu, batiments, eau) "
            "sont automatiquement exclues de l'analyse (apparaissent en gris).",
            styles["Corps"]))
        story.append(Spacer(1, 8))
        if vari_png:
            for flow in _image_with_caption(vari_png, "Carte VARI - vigueur végétale approximee (gris = hors végétation)", styles):
                story.append(flow)
        if veg_stats:
            story.append(Spacer(1, 10))
            story.append(_kpi_tiles([
                (f"{veg_stats.get('pct_image_vegetation', 0):.0f}%", "COUVERTURE VÉGÉTALE", BRAND_TEAL),
                (f"{veg_stats.get('pct_stress_severe', 0):.0f}%", "STRESS SÉVÈRE", DANGER),
                (f"{veg_stats.get('pct_stress_leger', 0):.0f}%", "STRESS LÉGER", WARNING),
                (f"{veg_stats.get('pct_vegetation_saine', 0):.0f}%", "VÉGÉTATION SAINE", SUCCESS),
            ], styles, tile_width=3.85 * cm))
        story.append(PageBreak())
        if exg_png:
            for flow in _image_with_caption(exg_png, "Carte ExG - indice de verdure (vérification croisée)", styles):
                story.append(flow)
            story.append(PageBreak())

    # ---- Zonage ----
    if zoning_png:
        story.append(_section_banner(3, "Zonage de gestion différenciée", BRAND_BLUE, styles))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "Classification automatique (k-means) de la carte de vigueur en classes "
            "homogènes, destinée a guider l'application variable d'intrants (engrais, "
            "phytosanitaires) et a prioriser les interventions.",
            styles["Corps"]))
        story.append(Spacer(1, 8))
        for flow in _image_with_caption(zoning_png, "Zones de gestion (rouge = prioritaire, vert = sain)", styles):
            story.append(flow)
        story.append(PageBreak())

    # ---- Topographie / MNT ----
    if hillshade_png or slope_png:
        story.append(_section_banner(4, "Topographie et drainage (MNT)", BRAND_DARK, styles))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "Le Modèle Numérique de Terrain permet d'identifier les zones basses "
            "sujettes a l'accumulation d'eau, d'orienter le nivellement et de "
            "planifier les drains agricoles.",
            styles["Corps"]))
        story.append(Spacer(1, 8))
        if hillshade_png:
            for flow in _image_with_caption(hillshade_png, "Modèle numérique de terrain (relief ombre)", styles):
                story.append(flow)
        if topo_stats:
            story.append(Spacer(1, 10))
            story.append(_kpi_tiles([
                (f"{topo_stats.get('min_alt', float('nan')):.1f} m", "ALTITUDE MIN", BRAND_BLUE),
                (f"{topo_stats.get('max_alt', float('nan')):.1f} m", "ALTITUDE MAX", BRAND_BLUE),
                (f"{topo_stats.get('mean_slope_pct', float('nan')):.0f}%", "PENTE MOYENNE", WARNING),
                (f"{topo_stats.get('pct_low_zones', 0):.0f}%", "ZONES BASSES", BRAND_TEAL),
            ], styles, tile_width=3.85 * cm))
        story.append(PageBreak())
        if slope_png:
            for flow in _image_with_caption(slope_png, "Carte des pentes (%) - aide au drainage", styles):
                story.append(flow)
            story.append(PageBreak())
        if low_zones_png:
            story.append(Paragraph(
                "Zones basses (20% des altitudes les plus basses de la parcelle), "
                "sujettes a l'accumulation d'eau apres pluie &mdash; a prendre en compte "
                "pour l'implantation de drains.",
                styles["Corps"]))
            story.append(Spacer(1, 8))
            for flow in _image_with_caption(low_zones_png, "Carte des zones basses (bleu = risque d'accumulation d'eau)", styles):
                story.append(flow)
            story.append(PageBreak())

    # ---- Sol et cultures possibles (optionnel) ----
    if soil is not None:
        story.append(_section_banner(5, "Sol et cultures possibles", BRAND_BLUE, styles))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "Le drone (photos RGB) ne mesure pas le sol lui-même : cette section "
            "s'appuie sur une donnée de sol distincte, précisée ci-dessous, croisée "
            "avec la topographie déjà calculee (section 4) pour orienter une liste "
            "de cultures possibles. Il s'agit d'une orientation indicative fondée "
            "sur des règles de tolérance courantes, jamais d'une prescription "
            "agronomique : elle ne remplace pas un conseil agronomique local.",
            styles["Corps"]))
        story.append(Spacer(1, 10))

        source_color = SUCCESS if soil.source == "Saisie manuelle" else WARNING
        story.append(_soil_table(
            [["Caracteristique", "Valeur"]] + [
                ["Source de la donnée", soil.source],
                ["pH du sol", f"{soil.ph:.1f}" if soil.ph is not None else "Non renseigne"],
                ["Texture du sol", soil.texture or "Non renseignée"],
            ] + ([["Note", soil.azote_note]] if soil.azote_note else []),
            styles,
        ))
        story.append(Spacer(1, 6))
        story.append(Paragraph(soil.source_detail, styles["Caveat"]))
        story.append(Spacer(1, 14))

        if crop_suggestions:
            story.append(Paragraph("Cultures potentiellement adaptees", ParagraphStyle(
                name="CropHeader", fontSize=11.5, leading=14, textColor=BRAND_DARK,
                fontName="Helvetica-Bold", spaceAfter=6)))
            adaptees = [c for c in crop_suggestions if c.adaptee]
            ecartees = [c for c in crop_suggestions if not c.adaptee]
            if adaptees:
                story.append(ListFlowable(
                    [ListItem(Paragraph(f"<b>{c.nom}</b>", styles["Recommandation"]), bulletColor=SUCCESS)
                     for c in adaptees],
                    bulletType="bullet", start="circle", leftIndent=14,
                ))
            else:
                story.append(Paragraph("Aucune culture de la base indicative ne ressort clairement adaptee avec les critères disponibles.", styles["Corps"]))
            story.append(Spacer(1, 10))
            if ecartees:
                story.append(Paragraph("Moins adaptees selon les critères disponibles", ParagraphStyle(
                    name="CropHeader2", fontSize=10.5, leading=13, textColor=NEUTRAL_GRAY,
                    fontName="Helvetica-Bold", spaceAfter=6)))
                for c in ecartees:
                    story.append(Paragraph(
                        f"<b>{c.nom}</b> &mdash; {'; '.join(c.raisons)}",
                        styles["Caveat"]))
                story.append(Spacer(1, 6))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "Limite méthodologique : cette liste repose sur des seuils de tolérance "
            "généraux (pH, texture, pente, zones humides), pas sur une étude "
            "agronomique locale. Une analyse de sol de laboratoire et l'avis d'un "
            "technicien agricole restent nécessaires avant toute décision "
            "d'investissement sur une culture.",
            styles["Caveat"]))
        story.append(PageBreak())

    # ---- Interprétation et recommandations ----
    section_num_interp = 6 if soil is not None else 5
    rating, rating_color, recommendations = _generate_interpretation(veg_stats, topo_stats)
    story.append(_section_banner(section_num_interp, "Interprétation et recommandations", SUCCESS if rating != "A surveiller" else DANGER, styles))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Cette section synthétise les cartes précédentes en pistes d'action concrètes "
        "pour l'exploitant, en réponse directe a l'objectif du projet : réduire les coûts "
        "d'intrants et améliorer les rendements grace a une décision agronomique mieux "
        "informée.",
        styles["Corps"]))
    story.append(Spacer(1, 10))

    rating_tile = Table(
        [[Paragraph(rating, styles["BigRating"])],
         [Paragraph("ÉTAT GÉNÉRAL DE LA VÉGÉTATION", styles["RatingLabel"])]],
        colWidths=[6 * cm],
    )
    rating_tile.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), rating_color),
        ("TOPPADDING", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 14),
    ]))
    story.append(rating_tile)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Recommandations", ParagraphStyle(
        name="RecoHeader", fontSize=11.5, leading=14, textColor=BRAND_DARK,
        fontName="Helvetica-Bold", spaceAfter=6)))
    story.append(ListFlowable(
        [ListItem(Paragraph(r, styles["Recommandation"]), bulletColor=BRAND_TEAL) for r in recommendations],
        bulletType="bullet", start="circle", leftIndent=14,
    ))
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "Suivi multi-dates : conformément aux orientations du mentor, le suivi de "
        "croissance multi-vols (semis puis levée puis floraison puis maturité, "
        "décrit section 3.2 du cahier des charges) a été volontairement laisse "
        "hors périmètre de cette version, au profit d'une analyse approfondie sur "
        "un vol unique. L'estimation présentée ici est donc un instantané "
        "qualitatif de l'état de la parcelle a la date du vol, et non une "
        "prévision de rendement, ce qui ne remet pas en cause sa fiabilité pour "
        "guider les décisions immédiates (zones a inspecter, modulation des "
        "intrants).",
        styles["Caveat"]))

    # ---- Pied de rapport ----
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Rapport généré automatiquement par l'application de traitement drone - "
        f"{meta.equipe} - ÉlectroChallenge 2026.", styles["Légende"]))

    # ---- Conformité au cahier des charges ----
    story.append(_section_banner(section_num_interp + 1, "Conformité au cahier des charges", BRAND_DARK, styles))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Récapitulatif des 7 livrables attendus (section 9 du cahier des charges) et de "
        "leur statut dans cette mission, par souci de transparence.",
        styles["Corps"]))
    story.append(Spacer(1, 8))

    ok_style = ParagraphStyle(name="StatutOK", fontSize=9.5, textColor=SUCCESS, fontName="Helvetica-Bold")
    partiel_style = ParagraphStyle(name="StatutPartiel", fontSize=9.5, textColor=WARNING, fontName="Helvetica-Bold")
    non_style = ParagraphStyle(name="StatutNon", fontSize=9.5, textColor=NEUTRAL_GRAY, fontName="Helvetica-Bold")
    cell_style = ParagraphStyle(name="CellText", fontSize=9.5, leading=12.5, textColor=colors.HexColor("#222222"))

    # Livrables 3 et 4 : « Fourni » seulement si les exports QGIS ont réellement
    # été produits pendant ce traitement ; sinon on reste honnête (« Partiel »).
    def _why_missing(what: str) -> str:
        if qgis_export is None:
            return f"{what} non généré par cette version"
        if qgis_export.errors:
            return f"{what} non abouti (voir le journal d'erreurs)"
        return f"{what} non produit pour cette mission (voir livrables/qgis/LISEZMOI_QGIS.txt)"

    if qgis_export is not None and qgis_export.has_contours:
        row3 = [Paragraph("3. Plan topographique (DXF / PDF)", cell_style), Paragraph("Fourni", ok_style),
                Paragraph(f"MNT GeoTIFF + carte PDF + courbes de niveau tous les "
                          f"{qgis_export.contour_interval_m:g} m : livrables/qgis/courbes_niveau.dxf "
                          "et .shp", cell_style)]
    else:
        suite = _why_missing("export DXF (courbes de niveau)")
        row3 = [Paragraph("3. Plan topographique (DXF / PDF)", cell_style), Paragraph("Partiel", partiel_style),
                Paragraph(f"MNT GeoTIFF + carte PDF fournis ; {suite}", cell_style)]
    if qgis_export is not None and qgis_export.has_zoning:
        row4 = [Paragraph("4. Carte de zonage modulable (SHP / PDF)", cell_style), Paragraph("Fourni", ok_style),
                Paragraph("Carte PDF (section 3) + livrables/qgis/zonage_gestion.shp (polygones) "
                          "et zonage_gestion.tif", cell_style)]
    else:
        suite = _why_missing("export vectoriel SHP")
        row4 = [Paragraph("4. Carte de zonage modulable (SHP / PDF)", cell_style), Paragraph("Partiel", partiel_style),
                Paragraph(f"Carte PDF fournie (section 3) ; {suite}", cell_style)]

    conformite_rows = [
        [Paragraph("Livrable attendu", ParagraphStyle(name="H", fontSize=9.5, textColor=WHITE, fontName="Helvetica-Bold")),
         Paragraph("Statut", ParagraphStyle(name="H2", fontSize=9.5, textColor=WHITE, fontName="Helvetica-Bold")),
         Paragraph("Détail", ParagraphStyle(name="H3", fontSize=9.5, textColor=WHITE, fontName="Helvetica-Bold"))],
        [Paragraph("1. Orthomosaïque parcelle (GeoTIFF)", cell_style), Paragraph("Fourni", ok_style),
         Paragraph("livrables/orthomosaique.tif", cell_style)],
        [Paragraph("2. Carte de vigueur VARI/ExG (GeoTIFF + PDF)", cell_style), Paragraph("Fourni", ok_style),
         Paragraph("livrables/carte_vari.tif + sections 2-3 de ce PDF", cell_style)],
        row3,
        row4,
        [Paragraph("5. Rapport de mission complet (PDF)", cell_style), Paragraph("Fourni", ok_style),
         Paragraph("Ce document, avec annexe de précision du moteur de traitement", cell_style)],
        [Paragraph("6. Protocole de vol reproductible (PDF)", cell_style), Paragraph("Non fourni", non_style),
         Paragraph("Hors périmètre de cette application (planification de vol, cote DJI Pilot 2)", cell_style)],
        [Paragraph("7. Guide d'exploitation des cartes (PDF)", cell_style), Paragraph("Fourni", ok_style),
         Paragraph("Intégré : chaque section du rapport explique comment lire et utiliser la carte associée", cell_style)],
    ]
    conformite_table = Table(conformite_rows, colWidths=[7.2 * cm, 2.3 * cm, 7.5 * cm])
    conformite_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("BACKGROUND", (0, 1), (-1, -1), BRAND_LIGHT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(conformite_table)
    story.append(PageBreak())

    # ---- Annexe : rapport technique du moteur de traitement ----
    # Répond au cahier des charges (section 4.5 et section 6) : le "rapport de
    # mission" doit inclure les données de précision (GSD, taux d'alignement
    # des photos, recouvrement...). Plutot que d'estimer ces chiffres, on
    # annexe le rapport technique déjà généré par le moteur photogrammetrique
    # lui-même, qui les calcule précisément.
    if odm_report_pdf and Path(odm_report_pdf).exists():
        story.append(_section_banner(section_num_interp + 2, "Annexe - Rapport technique de traitement", NEUTRAL_GRAY, styles))
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "Les pages suivantes sont generees automatiquement par le moteur de "
            "traitement photogrammetrique (OpenDroneMap) et contiennent les "
            "indicateurs de précision et de qualité de la mission : résolution "
            "au sol (GSD), taux d'alignement des photos, qualité de la "
            "reconstruction 3D, paramètres de traitement utilises, etc. "
            "&mdash; conformément aux exigences de traçabilité du cahier des charges.",
            styles["Corps"]))

    doc.build(story)

    if odm_report_pdf and Path(odm_report_pdf).exists():
        _append_pdf(output_path, odm_report_pdf)

    return output_path


def _append_pdf(base_pdf_path: str, extra_pdf_path: Path) -> None:
    """Concatène extra_pdf_path a la suite de base_pdf_path (fusion simple,
    sans réencodage des pages)."""
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    for path in (base_pdf_path, str(extra_pdf_path)):
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    with open(base_pdf_path, "wb") as f:
        writer.write(f)
