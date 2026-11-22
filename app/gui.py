"""
gui.py

Interface graphique de bureau (CustomTkinter : un habillage moderne de Tkinter,
embarqué dans l'exécutable, rien à installer sur les postes de l'équipe).

Flux d'utilisation :
  1. L'utilisateur choisit le dossier contenant les photos du drone.
  2. Il renseigne les métadonnées de la mission (parcelle, altitude, etc.).
  3. Il clique sur "Lancer le traitement".
  4. L'application envoie les photos au moteur NodeODM, suit la progression,
     calcule les indices agricoles, puis génère directement le PDF final.
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

# Palette identique a celle du rapport PDF (report_generator.py), pour une
# identité visuelle cohérente entre l'application et son livrable.
BRAND_DARK = "#0B4F5C"
BRAND_TEAL = "#0F9D74"
BRAND_BLUE = "#1E6FD9"
BRAND_LIGHT = "#EAF6F2"
BRAND_BG = "#FFFFFF"
DANGER = "#D64545"
TEXT_MUTED = "#5F5E5A"
CARD_BG = "#FFFFFF"
BORDER = "#D3E0DD"
FIELD_BORDER = "#AFC4BF"
BRAND_TEAL_HOVER = "#0C8460"
ACCENT_ORANGE = "#E2903A"   # rappel de la « Catégorie Orange »

# Libellé de la liste « texture du sol » quand rien n'est renseigné.
TEXTURE_NONE = "Non renseignée"
TEXTURES = (TEXTURE_NONE, "Sableux", "Limoneux", "Argileux", "Limono-argilo-sableux (mixte)")

# Preréglages de qualité selectionnables dans l'onglet "2. Moteur de
# traitement" (voir _build_ui). "economique" correspond aux valeurs par
# defaut d'ODMClient.DEFAULT_OPTIONS (machine a ressources limitees) ; les
# deux autres les surchargent via extra_options lors de l'appel a
# process_images. Niveaux ODM valides : ultra > high > medium > low > lowest.
QUALITY_PRESETS = {
    "economique": {},  # garde les valeurs par defaut d'ODMClient (medium/medium)
    "standard": {"pc-quality": "high", "feature-quality": "high"},
    "maximale": {"pc-quality": "ultra", "feature-quality": "ultra"},
}


def _write_error_log(exc_text: str, out_dir: str | None) -> str:
    """Enregistre le détail technique d'une erreur dans un fichier log,
    plutôt que de l'afficher brut a l'écran. Retourne le chemin du fichier
    (ou une chaîne vide si même la journalisation a échoue - dans ce cas on
    ne doit surtout pas lever d'exception supplémentaire)."""
    try:
        base = Path(out_dir) if out_dir else Path.home() / "Documents" / "rapports_drone"
        logs_dir = base / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = logs_dir / f"erreur_{stamp}.log"
        log_path.write_text(exc_text, encoding="utf-8")
        return str(log_path)
    except Exception:
        # La journalisation elle-même ne doit jamais faire planter l'appli
        return ""


def _copy_if_exists(src, dst):
    """Copie src vers dst si src existe et n'est pas None ; ignore sinon
    (par exemple le DSM n'est pas toujours généré selon les options).
    Ne leve jamais d'exception : un problème de copie (disque plein,
    permissions...) ne doit pas interrompre tout le traitement pour un
    fichier secondaire."""
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
        self.root.title("Vision Agricole - Agriculture de précision")
        self.root.configure(fg_color=BRAND_BG)
        # Taille adaptée à l'écran réel. CustomTkinter multiplie la largeur et
        # la hauteur de la fenêtre par le facteur d'échelle Windows (125 %,
        # 150 %...), mais pas la taille d'écran lue par Tkinter : on raisonne
        # donc en pixels réels, puis on convertit en unités logiques.
        try:
            self._scale = float(self.root._get_window_scaling())
        except Exception:
            self._scale = 1.0
        scale = self._scale
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        phys_w = max(560 * scale, min(780 * scale, screen_w - 40))
        phys_h = max(380 * scale, min(900 * scale, screen_h - 100))
        win_w = int(phys_w / scale)
        win_h = int(phys_h / scale)
        pos_x = max(0, int((screen_w - win_w * scale) // 2))
        pos_y = max(0, int((screen_h - win_h * scale) // 2 - 20))
        self.root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.root.minsize(560, 380)
        # Écran court (portable 768 px à 150 %...) : en-tête et bas de fenêtre
        # réduits pour laisser de la place au formulaire.
        self._compact = win_h < 560

        self.images_dir = StringVar()
        self.output_dir = StringVar(value=str(Path.home() / "Documents" / "rapports_drone"))
        self.node_host = StringVar(value="localhost")
        self.node_port = IntVar(value=3000)

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

        self.status_text = StringVar(value="Prêt.")
        self.elapsed_text = StringVar(value="")
        self.progress_value = DoubleVar(value=0)
        self.percent_text = StringVar(value="")
        self.progress_value.trace_add("write", self._update_percent)

        # Suivi pour rendre la barre de progression "vivante" même quand le
        # moteur de traitement ne remonte pas de pourcentage fréquemment
        self._is_processing = False
        self._processing_start_time = 0.0
        self._last_pct_value = None
        self._last_pct_update_time = 0.0
        self._progress_indeterminate = False

        self._build_ui()

    # ------------------------------------------------------ filet de sécurité

    def handle_tk_exception(self, exc_type, exc_value, exc_tb):
        """Appelé automatiquement par Tkinter pour TOUTE exception non gérée
        survenant dans un callback (clic de bouton, minuteur, etc.), ou
        qu'elle vienne. Sans ce filet, Tkinter se contente par défaut
        d'imprimer l'erreur sur une console qui n'existe pas dans la version
        .exe (fenêtre 'windowed'), ce qui peut donner l'impression que
        l'application est gelée ou plantée. Ici, on journalise le détail
        technique et on affiche un message clair, sans jamais interrompre
        l'application."""
        try:
            exc_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        except Exception:
            exc_text = f"{exc_type}: {exc_value}"

        log_path = _write_error_log(exc_text, self.output_dir.get() if hasattr(self, "output_dir") else None)

        try:
            launch_btn = getattr(self, "launch_btn", None)
            if launch_btn is not None:
                self._set_launch_enabled(True)
        except Exception:
            pass

        detail = f"\n\nDetail technique enregistre dans :\n{log_path}" if log_path else ""
        try:
            messagebox.showerror(
                "Erreur inattendue",
                "Une erreur inattendue s'est produite, mais l'application reste "
                "ouverte et utilisable." + detail,
            )
        except Exception:
            pass  # même l'affichage de l'erreur ne doit jamais faire planter l'appli

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
        """Active ou désactive le bouton principal. CustomTkinter ne grise pas
        le fond d'un bouton désactivé : on change donc aussi sa couleur."""
        try:
            self.launch_btn.configure(
                state="normal" if enabled else "disabled",
                fg_color=BRAND_TEAL if enabled else "#9FB9B5",
            )
        except Exception:
            pass

    def _card(self, parent, title: str):
        """Carte blanche aux coins arrondis avec un titre. Renvoie la zone
        (grille à 2 colonnes : libellé / champ) où ajouter les widgets."""
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, border_width=1,
                            border_color=BORDER, corner_radius=12)
        card.pack(fill="x", pady=(0, 14), padx=2)
        ctk.CTkLabel(card, text=title, text_color=BRAND_DARK, anchor="w",
                     font=self._font(14, True)).pack(anchor="w", padx=18, pady=(14, 6))
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 16))
        body.columnconfigure(0, minsize=200)
        body.columnconfigure(1, weight=1)
        return body

    def _label(self, body, row: int, text: str):
        ctk.CTkLabel(body, text=text, anchor="w", font=self._font(13)).grid(
            row=row, column=0, sticky="w", pady=6, padx=(0, 14))

    def _hint(self, body, row: int, text: str):
        ctk.CTkLabel(body, text=text, text_color=TEXT_MUTED, anchor="w", justify="left",
                     wraplength=480, font=self._font(12)).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 8))

    def _entry(self, body, row: int, var, sticky: str = "ew", width: int = 140):
        kwargs = {} if sticky == "ew" else {"width": width}
        entry = ctk.CTkEntry(body, textvariable=var, height=34, corner_radius=8,
                             border_color=FIELD_BORDER, fg_color="white",
                             text_color="#1F2A2E", font=self._font(13), **kwargs)
        entry.grid(row=row, column=1, sticky=sticky, pady=6)
        return entry

    def _secondary_button(self, parent, text: str, command, width: int = 110):
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=34,
                             corner_radius=8, fg_color="white", text_color=BRAND_DARK,
                             border_width=1, border_color="#B5CBC6", hover_color=BRAND_LIGHT,
                             font=self._font(12))

    def _draw_logo(self, parent, factor: float = 1.0):
        k = self._scale * factor
        size = int(48 * k)
        logo = Canvas(parent, width=size, height=size, bg=BRAND_DARK, highlightthickness=0)

        def pts(*coords):
            return [c * k for c in coords]

        logo.create_oval(*pts(2, 2, 46, 46), fill=BRAND_TEAL, outline="")
        logo.create_polygon(*pts(13, 35, 11, 22, 20, 12, 34, 11, 36, 25, 28, 35),
                            smooth=True, fill="white", outline="")
        logo.create_line(*pts(15, 33, 31, 16), fill=BRAND_TEAL, width=max(2, int(2 * k)))
        return logo

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        root = self.root
        compact = self._compact

        # ---- En-tête : logo + nom + filet orange (Catégorie Orange) ----
        header = ctk.CTkFrame(root, fg_color=BRAND_DARK, corner_radius=0)
        header.pack(fill="x")
        head_inner = ctk.CTkFrame(header, fg_color="transparent")
        head_inner.pack(fill="x", padx=24, pady=8 if compact else 16)
        self._draw_logo(head_inner, 0.75 if compact else 1.0).pack(side="left", padx=(0, 14))
        title_box = ctk.CTkFrame(head_inner, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(title_box, text="Vision Agricole", text_color="white", anchor="w",
                     font=self._font(18 if compact else 22, True)).pack(anchor="w")
        if not compact:
            ctk.CTkLabel(title_box, text="Cartographie aérienne par drone  →  rapport PDF en un clic",
                         text_color="#CFE8E2", anchor="w", font=self._font(12)).pack(anchor="w")
        ctk.CTkFrame(header, fg_color=ACCENT_ORANGE, height=3, corner_radius=0).pack(fill="x")

        # ---- Zone du bas (bouton + progression), empaquetée EN PREMIER côté
        # bas : elle reste toujours visible, même si la fenêtre est petite ----
        bottom = ctk.CTkFrame(root, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=24, pady=(4, 8) if compact else (6, 18))

        self.launch_btn = ctk.CTkButton(
            bottom, text="Lancer le traitement", command=self._on_launch,
            height=38 if compact else 48,
            corner_radius=10, fg_color=BRAND_TEAL, hover_color=BRAND_TEAL_HOVER,
            text_color_disabled="#EEF6F4", font=self._font(15, True))
        self.launch_btn.pack(fill="x", pady=(0, 6 if compact else 12))

        progress_row = ctk.CTkFrame(bottom, fg_color="transparent")
        progress_row.pack(fill="x")
        self.progress = ctk.CTkProgressBar(progress_row, height=12, corner_radius=6,
                                           progress_color=BRAND_TEAL, fg_color="#E3EEEB")
        self.progress.pack(side="left", fill="x", expand=True)
        self.progress.set(0)
        ctk.CTkLabel(progress_row, textvariable=self.percent_text, text_color=BRAND_DARK,
                     width=56, anchor="e", font=self._font(13, True)).pack(side="right")

        self.status_label = ctk.CTkLabel(
            bottom, textvariable=self.status_text, text_color=TEXT_MUTED, anchor="w",
            justify="left", wraplength=520, font=self._font(12))
        self.status_label.pack(fill="x", pady=(4 if compact else 8, 0))
        self.elapsed_label = ctk.CTkLabel(
            bottom, textvariable=self.elapsed_text, text_color=BRAND_TEAL, anchor="w",
            font=self._font(12, True))
        self.elapsed_label.pack(fill="x")

        # ---- Onglets ----
        tabs = ctk.CTkTabview(
            root, fg_color=BRAND_BG, corner_radius=12,
            segmented_button_fg_color="#E3EEEB",
            segmented_button_selected_color=BRAND_TEAL,
            segmented_button_selected_hover_color=BRAND_TEAL_HOVER,
            segmented_button_unselected_color=BRAND_DARK,
            segmented_button_unselected_hover_color="#116372",
            text_color="white")
        tabs.pack(fill="both", expand=True, padx=18, pady=(8 if compact else 14, 0))
        self.tabs = tabs

        def scrollable(tab_name):
            tab = tabs.add(tab_name)
            frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
            frame.pack(fill="both", expand=True)
            return frame

        tab_data = scrollable("1. Mission et images")
        tab_engine = scrollable("2. Moteur de traitement")
        tab_about = scrollable("3. À propos")

        # ---- Onglet 1 : fichiers ----
        b = self._card(tab_data, "Fichiers")
        b.columnconfigure(2, minsize=120)
        self._label(b, 0, "Dossier des photos du drone :")
        self._entry(b, 0, self.images_dir)
        self._secondary_button(b, "Parcourir...", self._choose_images_dir).grid(
            row=0, column=2, padx=(10, 0))
        self._label(b, 1, "Dossier de sortie (rapport) :")
        self._entry(b, 1, self.output_dir)
        self._secondary_button(b, "Parcourir...", self._choose_output_dir).grid(
            row=1, column=2, padx=(10, 0))

        # ---- Onglet 1 : informations de mission ----
        b = self._card(tab_data, "Informations de mission")
        fields = [
            ("Nom de la parcelle :", self.nom_parcelle),
            ("Exploitant / agriculteur :", self.exploitant),
            ("Date du vol (JJ/MM/AAAA) :", self.date_vol),
            ("Altitude de vol (m) :", self.altitude_vol),
            ("Pilote :", self.pilote),
            ("Équipe :", self.equipe),
        ]
        for i, (label, var) in enumerate(fields):
            self._label(b, i, label)
            self._entry(b, i, var)
        r = len(fields)
        self._label(b, r, "Nombre de zones de gestion :")
        ctk.CTkSegmentedButton(
            b, values=["2", "3", "4", "5", "6"], variable=self.n_zones, height=32,
            selected_color=BRAND_TEAL, selected_hover_color=BRAND_TEAL_HOVER,
            unselected_color=BRAND_DARK, unselected_hover_color="#116372",
            text_color="white", font=self._font(13)).grid(row=r, column=1, sticky="w", pady=6)

        # ---- Onglet 1 : sol et cultures (optionnel) ----
        b = self._card(tab_data, "Sol et cultures possibles (optionnel)")
        self._hint(b, 0, (
            "Le drone ne mesure pas le sol. Si vous avez un résultat d'analyse (même "
            "partiel), saisissez-le ci-dessous : c'est la source la plus fiable. Sinon, "
            "l'application peut tenter une estimation régionale par géolocalisation "
            "(SoilGrids) - internet requis, résolution ~250m, non mesurée sur site."))
        self._label(b, 1, "pH du sol :")
        self._entry(b, 1, self.soil_ph, sticky="w", width=110)
        self._label(b, 2, "Texture du sol :")
        ctk.CTkComboBox(
            b, values=list(TEXTURES), variable=self.soil_texture, state="readonly",
            height=34, width=300, corner_radius=8, border_color=FIELD_BORDER,
            fg_color="white", button_color=BRAND_LIGHT, button_hover_color="#D3E6E1",
            dropdown_fg_color="white", text_color="#1F2A2E", dropdown_text_color="#1F2A2E",
            font=self._font(13), dropdown_font=self._font(13)).grid(
            row=2, column=1, sticky="w", pady=6)
        self._label(b, 3, "Note (azote, matière organique...) :")
        self._entry(b, 3, self.soil_azote_note)
        ctk.CTkCheckBox(
            b, text="Estimer via SoilGrids si rien n'est saisi (internet requis)",
            variable=self.allow_soilgrids, onvalue=True, offvalue=False,
            fg_color=BRAND_TEAL, hover_color=BRAND_TEAL_HOVER,
            font=self._font(13)).grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))

        # ---- Onglet 2 : moteur de traitement ----
        b = self._card(tab_engine, "Le moteur de traitement")
        self._hint(b, 0, (
            "Le traitement photogrammétrique (alignement des photos, orthomosaïque, "
            "MNT) est réalisé par le moteur NodeODM/OpenDroneMap, le même moteur "
            "que celui utilisé par WebODM.\n\n"
            "Ce moteur doit tourner localement via Docker. Voir README.md pour "
            "l'installation complète (une seule commande)."))

        b = self._card(tab_engine, "Qualité du traitement")
        self._hint(b, 0, (
            "À ajuster selon la machine qui fait tourner le moteur NodeODM. "
            "Un niveau plus élevé prend plus de temps et de mémoire, pour une "
            "précision un peu meilleure."))
        for i, (value, label) in enumerate([
            ("economique", "Économique — PC modeste (8 Go RAM ou moins)"),
            ("standard", "Standard — PC courant (16 Go RAM)"),
            ("maximale", "Maximale — PC puissant, priorité à la précision"),
        ]):
            ctk.CTkRadioButton(
                b, text=label, value=value, variable=self.quality_level,
                fg_color=BRAND_TEAL, hover_color=BRAND_TEAL_HOVER,
                font=self._font(13)).grid(row=i + 1, column=0, columnspan=3, sticky="w", pady=6)

        b = self._card(tab_engine, "Connexion")
        self._label(b, 0, "Adresse du moteur (hôte) :")
        self._entry(b, 0, self.node_host)
        self._label(b, 1, "Port :")
        self._entry(b, 1, self.node_port, sticky="w", width=110)
        self._secondary_button(b, "Tester la connexion", self._test_connection, width=180).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # ---- Onglet 3 : à propos / identité du projet ----
        b = self._card(tab_about, "Identité du projet")
        ctk.CTkLabel(b, text="Vision Agricole", text_color=BRAND_DARK, anchor="w",
                     font=self._font(20, True)).grid(row=0, column=0, columnspan=2, sticky="w")
        ctk.CTkLabel(b, text="Agriculture de précision par drone et analyse automatisée",
                     text_color=TEXT_MUTED, anchor="w", font=self._font(12)).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

        badges = ctk.CTkFrame(b, fg_color="transparent")
        badges.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))
        for text, color in (("GROUPE 2", BRAND_DARK), ("CATÉGORIE ORANGE", ACCENT_ORANGE),
                            ("ÉLECTROCHALLENGE 2026", BRAND_TEAL)):
            ctk.CTkLabel(badges, text=f"  {text}  ", text_color="white", fg_color=color,
                         corner_radius=8, height=30, font=self._font(12, True)).pack(
                side="left", padx=(0, 8))

        info_rows = [
            ("Organisation :", "Impact Connexion"),
            ("Compétition :", "ÉlectroChallenge 2026"),
            ("Catégorie :", "Orange"),
            ("Mentor référent :", "Renaud DANVI"),
            ("Matériel :", "DJI Mavic 3 Enterprise (capteur RGB)"),
        ]
        for i, (label, value) in enumerate(info_rows):
            ctk.CTkLabel(b, text=label, text_color=BRAND_DARK, anchor="w",
                         font=self._font(12, True)).grid(row=3 + i, column=0, sticky="w", pady=3)
            ctk.CTkLabel(b, text=value, anchor="w", font=self._font(13)).grid(
                row=3 + i, column=1, sticky="w", pady=3)

        b = self._card(tab_about, "Membres de l'équipe")
        for i, member in enumerate([
            "DEGUE Jordi", "OYENIRAN Djessilatou Awèni",
            "GBAGUIDI Constantino", "ADIGBLI Serge-Olivier",
        ]):
            ctk.CTkLabel(b, text="•  " + member, anchor="w", font=self._font(13)).grid(
                row=i, column=0, columnspan=2, sticky="w", pady=2)

    # ------------------------------------------------------------- actions

    def _choose_images_dir(self):
        try:
            d = filedialog.askdirectory(title="Choisir le dossier des photos drone")
            if d:
                self.images_dir.set(d)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le selecteur de dossier :\n{exc}")

    def _choose_output_dir(self):
        try:
            d = filedialog.askdirectory(title="Choisir le dossier de sortie")
            if d:
                self.output_dir.set(d)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le selecteur de dossier :\n{exc}")

    def _test_connection(self):
        try:
            client = ODMClient(self.node_host.get(), int(self.node_port.get()))
            client.connect()
            messagebox.showinfo("Connexion réussie",
                                 "Le moteur de traitement répond correctement.")
        except ODMProcessingError as exc:
            messagebox.showerror("Connexion impossible", str(exc))
        except Exception as exc:  # port invalide, etc.
            messagebox.showerror("Erreur", str(exc))

    def _set_status(self, text: str, pct: float | None = None):
        try:
            self.status_text.set(text)
            lowered = text.lower()
            if any(word in lowered for word in ("erreur", "échoue", "impossible")):
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
            # La fenêtre a probablement été fermée : on ignore silencieusement,
            # le thread de traitement continuera puis se terminera normalement.
            pass

    def _tick(self):
        """Boucle appelée toutes les 500ms pendant le traitement, pour que
        l'interface reste visiblement vivante même quand le moteur ne
        remonte pas de nouveau pourcentage pendant un long moment."""
        if not self._is_processing:
            return

        try:
            elapsed = time.time() - self._processing_start_time
            minutes, seconds = divmod(int(elapsed), 60)
            self.elapsed_text.set(f"Temps écoulé : {minutes:d} min {seconds:02d} s")

            stagnant_for = time.time() - self._last_pct_update_time
            if stagnant_for > 6 and not self._progress_indeterminate:
                # aucune vraie progression recue depuis plus de 6s -> on bascule
                # sur une animation continue pour montrer que ça travaille toujours
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
            # La fenêtre a probablement été fermee pendant le traitement :
            # on arrête simplement le minuteur, sans remonter d'erreur.
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
            image_paths = []
            for ext in IMAGE_EXTENSIONS:
                image_paths.extend(glob.glob(os.path.join(images_dir, ext)))
            # Windows ignore la casse des extensions : "*.jpg" et "*.JPG"
            # retrouvent les mêmes fichiers, qui seraient comptés et envoyés
            # deux fois au moteur. On dédoublonne donc la liste.
            image_paths = unique_paths(image_paths)
        except Exception as exc:
            messagebox.showerror("Erreur", f"Impossible de lire le dossier des photos :\n{exc}")
            return

        if not image_paths:
            messagebox.showwarning("Aucune image", "Aucune photo (.jpg/.png) trouvée dans ce dossier.")
            return

        # Validation préalable des champs numériques, pour éviter une erreur
        # au milieu du traitement a cause d'une simple faute de frappe.
        altitude_text = self.altitude_vol.get().strip()
        if altitude_text:
            try:
                float(altitude_text)
            except ValueError:
                messagebox.showwarning(
                    "Altitude invalide",
                    f"\"{altitude_text}\" n'est pas un nombre valide pour l'altitude de vol.\n"
                    "Utilisez uniquement des chiffres (ex: 100).")
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
                f"Impossible de créer ou d'accéder au dossier de sortie :\n{out_dir}\n\nDetail : {exc}")
            return

        self._set_launch_enabled(False)
        self._start_ticker()
        thread = threading.Thread(target=self._run_pipeline, args=(image_paths, out_dir), daemon=True)
        thread.start()

    # ------------------------------------------------------- pipeline core

    def _run_pipeline(self, image_paths: list[str], out_dir: str):
        try:
            self._set_status(f"{len(image_paths)} photos detectees. Connexion au moteur de traitement...", 2)
            client = ODMClient(self.node_host.get(), int(self.node_port.get()))
            client.connect()

            def progress_cb(step, pct):
                self._set_status(step, pct * 0.65)  # traitement ODM = 0 a 65% de la barre globale

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
                str(result.orthophoto_path), os.path.join(out_dir, "analyses"))

            topo_result = None
            if result.dtm_path is not None:
                self._set_status("Analyse topographique (MNT, pentes, drainage)...", 84)
                topo_result = compute_topography(
                    str(result.dtm_path), os.path.join(out_dir, "analyses"))
            else:
                self._set_status("MNT non disponible dans les résultats, étape ignorée.", 84)

            # Regroupe les livrables GeoTIFF dans un dossier clair et unique,
            # au lieu de les laisser enfouis dans odm_output\extracted\...
            # (cahier des charges, section 4.5 : livrables geo-références
            # exploitables par l'agriculteur / dans un SIG comme QGIS)
            self._set_status("Organisation des livrables geo-références...", 90)
            livrables_dir = os.path.join(out_dir, "livrables")
            os.makedirs(livrables_dir, exist_ok=True)
            _copy_if_exists(result.orthophoto_path, os.path.join(livrables_dir, "orthomosaique.tif"))
            _copy_if_exists(result.dtm_path, os.path.join(livrables_dir, "mnt.tif"))
            _copy_if_exists(result.dsm_path, os.path.join(livrables_dir, "mns.tif"))
            _copy_if_exists(veg_result.vari_tif, os.path.join(livrables_dir, "carte_vari.tif"))
            if result.point_cloud_path is not None:
                pc_name = "nuage_points" + Path(result.point_cloud_path).suffix
                _copy_if_exists(result.point_cloud_path, os.path.join(livrables_dir, pc_name))

            # Couches prêtes pour QGIS : zonage (GeoTIFF + SHP) et courbes de
            # niveau (SHP + DXF). Un échec ici ne doit jamais interrompre le
            # traitement : les erreurs sont journalisées, le rapport signale
            # simplement le livrable comme partiel.
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
                # Calcul secondaire : un échec ne doit pas interrompre le
                # traitement, mais on journalise désormais la vraie cause
                # (auparavant avalée silencieusement dans la fonction elle-même).
                _write_error_log(traceback.format_exc(), out_dir)
                surface_ha = None

            # Sol et cultures possibles (optionnel) : priorité a la saisie
            # manuelle ; repli SoilGrids uniquement si autorise ET rien saisi.
            # Aucun échec ici ne doit interrompre le traitement principal.
            self._set_status("Analyse du sol et des cultures possibles...", 91.5)
            soil = None
            crop_suggestions = None
            try:
                ph_text = self.soil_ph.get().strip()
                ph_value = float(ph_text.replace(",", ".")) if ph_text else None
                soil = soil_data_from_manual(
                    ph_value,
                    "" if self.soil_texture.get() == TEXTURE_NONE else self.soil_texture.get(),
                    self.soil_azote_note.get())
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


            self._set_status(f"Terminé ! Rapport généré : {pdf_path}", 100)
            total_elapsed = time.time() - self._processing_start_time
            m, s = divmod(int(total_elapsed), 60)
            self._stop_ticker(f"Traitement terminé en {m} min {s:02d} s.")
            # Bouton réactivé AVANT la boîte de dialogue et l'ouverture du PDF :
            # si l'un des deux traîne, l'utilisateur peut déjà relancer.
            self._set_launch_enabled(True)
            messagebox.showinfo("Traitement terminé",
                                 f"Le rapport PDF a été généré avec succès :\n{pdf_path}")
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
            detail = f"\n\nDetail technique enregistre dans :\n{log_path}" if log_path else ""
            messagebox.showerror(
                "Erreur inattendue",
                "Le traitement n'a pas pu aboutir a cause d'une erreur inattendue. "
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
            pass  # ouverture automatique optionnelle, pas bloquant


def run_app():
    ctk.set_appearance_mode("light")   # indépendant du mode sombre de Windows
    root = ctk.CTk()
    app = DroneReportApp(root)
    # Filet de sécurité global : intercepte toute exception non gérée dans
    # n'importe quel callback Tkinter (clic, minuteur, etc.) pour que
    # l'application ne se fige ni ne plante jamais silencieusement.
    root.report_callback_exception = app.handle_tk_exception
    root.mainloop()
