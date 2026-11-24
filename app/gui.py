"""
gui.py

Interface graphique de bureau (CustomTkinter : un habillage moderne de Tkinter,
embarqué dans l'exécutable, rien à installer sur les postes de l'équipe).

Palette « Parcelle & Télémétrie » :
  - Fond lin naturel (#F6F4EF) et bordures sable (#DFD9CE) pour ancrer
    l'univers agricole et terrain.
  - Structure pétrole (#0B4F5C) et primaire émeraude (#0F9D74) pour les
    actions principales et la végétation.
  - Bleu télémétrie (#1E6FD9) pour les éléments techniques (moteur ODM,
    topographie/MNT, exports SIG).
  - Orange latérite (#DF7E26) pour l'identité Catégorie Orange et les
    alertes / points de vigilance.
"""

from __future__ import annotations

import glob
import os
import shutil
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import StringVar, IntVar, DoubleVar, BooleanVar, filedialog, messagebox, Canvas

import customtkinter as ctk
from PIL import Image as PILImage

from app.odm_client import ODMClient, ODMProcessingError
from app.raster_processing import (
    compute_vegetation_indices, compute_topography, make_orthophoto_preview,
    compute_surveyed_area_ha, get_center_latlon, zone_palette,
)
from app.report_generator import MissionMetadata, generate_pdf_report
from app.gis_export import export_qgis_package, QgisExportResult
from app.soil_data import soil_data_from_manual, fetch_soilgrids_estimate, suggest_crops

IMAGE_EXTENSIONS = ("*.jpg", "*.jpeg", "*.JPG", "*.JPEG", "*.png", "*.PNG")


def unique_paths(paths):
    """Retire les doublons d'une liste de chemins en conservant l'ordre.
    La comparaison tient compte du système : insensible à la casse sous
    Windows (os.path.normcase), sensible sous Linux/macOS."""
    seen = set()
    result = []
    for p in sorted(paths):
        key = os.path.normcase(os.path.abspath(p))
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result


# ----------------------------------------------------------------------------
# Palette « Parcelle & Télémétrie » (1 + 3 + 4)
# ----------------------------------------------------------------------------
BRAND_DARK = "#0B4F5C"          # Pétrole profond (en-tête, titres)
BRAND_DARK_ALT = "#126474"      # Survol pétrole
BRAND_TEAL = "#0F9D74"          # Émeraude drone (CTA principal, actif)
BRAND_TEAL_HOVER = "#0C8260"    # Survol émeraude
BRAND_TEAL_SOFT = "#E5F5EF"     # Fond doux émeraude (badges succès / infos)

TELEMETRY_BLUE = "#1E6FD9"      # Bleu télémétrie (moteur ODM, SIG, MNT)
TELEMETRY_SOFT = "#E8F1FC"      # Fond doux bleu télémétrie

ACCENT_ORANGE = "#DF7E26"       # Orange latérite (Catégorie Orange / vigilance)
ACCENT_ORANGE_SOFT = "#FDF1E6"  # Fond doux orange

APP_BG = "#F6F4EF"              # Fond lin naturel (chaleureux et reposant)
CARD_BG = "#FFFFFF"             # Cartes blanc ivoire
SUBTLE_BG = "#EFECE4"           # Fond onglets inactifs / zones secondaires
HOVER_SOFT = "#EDF3F0"          # Survol boutons secondaires
BORDER = "#DFD9CE"              # Bordure sable pierre
FIELD_BORDER = "#C7BFB0"        # Bordure champs de saisie

TEXT_PRIMARY = "#1E292B"        # Texte principal très lisible
TEXT_MUTED = "#626662"          # Texte secondaire / aides
DANGER = "#D64545"              # Erreur
DANGER_SOFT = "#FCEAEA"         # Fond doux erreur

# Libellé de la liste « texture du sol » quand rien n'est renseigné.
TEXTURE_NONE = "Non renseignée"
TEXTURES = (TEXTURE_NONE, "Sableux", "Limoneux", "Argileux", "Limono-argilo-sableux (mixte)")

# Préréglages de qualité sélectionnables dans l'onglet "2. Moteur & SIG"
QUALITY_PRESETS = {
    "economique": {},
    "standard": {"pc-quality": "high", "feature-quality": "high"},
    "maximale": {"pc-quality": "ultra", "feature-quality": "ultra"},
}


def _write_error_log(exc_text: str, out_dir: str | None) -> str:
    """Enregistre le détail technique d'une erreur dans un fichier log."""
    try:
        base = Path(out_dir) if out_dir else Path.home() / "Documents" / "rapports_drone"
        logs_dir = base / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = logs_dir / f"erreur_{stamp}.log"
        log_path.write_text(exc_text, encoding="utf-8")
        return str(log_path)
    except Exception:
        return ""


def _copy_if_exists(src, dst):
    """Copie src vers dst si src existe et n'est pas None ; ignore sinon."""
    try:
        if src is None:
            return
        src_path = Path(src)
        if src_path.exists():
            shutil.copy2(src_path, dst)
    except Exception:
        pass


class DroneReportApp:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Vision Agricole — Agriculture de précision")
        self.root.configure(fg_color=APP_BG)

        try:
            self._scale = float(self.root._get_window_scaling())
        except Exception:
            self._scale = 1.0
        scale = self._scale
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        phys_w = max(620 * scale, min(860 * scale, screen_w - 40))
        phys_h = max(440 * scale, min(940 * scale, screen_h - 90))
        win_w = int(phys_w / scale)
        win_h = int(phys_h / scale)
        pos_x = max(0, int((screen_w - win_w * scale) // 2))
        pos_y = max(0, int((screen_h - win_h * scale) // 2 - 20))
        self.root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.root.minsize(620, 440)
        self._compact = win_h < 580

        # Variables de formulaire
        self.images_dir = StringVar()
        self.images_count_text = StringVar(value="Aucun dossier sélectionné")
        self.output_dir = StringVar(value=str(Path.home() / "Documents" / "rapports_drone"))
        self.node_host = StringVar(value="localhost")
        self.node_port = IntVar(value=3000)
        self.engine_status_text = StringVar(value="Statut : non vérifié")

        self.nom_parcelle = StringVar()
        self.exploitant = StringVar()
        self.date_vol = StringVar()
        self.altitude_vol = StringVar()
        self.pilote = StringVar()
        self.equipe = StringVar(value="Groupe 2 - Impact Connexion")
        self.n_zones = StringVar(value="4")

        self.soil_ph = StringVar()
        self.soil_texture = StringVar(value=TEXTURE_NONE)
        self.soil_azote_note = StringVar()
        self.allow_soilgrids = BooleanVar(value=False)
        self.quality_level = StringVar(value="economique")

        self.status_text = StringVar(value="Prêt à démarrer une mission.")
        self.elapsed_text = StringVar(value="")
        self.progress_value = DoubleVar(value=0)
        self.percent_text = StringVar(value="")
        self.progress_value.trace_add("write", self._update_percent)

        # État des résultats pour l'onglet 4 (Aperçu des cartes)
        self._preview_maps: dict[str, Path] = {}
        self._preview_titles: dict[str, str] = {}
        self._selected_map_key = StringVar(value="ortho")
        self._last_pdf_path: str | None = None
        self._last_output_dir: str | None = None
        self._ctk_preview_image = None  # conserve la référence CTkImage

        self._is_processing = False
        self._processing_start_time = 0.0
        self._last_pct_value = None
        self._last_pct_update_time = 0.0
        self._progress_indeterminate = False

        self._build_ui()

    # ------------------------------------------------------ filet de sécurité

    def handle_tk_exception(self, exc_type, exc_value, exc_tb):
        """Filet de sécurité global pour les callbacks Tkinter."""
        try:
            exc_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        except Exception:
            exc_text = f"{exc_type}: {exc_value}"

        log_path = _write_error_log(exc_text, self.output_dir.get() if hasattr(self, "output_dir") else None)

        try:
            if getattr(self, "launch_btn", None) is not None:
                self._set_launch_enabled(True)
        except Exception:
            pass

        detail = f"\n\nDétail technique enregistré dans :\n{log_path}" if log_path else ""
        try:
            messagebox.showerror(
                "Erreur inattendue",
                "Une erreur inattendue s'est produite, mais l'application reste "
                "ouverte et utilisable." + detail,
            )
        except Exception:
            pass

    # ------------------------------------------------------------------ UI

    def _update_percent(self, *_):
        try:
            value = int(round(self.progress_value.get()))
            self.percent_text.set(f"{value} %" if value > 0 else "")
            if not getattr(self, "_progress_indeterminate", False):
                bar = getattr(self, "progress", None)
                if bar is not None:
                    bar.set(max(0.0, min(1.0, self.progress_value.get() / 100.0)))
        except Exception:
            pass

    # ------------------------------------------------------------ helpers UI

    def _font(self, size: int, bold: bool = False):
        return ctk.CTkFont(size=size, weight="bold" if bold else "normal")

    def _set_launch_enabled(self, enabled: bool):
        try:
            self.launch_btn.configure(
                state="normal" if enabled else "disabled",
                fg_color=BRAND_TEAL if enabled else "#A8BEB6",
            )
        except Exception:
            pass

    def _card(self, parent, title: str, accent_color: str = BRAND_TEAL, subtitle: str = ""):
        """Carte blanc ivoire avec liseré d'accent thématique à gauche du titre."""
        card = ctk.CTkFrame(
            parent, fg_color=CARD_BG, border_width=1,
            border_color=BORDER, corner_radius=12,
        )
        card.pack(fill="x", pady=(0, 14), padx=2)

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(14, 6))

        pill = ctk.CTkFrame(head, width=4, height=18, fg_color=accent_color, corner_radius=2)
        pill.pack(side="left", padx=(0, 10))
        pill.pack_propagate(False)

        title_col = ctk.CTkFrame(head, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_col, text=title, text_color=BRAND_DARK, anchor="w",
            font=self._font(14, True),
        ).pack(anchor="w")

        if subtitle:
            ctk.CTkLabel(
                title_col, text=subtitle, text_color=TEXT_MUTED, anchor="w",
                font=self._font(11),
            ).pack(anchor="w")

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(2, 16))
        body.columnconfigure(0, minsize=205)
        body.columnconfigure(1, weight=1)
        return body

    def _label(self, body, row: int, text: str):
        ctk.CTkLabel(
            body, text=text, text_color=TEXT_PRIMARY, anchor="w",
            font=self._font(13),
        ).grid(row=row, column=0, sticky="w", pady=6, padx=(0, 14))

    def _hint(self, body, row: int, text: str, bg_color: str | None = None):
        if bg_color:
            box = ctk.CTkFrame(body, fg_color=bg_color, corner_radius=8)
            box.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(0, 10))
            ctk.CTkLabel(
                box, text=text, text_color=TEXT_PRIMARY, anchor="w", justify="left",
                wraplength=530, font=self._font(12),
            ).pack(fill="x", padx=12, pady=8)
        else:
            ctk.CTkLabel(
                body, text=text, text_color=TEXT_MUTED, anchor="w", justify="left",
                wraplength=530, font=self._font(12),
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 8))

    def _entry(self, body, row: int, var, sticky: str = "ew", width: int = 140, placeholder: str = ""):
        kwargs = {} if sticky == "ew" else {"width": width}
        entry = ctk.CTkEntry(
            body, textvariable=var, height=35, corner_radius=8,
            border_width=1, border_color=FIELD_BORDER,
            fg_color="#FCFBF9", text_color=TEXT_PRIMARY,
            placeholder_text=placeholder,
            font=self._font(13), **kwargs,
        )
        entry.grid(row=row, column=1, sticky=sticky, pady=6)
        return entry

    def _secondary_button(self, parent, text: str, command, width: int = 115, accent: str = BRAND_DARK):
        return ctk.CTkButton(
            parent, text=text, command=command, width=width, height=35,
            corner_radius=8, fg_color="white", text_color=accent,
            border_width=1, border_color=FIELD_BORDER, hover_color=HOVER_SOFT,
            font=self._font(12, True),
        )

    def _draw_logo(self, parent, factor: float = 1.0):
        k = self._scale * factor
        size = int(50 * k)
        logo = Canvas(parent, width=size, height=size, bg=BRAND_DARK, highlightthickness=0)

        def pts(*coords):
            return [c * k for c in coords]

        logo.create_oval(*pts(1, 1, 49, 49), fill="", outline="#278291", width=max(1, int(1.5 * k)))
        logo.create_oval(*pts(4, 4, 46, 46), fill=BRAND_TEAL, outline="")
        logo.create_polygon(
            *pts(14, 35, 12, 22, 21, 13, 34, 12, 36, 25, 28, 35),
            smooth=True, fill="white", outline="",
        )
        logo.create_line(*pts(16, 33, 31, 17), fill=BRAND_TEAL, width=max(2, int(2.2 * k)))
        return logo

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        root = self.root
        compact = self._compact

        # ---- En-tête : pétrole profond + badge Catégorie Orange ----
        header = ctk.CTkFrame(root, fg_color=BRAND_DARK, corner_radius=0)
        header.pack(fill="x")

        head_inner = ctk.CTkFrame(header, fg_color="transparent")
        head_inner.pack(fill="x", padx=24, pady=9 if compact else 15)

        self._draw_logo(head_inner, 0.78 if compact else 1.0).pack(side="left", padx=(0, 14))

        title_box = ctk.CTkFrame(head_inner, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_box, text="Vision Agricole", text_color="white", anchor="w",
            font=self._font(18 if compact else 22, True),
        ).pack(anchor="w")

        if not compact:
            ctk.CTkLabel(
                title_box,
                text="Photogrammétrie drone, indices VARI/ExG, topographie & rapport PDF",
                text_color="#CBE4E0", anchor="w", font=self._font(12),
            ).pack(anchor="w")

        badge_header = ctk.CTkLabel(
            head_inner, text="  CATÉGORIE ORANGE  ",
            text_color="white", fg_color=ACCENT_ORANGE,
            corner_radius=8, height=28, font=self._font(11, True),
        )
        badge_header.pack(side="right", padx=(10, 0))

        ctk.CTkFrame(header, fg_color=BRAND_TEAL, height=2, corner_radius=0).pack(fill="x")
        ctk.CTkFrame(header, fg_color=ACCENT_ORANGE, height=3, corner_radius=0).pack(fill="x")

        # ---- Zone du bas : panneau de commande ancré ----
        bottom_wrap = ctk.CTkFrame(
            root, fg_color=CARD_BG, border_width=1,
            border_color=BORDER, corner_radius=12,
        )
        bottom_wrap.pack(side="bottom", fill="x", padx=20, pady=(6, 10) if compact else (8, 16))

        bottom = ctk.CTkFrame(bottom_wrap, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=10 if compact else 14)

        self.launch_btn = ctk.CTkButton(
            bottom, text="Lancer le traitement complet", command=self._on_launch,
            height=40 if compact else 46,
            corner_radius=10, fg_color=BRAND_TEAL, hover_color=BRAND_TEAL_HOVER,
            text_color="white", text_color_disabled="#EEF6F4",
            font=self._font(15, True),
        )
        self.launch_btn.pack(fill="x", pady=(0, 8 if compact else 10))

        progress_row = ctk.CTkFrame(bottom, fg_color="transparent")
        progress_row.pack(fill="x")
        self.progress = ctk.CTkProgressBar(
            progress_row, height=11, corner_radius=6,
            progress_color=BRAND_TEAL, fg_color=SUBTLE_BG,
        )
        self.progress.pack(side="left", fill="x", expand=True)
        self.progress.set(0)

        ctk.CTkLabel(
            progress_row, textvariable=self.percent_text, text_color=BRAND_DARK,
            width=54, anchor="e", font=self._font(13, True),
        ).pack(side="right")

        status_row = ctk.CTkFrame(bottom, fg_color="transparent")
        status_row.pack(fill="x", pady=(6, 0))

        self.status_label = ctk.CTkLabel(
            status_row, textvariable=self.status_text, text_color=TEXT_MUTED,
            anchor="w", justify="left", wraplength=440, font=self._font(12),
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        self.elapsed_label = ctk.CTkLabel(
            status_row, textvariable=self.elapsed_text, text_color=TELEMETRY_BLUE,
            anchor="e", font=self._font(12, True),
        )
        self.elapsed_label.pack(side="right", padx=(8, 0))

        # ---- Onglets principaux ----
        tabs = ctk.CTkTabview(
            root, fg_color=APP_BG, corner_radius=12,
            segmented_button_fg_color=SUBTLE_BG,
            segmented_button_selected_color=BRAND_TEAL,
            segmented_button_selected_hover_color=BRAND_TEAL_HOVER,
            segmented_button_unselected_color=BRAND_DARK,
            segmented_button_unselected_hover_color=BRAND_DARK_ALT,
            text_color="white",
        )
        tabs.pack(fill="both", expand=True, padx=18, pady=(8 if compact else 12, 0))
        self.tabs = tabs

        def scrollable(tab_name):
            tab = tabs.add(tab_name)
            frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
            frame.pack(fill="both", expand=True)
            return frame

        tab_data = scrollable("1. Mission et images")
        tab_engine = scrollable("2. Moteur & SIG")
        tab_preview = scrollable("3. Aperçu des cartes")
        tab_about = scrollable("4. À propos")

        # ====================================================================
        # ONGLET 1 : MISSION ET IMAGES
        # ====================================================================
        b = self._card(
            tab_data, "Données d'entrée & livrables",
            accent_color=BRAND_TEAL,
            subtitle="Sélectionnez le dossier des prises de vue DJI Mavic 3 Enterprise",
        )
        b.columnconfigure(2, minsize=125)

        self._label(b, 0, "Dossier des photos du drone :")
        self._entry(b, 0, self.images_dir, placeholder="Ex : D:\\Missions\\Parcelle_Nord\\DCIM")
        self._secondary_button(b, "Parcourir...", self._choose_images_dir).grid(
            row=0, column=2, padx=(10, 0),
        )

        self.images_badge = ctk.CTkLabel(
            b, textvariable=self.images_count_text,
            text_color=TEXT_MUTED, fg_color=SUBTLE_BG,
            corner_radius=6, height=26, anchor="w", padx=10,
            font=self._font(11, True),
        )
        self.images_badge.grid(row=1, column=1, columnspan=2, sticky="w", pady=(0, 6))

        self._label(b, 2, "Dossier de sortie (PDF & SIG) :")
        self._entry(b, 2, self.output_dir)
        self._secondary_button(b, "Parcourir...", self._choose_output_dir).grid(
            row=2, column=2, padx=(10, 0),
        )

        # ---- Informations de mission ----
        b = self._card(
            tab_data, "Informations de mission",
            accent_color=BRAND_DARK,
            subtitle="Ces informations apparaissent en page de garde du rapport PDF",
        )
        fields = [
            ("Nom de la parcelle :", self.nom_parcelle, "Ex : Parcelle Maïs Sud - Savalou"),
            ("Exploitant / agriculteur :", self.exploitant, "Nom ou coopérative"),
            ("Date du vol (JJ/MM/AAAA) :", self.date_vol, datetime.now().strftime("%d/%m/%Y")),
            ("Altitude de vol (m) :", self.altitude_vol, "Ex : 90"),
            ("Pilote :", self.pilote, "Nom du télépilote"),
            ("Équipe :", self.equipe, ""),
        ]
        for i, (label, var, ph) in enumerate(fields):
            self._label(b, i, label)
            self._entry(b, i, var, placeholder=ph)

        r = len(fields)
        self._label(b, r, "Classes de zonage (VARI) :")
        ctk.CTkSegmentedButton(
            b, values=["2", "3", "4", "5", "6"], variable=self.n_zones, height=33,
            selected_color=BRAND_TEAL, selected_hover_color=BRAND_TEAL_HOVER,
            unselected_color=BRAND_DARK, unselected_hover_color=BRAND_DARK_ALT,
            text_color="white", font=self._font(13, True),
        ).grid(row=r, column=1, sticky="w", pady=6)

        # ---- Sol et cultures (accent orange latérite = terre/agronomie) ----
        b = self._card(
            tab_data, "Sol et orientation culturale (optionnel)",
            accent_color=ACCENT_ORANGE,
            subtitle="Croise la topographie du drone avec les caractéristiques du sol",
        )
        self._hint(
            b, 0,
            "Le capteur RGB du drone ne mesure pas le sol directement. Saisissez "
            "vos résultats d'analyse terrain ci-dessous (prioritaire), ou autorisez "
            "une estimation régionale SoilGrids (~250 m, internet requis).",
            bg_color=ACCENT_ORANGE_SOFT,
        )
        self._label(b, 1, "pH du sol :")
        self._entry(b, 1, self.soil_ph, sticky="w", width=110, placeholder="Ex : 6.2")

        self._label(b, 2, "Texture du sol :")
        ctk.CTkComboBox(
            b, values=list(TEXTURES), variable=self.soil_texture, state="readonly",
            height=35, width=310, corner_radius=8, border_color=FIELD_BORDER,
            fg_color="#FCFBF9", button_color=BRAND_TEAL_SOFT, button_hover_color="#CBECE0",
            dropdown_fg_color="white", text_color=TEXT_PRIMARY, dropdown_text_color=TEXT_PRIMARY,
            font=self._font(13), dropdown_font=self._font(13),
        ).grid(row=2, column=1, sticky="w", pady=6)

        self._label(b, 3, "Note (azote, M.O., observations) :")
        self._entry(b, 3, self.soil_azote_note, placeholder="Ex : Sol légèrement drainant, apport NPK prévu")

        ctk.CTkCheckBox(
            b, text="Estimer via SoilGrids si rien n'est saisi (internet requis)",
            variable=self.allow_soilgrids, onvalue=True, offvalue=False,
            fg_color=ACCENT_ORANGE, hover_color="#C96D1B",
            text_color=TEXT_PRIMARY, font=self._font(13),
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))

        # ====================================================================
        # ONGLET 2 : MOTEUR DE TRAITEMENT & SIG (accent bleu télémétrie)
        # ====================================================================
        b = self._card(
            tab_engine, "Connexion au moteur NodeODM / OpenDroneMap",
            accent_color=TELEMETRY_BLUE,
            subtitle="Moteur photogrammétrique local exécuté via Docker",
        )
        self._hint(
            b, 0,
            "Le traitement photogrammétrique (alignement, nuage de points, "
            "orthomosaïque, MNT) est assuré par NodeODM sur Docker. Par défaut : "
            "localhost:3000 (ou port 3001 pour un nœud WebODM existant).",
            bg_color=TELEMETRY_SOFT,
        )
        self._label(b, 1, "Adresse du moteur (hôte) :")
        self._entry(b, 1, self.node_host)

        self._label(b, 2, "Port :")
        self._entry(b, 2, self.node_port, sticky="w", width=110)

        conn_bar = ctk.CTkFrame(b, fg_color="transparent")
        conn_bar.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        self._secondary_button(
            conn_bar, "Tester la connexion", self._test_connection,
            width=185, accent=TELEMETRY_BLUE,
        ).pack(side="left")

        self.engine_badge = ctk.CTkLabel(
            conn_bar, textvariable=self.engine_status_text,
            text_color=TEXT_MUTED, fg_color=SUBTLE_BG,
            corner_radius=8, height=34, padx=12, font=self._font(12, True),
        )
        self.engine_badge.pack(side="left", padx=(12, 0))

        # ---- Qualité du traitement ----
        b = self._card(
            tab_engine, "Préréglage de qualité photogrammétrique",
            accent_color=BRAND_TEAL,
            subtitle="Adaptez la finesse de reconstruction selon la RAM disponible",
        )
        presets = [
            ("economique", "Économique (recommandé ≤ 8 Go RAM)", "Résolution 2 cm/px, qualité medium — rapide et stable."),
            ("standard", "Standard (16 Go RAM)", "Qualité high — meilleur détail du relief MNT et des bordures."),
            ("maximale", "Maximale (station puissante)", "Qualité ultra — précision maximale, temps de calcul long."),
        ]
        for i, (value, title_p, desc_p) in enumerate(presets):
            row_card = ctk.CTkFrame(
                b, fg_color="#FAF9F5", border_width=1,
                border_color=BORDER, corner_radius=8,
            )
            row_card.grid(row=i, column=0, columnspan=3, sticky="ew", pady=5)
            ctk.CTkRadioButton(
                row_card, text=title_p, value=value, variable=self.quality_level,
                fg_color=BRAND_TEAL, hover_color=BRAND_TEAL_HOVER,
                text_color=BRAND_DARK, font=self._font(13, True),
            ).pack(anchor="w", padx=12, pady=(8, 2))
            ctk.CTkLabel(
                row_card, text=desc_p, text_color=TEXT_MUTED,
                font=self._font(11),
            ).pack(anchor="w", padx=36, pady=(0, 8))

        # ====================================================================
        # ONGLET 3 : APERÇU DES CARTES (visualisation directe des résultats)
        # ====================================================================
        b_prev = self._card(
            tab_preview, "Visualisation interactive des cartes générées",
            accent_color=TELEMETRY_BLUE,
            subtitle="Consultez l'orthomosaïque, la vigueur végétale, le zonage et le relief sans quitter l'application",
        )
        b_prev.columnconfigure(0, weight=1)

        # Barre de sélection de carte + accès rapide dossier / PDF
        toolbar = ctk.CTkFrame(b_prev, fg_color="transparent")
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        self.map_selector = ctk.CTkSegmentedButton(
            toolbar,
            values=["Orthomosaïque", "Vigueur VARI", "Indice ExG", "Zonage", "Relief MNT", "Pentes", "Zones basses"],
            command=self._on_select_map_label,
            height=34,
            selected_color=TELEMETRY_BLUE,
            selected_hover_color="#1759B2",
            unselected_color=SUBTLE_BG,
            unselected_hover_color="#E2DDD2",
            text_color=TEXT_PRIMARY,
            font=self._font(12, True),
        )
        self.map_selector.pack(fill="x", pady=(0, 8))
        self.map_selector.set("Orthomosaïque")

        actions_bar = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions_bar.pack(fill="x")

        self.preview_caption = ctk.CTkLabel(
            actions_bar,
            text="Aucune carte disponible pour le moment — lancez un traitement ou chargez un dossier existant.",
            text_color=TEXT_MUTED, anchor="w", font=self._font(12),
        )
        self.preview_caption.pack(side="left", fill="x", expand=True)

        self._secondary_button(
            actions_bar, "Charger un dossier...", self._load_existing_analyses,
            width=155, accent=BRAND_DARK,
        ).pack(side="right", padx=(8, 0))

        self.open_pdf_btn = self._secondary_button(
            actions_bar, "Ouvrir le PDF", self._open_last_pdf,
            width=125, accent=BRAND_TEAL,
        )
        self.open_pdf_btn.pack(side="right", padx=(8, 0))
        self.open_pdf_btn.configure(state="disabled")

        self.open_folder_btn = self._secondary_button(
            actions_bar, "Dossier livrables", self._open_last_folder,
            width=135, accent=TELEMETRY_BLUE,
        )
        self.open_folder_btn.pack(side="right")
        self.open_folder_btn.configure(state="disabled")

        # Cadre d'affichage de l'image
        self.preview_box = ctk.CTkFrame(
            b_prev, fg_color="#FAF9F5", border_width=1,
            border_color=BORDER, corner_radius=10, height=380,
        )
        self.preview_box.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(4, 6))
        self.preview_box.pack_propagate(False)

        self.preview_image_label = ctk.CTkLabel(
            self.preview_box,
            text="🗺️\n\nLes cartes générées (Orthomosaïque, VARI, ExG, Zonage, MNT)\n"
                 "s'afficheront automatiquement ici à la fin du traitement.\n\n"
                 "Astuce : cliquez sur « Charger un dossier... » pour inspecter\n"
                 "les résultats d'une mission précédente.",
            text_color=TEXT_MUTED, justify="center",
            font=self._font(13),
        )
        self.preview_image_label.pack(expand=True, fill="both", padx=16, pady=16)

        # Bandeau de synthèse rapide sous l'aperçu
        self.preview_stats_label = ctk.CTkLabel(
            b_prev, text="", text_color=BRAND_DARK,
            fg_color=BRAND_TEAL_SOFT, corner_radius=8, height=32,
            anchor="w", padx=12, font=self._font(12, True),
        )

        # ====================================================================
        # ONGLET 4 : À PROPOS / IDENTITÉ DU PROJET
        # ====================================================================
        b = self._card(
            tab_about, "Identité du projet",
            accent_color=ACCENT_ORANGE,
            subtitle="Solution automatisée d'aide à la décision agronomique",
        )
        ctk.CTkLabel(
            b, text="Vision Agricole", text_color=BRAND_DARK, anchor="w",
            font=self._font(20, True),
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        ctk.CTkLabel(
            b, text="Cartographie drone RGB, vigueur végétale (VARI/ExG), zonage & exports QGIS",
            text_color=TEXT_MUTED, anchor="w", font=self._font(12),
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 12))

        badges = ctk.CTkFrame(b, fg_color="transparent")
        badges.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 12))
        for text, color in (
            ("GROUPE 2", BRAND_DARK),
            ("CATÉGORIE ORANGE", ACCENT_ORANGE),
            ("ÉLECTROCHALLENGE 2026", BRAND_TEAL),
        ):
            ctk.CTkLabel(
                badges, text=f"  {text}  ", text_color="white", fg_color=color,
                corner_radius=8, height=30, font=self._font(11, True),
            ).pack(side="left", padx=(0, 8))

        info_rows = [
            ("Organisation :", "Impact Connexion"),
            ("Compétition :", "ÉlectroChallenge 2026"),
            ("Catégorie :", "Orange"),
            ("Mentor référent :", "Renaud DANVI"),
            ("Vecteur aérien :", "DJI Mavic 3 Enterprise (capteur RGB)"),
            ("Livrables SIG :", "GeoTIFF, Shapefile (.shp), AutoCAD (.dxf) & Rapport PDF"),
        ]
        for i, (label, value) in enumerate(info_rows):
            ctk.CTkLabel(
                b, text=label, text_color=BRAND_DARK, anchor="w",
                font=self._font(12, True),
            ).grid(row=3 + i, column=0, sticky="w", pady=4)
            ctk.CTkLabel(
                b, text=value, text_color=TEXT_PRIMARY, anchor="w",
                font=self._font(13),
            ).grid(row=3 + i, column=1, sticky="w", pady=4)

        b = self._card(
            tab_about, "Membres de l'équipe — Groupe 2",
            accent_color=TELEMETRY_BLUE,
        )
        members = [
            ("DEGUE Jordi", "Développement & Pipeline"),
            ("OYENIRAN Djessilatou Awèni", "Analyse & Conception"),
            ("GBAGUIDI Constantino", "Systèmes & Terrain"),
            ("ADIGBLI Serge-Olivier", "Intégration & Validation"),
        ]
        for i, (member, role_hint) in enumerate(members):
            row_m = ctk.CTkFrame(b, fg_color="#FAF9F5", corner_radius=8)
            row_m.grid(row=i, column=0, columnspan=2, sticky="ew", pady=3)
            ctk.CTkLabel(
                row_m, text=f"●  {member}", text_color=BRAND_DARK,
                font=self._font(13, True),
            ).pack(side="left", padx=12, pady=6)
            ctk.CTkLabel(
                row_m, text=role_hint, text_color=TEXT_MUTED,
                font=self._font(11),
            ).pack(side="right", padx=12, pady=6)

    # ------------------------------------------------- aperçu des cartes

    _MAP_LABEL_TO_KEY = {
        "Orthomosaïque": "ortho",
        "Vigueur VARI": "vari",
        "Indice ExG": "exg",
        "Zonage": "zoning",
        "Relief MNT": "hillshade",
        "Pentes": "slope",
        "Zones basses": "low_zones",
    }

    _MAP_DESCRIPTIONS = {
        "ortho": "Orthomosaïque géoréférencée — assemblage haute résolution de la parcelle",
        "vari": "Indice VARI (RGB) — vigueur végétale approximée (rouge = stress, vert = sain)",
        "exg": "Indice ExG (Excess Green) — détection de la biomasse verte",
        "zoning": "Zonage de gestion différenciée — classes homogènes pour modulation des intrants",
        "hillshade": "Modèle Numérique de Terrain (ombrage) — micro-relief de la parcelle",
        "slope": "Carte des pentes (%) — évaluation du ruissellement et du drainage",
        "low_zones": "Zones basses (20 % altitudes les plus faibles) — risque d'accumulation d'eau",
    }

    def _on_select_map_label(self, label: str):
        key = self._MAP_LABEL_TO_KEY.get(label, "ortho")
        self._selected_map_key.set(key)
        self._render_preview_map(key)

    def _render_preview_map(self, key: str):
        path = self._preview_maps.get(key)
        desc = self._MAP_DESCRIPTIONS.get(key, "")
        if not path or not Path(path).exists():
            self._ctk_preview_image = None
            self.preview_image_label.configure(
                image=None,
                text=f"Carte « {key} » non disponible pour cette mission.\n({desc})",
            )
            self.preview_caption.configure(text=desc)
            return

        try:
            with PILImage.open(path) as im:
                im = im.convert("RGB")
                w, h = im.size
                max_w, max_h = 680, 355
                ratio = min(max_w / max(w, 1), max_h / max(h, 1))
                new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
                resized = im.resize(new_size, PILImage.Resampling.LANCZOS)

            ctk_img = ctk.CTkImage(light_image=resized, dark_image=resized, size=new_size)
            self._ctk_preview_image = ctk_img
            self.preview_image_label.configure(image=ctk_img, text="")
            self.preview_caption.configure(text=desc)
        except Exception as exc:
            self._ctk_preview_image = None
            self.preview_image_label.configure(
                image=None,
                text=f"Impossible d'afficher l'aperçu : {exc}",
            )

    def _populate_previews(
        self,
        maps: dict[str, Path | None],
        pdf_path: str | None = None,
        out_dir: str | None = None,
        summary_text: str = "",
        switch_to_tab: bool = True,
    ):
        self._preview_maps = {k: Path(v) for k, v in maps.items() if v is not None and Path(v).exists()}
        self._last_pdf_path = pdf_path if (pdf_path and Path(pdf_path).exists()) else None
        self._last_output_dir = out_dir if (out_dir and Path(out_dir).exists()) else None

        self.open_pdf_btn.configure(state="normal" if self._last_pdf_path else "disabled")
        self.open_folder_btn.configure(state="normal" if self._last_output_dir else "disabled")

        if summary_text:
            self.preview_stats_label.configure(text=summary_text)
            self.preview_stats_label.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        else:
            self.preview_stats_label.grid_forget()

        # Sélectionne la première carte disponible
        preferred_order = ["ortho", "vari", "zoning", "exg", "hillshade", "slope", "low_zones"]
        key_to_label = {v: k for k, v in self._MAP_LABEL_TO_KEY.items()}
        chosen = next((k for k in preferred_order if k in self._preview_maps), "ortho")
        self.map_selector.set(key_to_label.get(chosen, "Orthomosaïque"))
        self._render_preview_map(chosen)

        if switch_to_tab and self._preview_maps:
            try:
                self.tabs.set("3. Aperçu des cartes")
            except Exception:
                pass

    def _load_existing_analyses(self):
        """Permet de charger un dossier de sortie d'une mission passée."""
        d = filedialog.askdirectory(title="Sélectionner un dossier de résultats (ex : rapports_drone)")
        if not d:
            return
        base = Path(d)
        analyses = base / "analyses" if (base / "analyses").is_dir() else base
        maps = {
            "ortho": analyses / "orthomosaique_apercu.png",
            "vari": analyses / "carte_vari.png",
            "exg": analyses / "carte_exg.png",
            "zoning": analyses / "carte_zonage.png",
            "hillshade": analyses / "mnt_ombrage.png",
            "slope": analyses / "carte_pentes.png",
            "low_zones": analyses / "carte_zones_basses.png",
        }
        existing = {k: p for k, p in maps.items() if p.exists()}
        if not existing:
            messagebox.showinfo(
                "Aucune carte trouvée",
                "Aucune image d'analyse PNG n'a été trouvée dans ce dossier.",
            )
            return
        pdf_candidate = base / "rapport_mission_drone.pdf"
        if not pdf_candidate.exists() and base.parent != base:
            pdf_candidate = base.parent / "rapport_mission_drone.pdf"
        out_candidate = pdf_candidate.parent if pdf_candidate.exists() else base
        self._populate_previews(
            existing,
            pdf_path=str(pdf_candidate) if pdf_candidate.exists() else None,
            out_dir=str(out_candidate),
            summary_text=f"Mission chargée : {len(existing)} carte(s) disponible(s) dans {out_candidate.name}",
            switch_to_tab=False,
        )

    def _open_last_pdf(self):
        if self._last_pdf_path and Path(self._last_pdf_path).exists():
            self._open_file(self._last_pdf_path)

    def _open_last_folder(self):
        if self._last_output_dir and Path(self._last_output_dir).exists():
            self._open_file(self._last_output_dir)

    # ------------------------------------------------------------- actions

    def _scan_images(self, folder: str) -> list[str]:
        found = []
        for ext in IMAGE_EXTENSIONS:
            found.extend(glob.glob(os.path.join(folder, ext)))
        return unique_paths(found)

    def _choose_images_dir(self):
        try:
            d = filedialog.askdirectory(title="Choisir le dossier des photos drone")
            if d:
                self.images_dir.set(d)
                imgs = self._scan_images(d)
                if imgs:
                    self.images_count_text.set(f"✓  {len(imgs)} photo(s) drone détectée(s)")
                    self.images_badge.configure(fg_color=BRAND_TEAL_SOFT, text_color=BRAND_TEAL)
                else:
                    self.images_count_text.set("⚠  Aucune image (.jpg/.png) trouvée dans ce dossier")
                    self.images_badge.configure(fg_color=ACCENT_ORANGE_SOFT, text_color=ACCENT_ORANGE)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le sélecteur de dossier :\n{exc}")

    def _choose_output_dir(self):
        try:
            d = filedialog.askdirectory(title="Choisir le dossier de sortie")
            if d:
                self.output_dir.set(d)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le sélecteur de dossier :\n{exc}")

    def _test_connection(self):
        try:
            client = ODMClient(self.node_host.get(), int(self.node_port.get()))
            client.connect()
            self.engine_status_text.set(f"●  Connecté ({self.node_host.get()}:{self.node_port.get()})")
            self.engine_badge.configure(fg_color=BRAND_TEAL_SOFT, text_color=BRAND_TEAL)
            messagebox.showinfo(
                "Connexion réussie",
                "Le moteur de traitement NodeODM répond correctement.",
            )
        except ODMProcessingError as exc:
            self.engine_status_text.set("●  Moteur inaccessible")
            self.engine_badge.configure(fg_color=DANGER_SOFT, text_color=DANGER)
            messagebox.showerror("Connexion impossible", str(exc))
        except Exception as exc:
            self.engine_status_text.set("●  Erreur de configuration")
            self.engine_badge.configure(fg_color=DANGER_SOFT, text_color=DANGER)
            messagebox.showerror("Erreur", str(exc))

    def _set_status(self, text: str, pct: float | None = None):
        try:
            self.status_text.set(text)
            lowered = text.lower()
            if any(word in lowered for word in ("erreur", "échoué", "echoue", "impossible")):
                self.status_label.configure(text_color=DANGER)
            elif any(word in lowered for word in ("terminé", "réussi", "succès")):
                self.status_label.configure(text_color=BRAND_TEAL)
            else:
                self.status_label.configure(text_color=TEXT_MUTED)
            if pct is not None:
                if self._last_pct_value is None or abs(pct - self._last_pct_value) >= 0.05:
                    self._last_pct_value = pct
                    self._last_pct_update_time = time.time()
                self.progress_value.set(pct)
            self.root.update_idletasks()
        except Exception:
            pass

    def _tick(self):
        if not self._is_processing:
            return

        try:
            elapsed = time.time() - self._processing_start_time
            minutes, seconds = divmod(int(elapsed), 60)
            self.elapsed_text.set(f"Temps écoulé : {minutes:d} min {seconds:02d} s")

            stagnant_for = time.time() - self._last_pct_update_time
            if stagnant_for > 6 and not self._progress_indeterminate:
                self.progress.configure(mode="indeterminate")
                self.progress.start()
                self._progress_indeterminate = True
            elif stagnant_for <= 6 and self._progress_indeterminate:
                self.progress.stop()
                self.progress.configure(mode="determinate")
                self._progress_indeterminate = False
                self.progress.set(max(0.0, min(1.0, self.progress_value.get() / 100.0)))

            self.root.after(500, self._tick)
        except Exception:
            self._is_processing = False

    def _start_ticker(self):
        self._is_processing = True
        self._processing_start_time = time.time()
        self._last_pct_value = None
        self._last_pct_update_time = time.time()
        self._progress_indeterminate = False
        self.elapsed_text.set("Temps écoulé : 0 min 00 s")
        self._tick()

    def _stop_ticker(self, final_message: str = ""):
        self._is_processing = False
        try:
            if self._progress_indeterminate:
                self.progress.stop()
                self.progress.configure(mode="determinate")
                self._progress_indeterminate = False
                self.progress.set(max(0.0, min(1.0, self.progress_value.get() / 100.0)))
            if final_message:
                self.elapsed_text.set(final_message)
        except Exception:
            pass

    def _on_launch(self):
        images_dir = self.images_dir.get().strip()
        if not images_dir or not Path(images_dir).is_dir():
            messagebox.showwarning("Dossier manquant", "Choisissez un dossier de photos valide.")
            return

        try:
            image_paths = self._scan_images(images_dir)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Impossible de lire le dossier des photos :\n{exc}")
            return

        if not image_paths:
            messagebox.showwarning("Aucune image", "Aucune photo (.jpg/.png) trouvée dans ce dossier.")
            return

        altitude_text = self.altitude_vol.get().strip()
        if altitude_text:
            try:
                float(altitude_text)
            except ValueError:
                messagebox.showwarning(
                    "Altitude invalide",
                    f"\"{altitude_text}\" n'est pas un nombre valide pour l'altitude de vol.\n"
                    "Utilisez uniquement des chiffres (ex : 90).",
                )
                return

        try:
            int(self.node_port.get())
        except Exception:
            messagebox.showwarning("Port invalide", "Le port du moteur de traitement doit être un nombre entier.")
            return

        try:
            int(self.n_zones.get())
        except Exception:
            messagebox.showwarning("Valeur invalide", "Le nombre de zones de gestion doit être un nombre entier.")
            return

        out_dir = self.output_dir.get().strip() or str(Path.home() / "Documents" / "rapports_drone")
        try:
            Path(out_dir).mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            messagebox.showerror(
                "Dossier de sortie invalide",
                f"Impossible de créer ou d'accéder au dossier de sortie :\n{out_dir}\n\nDétail : {exc}",
            )
            return

        self._set_launch_enabled(False)
        self._start_ticker()
        thread = threading.Thread(target=self._run_pipeline, args=(image_paths, out_dir), daemon=True)
        thread.start()

    # ------------------------------------------------------- pipeline core

    def _run_pipeline(self, image_paths: list[str], out_dir: str):
        try:
            self._set_status(f"{len(image_paths)} photos détectées. Connexion au moteur de traitement...", 2)
            client = ODMClient(self.node_host.get(), int(self.node_port.get()))
            client.connect()

            def progress_cb(step, pct):
                self._set_status(step, pct * 0.65)

            quality_overrides = QUALITY_PRESETS.get(self.quality_level.get(), {})
            result = client.process_images(
                image_paths, os.path.join(out_dir, "odm_output"),
                extra_options=quality_overrides,
                progress_callback=progress_cb,
            )

            if result.orthophoto_path is None:
                raise ODMProcessingError(
                    "Le traitement s'est terminé mais aucune orthomosaïque n'a été "
                    "trouvée dans les résultats. Vérifiez que les photos ont un "
                    "recouvrement suffisant (>= 75%)."
                )

            self._set_status("Calcul des indices de vigueur végétale (VARI/ExG)...", 68)
            veg_result = compute_vegetation_indices(
                str(result.orthophoto_path), os.path.join(out_dir, "analyses"),
                n_zones=int(self.n_zones.get()),
            )

            self._set_status("Génération de l'aperçu orthomosaïque...", 76)
            ortho_preview = make_orthophoto_preview(
                str(result.orthophoto_path), os.path.join(out_dir, "analyses"),
            )

            topo_result = None
            if result.dtm_path is not None:
                self._set_status("Analyse topographique (MNT, pentes, drainage)...", 84)
                topo_result = compute_topography(
                    str(result.dtm_path), os.path.join(out_dir, "analyses"),
                )
            else:
                self._set_status("MNT non disponible dans les résultats, étape ignorée.", 84)

            self._set_status("Organisation des livrables géoréférencés...", 90)
            livrables_dir = os.path.join(out_dir, "livrables")
            os.makedirs(livrables_dir, exist_ok=True)
            _copy_if_exists(result.orthophoto_path, os.path.join(livrables_dir, "orthomosaique.tif"))
            _copy_if_exists(result.dtm_path, os.path.join(livrables_dir, "mnt.tif"))
            _copy_if_exists(result.dsm_path, os.path.join(livrables_dir, "mns.tif"))
            _copy_if_exists(veg_result.vari_tif, os.path.join(livrables_dir, "carte_vari.tif"))
            if result.point_cloud_path is not None:
                pc_name = "nuage_points" + Path(result.point_cloud_path).suffix
                _copy_if_exists(result.point_cloud_path, os.path.join(livrables_dir, pc_name))

            self._set_status("Export des couches pour QGIS (zonage, courbes de niveau)...", 90.5)
            qgis_export = None
            try:
                qgis_export = export_qgis_package(
                    Path(livrables_dir) / "qgis",
                    veg_result.zone_map, veg_result.vari_array,
                    veg_result.zone_transform, veg_result.zone_crs,
                    veg_result.n_zones, zone_palette(veg_result.n_zones or int(self.n_zones.get())),
                    str(result.dtm_path) if result.dtm_path else None,
                )
                for trace in qgis_export.errors:
                    _write_error_log(trace, out_dir)
            except Exception:
                trace = traceback.format_exc()
                _write_error_log(trace, out_dir)
                qgis_export = QgisExportResult(folder=Path(livrables_dir) / "qgis", errors=[trace])

            self._set_status("Calcul de la surface survolée...", 91)
            try:
                surface_ha = compute_surveyed_area_ha(str(result.orthophoto_path))
            except Exception:
                _write_error_log(traceback.format_exc(), out_dir)
                surface_ha = None

            self._set_status("Analyse du sol et des cultures possibles...", 91.5)
            soil = None
            crop_suggestions = None
            try:
                ph_text = self.soil_ph.get().strip()
                ph_value = float(ph_text.replace(",", ".")) if ph_text else None
                soil = soil_data_from_manual(
                    ph_value,
                    "" if self.soil_texture.get() == TEXTURE_NONE else self.soil_texture.get(),
                    self.soil_azote_note.get(),
                )
                if soil is None and self.allow_soilgrids.get():
                    latlon = get_center_latlon(str(result.orthophoto_path))
                    if latlon:
                        soil = fetch_soilgrids_estimate(latlon[0], latlon[1])
                if soil is not None:
                    crop_suggestions = suggest_crops(
                        soil,
                        topo_result.mean_slope_pct if topo_result else None,
                        topo_result.pct_low_zones if topo_result else None,
                    )
            except Exception:
                _write_error_log(traceback.format_exc(), out_dir)
                soil, crop_suggestions = None, None

            self._set_status("Génération du rapport PDF...", 92)
            meta = MissionMetadata(
                nom_parcelle=self.nom_parcelle.get() or "Parcelle non renseignée",
                exploitant=self.exploitant.get(),
                date_vol=self.date_vol.get() or "-",
                altitude_vol_m=float(self.altitude_vol.get()) if self.altitude_vol.get().strip() else None,
                surface_ha=surface_ha,
                nombre_photos=len(image_paths),
                pilote=self.pilote.get(),
                equipe=self.equipe.get(),
            )

            pdf_path = os.path.join(out_dir, "rapport_mission_drone.pdf")
            generate_pdf_report(
                pdf_path,
                meta,
                orthophoto_preview=ortho_preview,
                vari_png=veg_result.vari_png,
                exg_png=veg_result.exg_png,
                zoning_png=veg_result.zoning_png,
                hillshade_png=topo_result.hillshade_png if topo_result else None,
                slope_png=topo_result.slope_png if topo_result else None,
                low_zones_png=topo_result.low_zones_png if topo_result else None,
                veg_stats={
                    "mean_vari": veg_result.mean_vari,
                    "pct_stress_severe": veg_result.pct_stress_severe,
                    "pct_stress_leger": veg_result.pct_stress_leger,
                    "pct_vegetation_saine": veg_result.pct_vegetation_saine,
                    "pct_image_vegetation": veg_result.pct_image_vegetation,
                },
                topo_stats={
                    "min_alt": topo_result.min_alt,
                    "max_alt": topo_result.max_alt,
                    "mean_slope_pct": topo_result.mean_slope_pct,
                    "pct_low_zones": topo_result.pct_low_zones,
                } if topo_result else None,
                soil=soil,
                crop_suggestions=crop_suggestions,
                qgis_export=qgis_export,
                odm_report_pdf=result.report_pdf_path,
            )

            # Mise à jour de l'onglet 3 (Aperçu des cartes) sur le thread UI
            summary_parts = [
                f"Couverture végétale : {veg_result.pct_image_vegetation:.0f} %",
                f"Végétation saine : {veg_result.pct_vegetation_saine:.0f} %",
                f"Stress sévère : {veg_result.pct_stress_severe:.0f} %",
            ]
            if surface_ha is not None:
                summary_parts.insert(0, f"Surface : {surface_ha:.2f} ha")
            summary_line = "   •   ".join(summary_parts)

            preview_payload = {
                "ortho": ortho_preview,
                "vari": veg_result.vari_png,
                "exg": veg_result.exg_png,
                "zoning": veg_result.zoning_png,
                "hillshade": topo_result.hillshade_png if topo_result else None,
                "slope": topo_result.slope_png if topo_result else None,
                "low_zones": topo_result.low_zones_png if topo_result else None,
            }
            self.root.after(
                0,
                lambda: self._populate_previews(
                    preview_payload,
                    pdf_path=pdf_path,
                    out_dir=out_dir,
                    summary_text=summary_line,
                    switch_to_tab=True,
                ),
            )

            self._set_status(f"Terminé ! Rapport généré : {pdf_path}", 100)
            total_elapsed = time.time() - self._processing_start_time
            m, s = divmod(int(total_elapsed), 60)
            self._stop_ticker(f"Terminé en {m} min {s:02d} s")
            self._set_launch_enabled(True)
            messagebox.showinfo(
                "Traitement terminé",
                f"Le rapport PDF a été généré avec succès :\n{pdf_path}",
            )
            self._open_file(pdf_path)

        except ODMProcessingError as exc:
            self._set_status("Erreur pendant le traitement.", 0)
            self._stop_ticker()
            _write_error_log(str(exc), out_dir)
            messagebox.showerror("Erreur de traitement", str(exc))
        except Exception:
            self._set_status("Erreur inattendue pendant le traitement.", 0)
            self._stop_ticker()
            log_path = _write_error_log(traceback.format_exc(), out_dir)
            detail = f"\n\nDétail technique enregistré dans :\n{log_path}" if log_path else ""
            messagebox.showerror(
                "Erreur inattendue",
                "Le traitement n'a pas pu aboutir à cause d'une erreur inattendue. "
                "Vous pouvez ajuster les paramètres et réessayer." + detail,
            )
        finally:
            try:
                self._set_launch_enabled(True)
            except Exception:
                pass

    @staticmethod
    def _open_file(path: str):
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif os.uname().sysname == "Darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception:
            pass


def run_app():
    ctk.set_appearance_mode("light")
    root = ctk.CTk()
    app = DroneReportApp(root)
    root.report_callback_exception = app.handle_tk_exception
    root.mainloop()
