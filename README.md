# Vision Agricole — Cartographie Drone → Rapport PDF

Application de bureau (Python + CustomTkinter) qui transforme un dossier de photos
prises par le DJI Mavic 3 Enterprise en un **rapport PDF complet** en un seul
clic : orthomosaïque, carte de vigueur (VARI/ExG), MNT (topographie/drainage)
et carte de zonage de gestion différenciée.

Elle correspond à l'**Option B (pipeline automatisé)** du dossier technique :
photos → moteur de traitement photogrammétrique (API) → analyse Python
(rasterio/numpy/scikit-learn, sans QGIS) → exports QGIS + rapport PDF.

---

## 1. Architecture

```
Photos drone (JPEG)
        │
        ▼
  NodeODM (moteur de traitement photogrammétrique, dans Docker)
  = le même moteur que celui utilisé en interne par WebODM
        │  (orthomosaïque GeoTIFF + MNT/MNS GeoTIFF)
        ▼
  app/raster_processing.py
  → VARI / ExG (indices RGB, car le M3E n'a pas de capteur multispectral)
  → Zonage de gestion (k-means, 2 à 6 classes)
  → Pentes + ombrage à partir du MNT
        │
        ▼
  app/gis_export.py
  → zonage en GeoTIFF + Shapefile, courbes de niveau en Shapefile + DXF
    (couches prêtes pour QGIS, dans livrables/qgis/)
        │
        ▼
  app/soil_data.py (optionnel)
  → sol saisi manuellement, ou estimé par géolocalisation (SoilGrids/ISRIC)
  → croisé avec la pente/zones basses → cultures indicatives par zone
        │
        ▼
  app/report_generator.py → rapport_mission_drone.pdf
        │
        ▼
  app/gui.py (interface graphique) pilote l'ensemble
```

**Pourquoi NodeODM plutôt que WebODM complet ?** WebODM est une application
web complète (interface web, base de données PostgreSQL, gestion
multi-utilisateurs) qui délègue elle-même le calcul à un ou plusieurs
« nœuds » NodeODM. Pour une application de bureau utilisée par une seule
équipe, faire tourner uniquement le conteneur NodeODM est beaucoup plus léger
à installer (un seul conteneur, pas de base de données) tout en utilisant
**exactement le même moteur photogrammétrique (OpenDroneMap)**. Si l'équipe
préfère malgré tout utiliser une instance WebODM complète déjà installée, il
suffit de pointer l'application vers le nœud NodeODM interne de WebODM
(voir section 4).

---

## 2. Installation

### 2.1 Prérequis

- Python 3.10 ou plus récent
- Docker Desktop (ou Docker Engine sous Linux) — pour le moteur de traitement
- ~8 Go de RAM disponibles pour Docker (le traitement photogrammétrique est
  gourmand en mémoire)

### 2.2 Installer les dépendances Python

```bash
cd drone_report_app
pip install -r requirements.txt
```

### 2.3 Démarrer le moteur de traitement (NodeODM)

Une seule commande, à exécuter une fois Docker installé et démarré :

```bash
docker run -d -p 3000:3000 --name nodeodm opendronemap/nodeodm
```

Vérifier que ça fonctionne en ouvrant http://localhost:3000 dans un
navigateur (une page d'info JSON doit s'afficher).

Pour arrêter le moteur plus tard : `docker stop nodeodm`
Pour le redémarrer : `docker start nodeodm`

### 2.4 Lancer l'application

```bash
python3 main.py
```

---

## 3. Utilisation

1. **Onglet "1. Mission et images"**
   - Choisir le dossier contenant toutes les photos JPEG du vol.
   - Choisir le dossier où seront enregistrés le rapport et les fichiers
     intermédiaires.
   - Renseigner les métadonnées de mission (parcelle, exploitant, date,
     altitude, pilote...).
   - Choisir le nombre de zones de gestion souhaité pour le zonage (4 par
     défaut).

2. **Onglet "2. Moteur de traitement"**
   - Par défaut, l'application se connecte à `localhost:3000` (le conteneur
     Docker lancé à l'étape 2.3).
   - Cliquer sur "Tester la connexion" pour vérifier.

3. Cliquer sur **"Lancer le traitement"**.
   - La barre de progression affiche les étapes : envoi des photos,
     traitement photogrammétrique (le plus long — de quelques minutes à
     plusieurs heures selon le nombre de photos), calcul des indices
     agricoles, génération du PDF.
   - Le rapport `rapport_mission_drone.pdf` s'ouvre automatiquement à la fin
     dans le dossier de sortie choisi.

---

## 4. Utiliser une instance WebODM complète existante (optionnel)

Si l'équipe a déjà une instance WebODM installée (via `docker-compose` du
projet officiel WebODM), le nœud NodeODM interne est généralement exposé sur
le port **3001** de la machine hôte. Il suffit alors de renseigner, dans
l'onglet "2. Moteur de traitement" :
- Adresse : `localhost`
- Port : `3001`

(Vérifier le port exact avec `docker ps` — le conteneur s'appelle
généralement `webodm_node-odm_1`.)

---

## 5. Structure du projet

```
drone_report_app/
├── main.py                     # point d'entrée de l'application
├── requirements.txt
├── app/
│   ├── odm_client.py            # communication avec le moteur NodeODM (pyodm)
│   ├── raster_processing.py     # VARI/ExG, zonage k-means, pentes/ombrage MNT
│   ├── gis_export.py            # exports QGIS : zonage (GeoTIFF/SHP), courbes de niveau (SHP/DXF)
│   ├── soil_data.py             # sol (saisie manuelle ou repli SoilGrids) + suggestion de cultures
│   ├── report_generator.py      # assemblage du PDF (reportlab)
│   └── gui.py                   # interface graphique (CustomTkinter)
└── tests/
    └── make_synthetic_data.py   # génère de fausses données pour tester
                                  # le pipeline sans vraies photos drone
```

---

## 6. Créer une version portable (.exe) pour les autres PC de l'équipe

Pour éviter d'installer Python sur chaque PC, vous pouvez générer un
exécutable Windows autonome (`.exe`) une seule fois, puis le copier sur les
autres postes.

**Important :** ceci empaquette uniquement l'application (interface +
analyse + PDF). Docker et le moteur NodeODM doivent rester installés
séparément sur le PC qui fait réellement le traitement des photos (voir
section 2.3) — un `.exe` ne peut pas contenir un moteur de virtualisation.
En pratique, une seule personne de l'équipe a besoin de Docker ; les autres
peuvent simplement recevoir le PDF final.

### Étapes (à faire une seule fois, sur le PC qui a déjà Python installé)

**Si votre dossier `drone_report_app` se trouve dans OneDrive, Google Drive ou un
dossier synchronisé** : la synchronisation en arrière-plan peut verrouiller des
fichiers pendant que PyInstaller les écrit, provoquant des échecs difficiles à
diagnostiquer. Il est recommandé de mettre la synchronisation en pause le temps
de la construction (clic droit sur l'icône OneDrive dans la barre des tâches →
"Suspendre la synchronisation"), ou de copier temporairement le dossier hors de
OneDrive (par exemple dans `C:\Dev\drone_report_app`) pour la construction.

1. Ouvrez l'Invite de commandes dans le dossier `drone_report_app`.
2. Lancez :
   ```bash
   build_exe.bat
   ```
3. Patientez (plusieurs minutes) — le script installe PyInstaller puis
   construit l'exécutable.
4. Une fois terminé, `dist\Vision Agricole.exe` est un **fichier unique et
   autonome** : tout le code de l'application (dossier `app\`) est intégré
   à l'intérieur, il n'y a plus de dossier `_internal` ni de fichiers `.py`
   à côté de l'exe.

### Distribuer l'application

Copiez uniquement `Vision Agricole.exe` — sur une clé USB, un dossier
partagé, peu importe. Aucun autre fichier ne l'accompagne. Double-clic pour
lancer l'application sur n'importe quel PC Windows, sans installer Python.

Le premier lancement sur chaque poste est un peu plus lent que les suivants :
le fichier se décompresse dans un dossier temporaire à chaque démarrage
(propriété du mode `--onefile`).

### Appliquer un correctif

Contrepartie du fichier unique : il n'y a plus de dossier `app\` externe à
côté de l'exe où remplacer un fichier `.py` pour corriger un bug sans tout
reconstruire. Tout correctif, même mineur, demande de relancer
`build_exe.bat` en entier puis de redistribuer le nouveau
`Vision Agricole.exe`.

---

## 6 bis. Version Mac (non testée sur Mac réel)

Le code est le même sur Windows et sur Mac (Python, CustomTkinter). Seule la
construction diffère, et **elle doit se faire sur un Mac** :

1. Installez Python 3 depuis python.org (il inclut un Tkinter récent).
2. Dans le Terminal, dans le dossier du projet :
   ```bash
   chmod +x build_mac.sh
   ./build_mac.sh
   ```
3. Résultat : `dist/Vision Agricole.app`. Sur Mac, une app graphique est
   toujours un dossier présenté comme une seule icône : le fichier unique
   de Windows n'existe pas ici.
4. Premier lancement : clic droit > Ouvrir (app non signée). Pour une copie
   reçue par e-mail ou téléchargée : `xattr -dr com.apple.quarantine
   "Vision Agricole.app"`.

Points d'attention :
- **Docker Desktop pour Mac** est nécessaire, comme sous Windows. Réglez sa
  mémoire dans Réglages > Resources (4 à 5 Go sur un Mac de 8 Go).
- **Mac Apple Silicon (M1, M2, M3...)** : l'image NodeODM peut tourner en
  émulation (`--platform linux/amd64`), donc nettement plus lentement. À
  tester avant de compter dessus.
- Cette version Mac n'a été vérifiée qu'en lecture du code : aucun test sur
  un vrai Mac n'a eu lieu.

---

## 6 ter. Utiliser les résultats dans QGIS

Chaque traitement dépose dans `livrables/` des GeoTIFF géoréférencés
(`orthomosaique.tif`, `mnt.tif`, `carte_vari.tif`) et, dans `livrables/qgis/` :

| Fichier | Contenu |
|---|---|
| `zonage_gestion.tif` | zonage en GeoTIFF, couleurs intégrées |
| `zonage_gestion.shp` | zones de gestion en polygones (champs ZONE, LIBELLE, SURF_HA, PCT_SURF, PCT_BRUT, VARI_MOY) |
| `courbes_niveau.shp` / `.dxf` | courbes de niveau du MNT (échelon choisi automatiquement, courbes maîtresses tous les 5 échelons) |
| `LISEZMOI_QGIS.txt` | système de coordonnées, mode d'emploi, points à noter |

Dans QGIS : glisser les fichiers dans la fenêtre ; ils se superposent sans réglage
(même système de coordonnées). Pour colorier le zonage vectoriel : Symbologie >
Catégorisé > valeur `ZONE`.

À savoir :
- Le zonage exporté est **lissé** (filtre de majorité sur ~0,6 m, puis fusion des
  fragments de moins de 5 m²) : il est plus net que l'image du rapport. `PCT_BRUT`
  donne la part de chaque zone avant lissage ; le programme avertit si le lissage
  la modifie fortement.
- Vérifié par relecture avec GDAL (le moteur de lecture de QGIS), pas encore
  ouvert dans QGIS lui-même.
- Dans le rapport PDF, les livrables « Plan topographique » et « Carte de zonage »
  ne passent à « Fourni » que si ces fichiers ont réellement été produits.

---

## 7. Limites connues et points à valider avec le mentor

- **VARI/ExG et non NDVI** : approximation RGB uniquement, cohérente avec
  l'absence de capteur multispectral sur le M3E (voir cahier des charges,
  section 3.2).
- **Altitude de vol** : le point de vigilance réglementaire soulevé dans la
  proposition technique (plafond possible de 91,5 m selon l'ANAC-Bénin,
  contre 100-120 m prévus dans les paramètres de mission FP1) reste à
  confirmer par le mentor — l'application ne bloque pas les altitudes
  saisies, elle les rapporte simplement dans le PDF.
- **Qualité du traitement** : les options par défaut (`pc-quality: medium`,
  `feature-quality: medium`) offrent un bon compromis vitesse/précision sur un
  PC aux ressources limitées (8 Go de RAM) ; elles sont modifiables dans
  `app/odm_client.py` (`DEFAULT_OPTIONS`) si un PC plus puissant est
  disponible pour la compétition.
- **Tester sans photos réelles** : `python3 tests/make_synthetic_data.py tests/data`
  génère une fausse orthomosaïque et un faux MNT pour vérifier que les
  modules d'analyse et le PDF fonctionnent avant même d'avoir des vraies
  données de vol.
