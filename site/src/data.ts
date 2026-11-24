// Contenu du site : liens, textes et données.
// Source des textes : site/argumentaire.md, site/contenu.md, README.md et le rapport du projet (vol test).

export const GITHUB = 'https://github.com/Jojo-DG/vision-agricole'

export const LINKS = {
  download: `${GITHUB}/releases/download/v1.1.0/Vision.Agricole.exe`,
  sha256: 'ecf9f03b36ac40f7828d46675f0bd0000a16663846c9f8efcf3a6da1eadc9c0e',
  virustotal:
    'https://www.virustotal.com/gui/file/ecf9f03b36ac40f7828d46675f0bd0000a16663846c9f8efcf3a6da1eadc9c0e',
  github: GITHUB,
  readme: `${GITHUB}#readme`,
  issues: `${GITHUB}/issues`,
  license: `${GITHUB}/blob/main/LICENSE`,
} as const

export const media = (name: string) => `medias/${name}`

/** Captures de la vraie application (version 1.1.0). */
export const shots = {
  home: { src: media('captures/01-accueil.jpg'), w: 1400, h: 762 },
  photos: { src: media('captures/02-choix-photos.jpg'), w: 1400, h: 762 },
  settings: { src: media('captures/03-reglages.jpg'), w: 1400, h: 762 },
  exports: { src: media('captures/04-reglages-exports.jpg'), w: 1400, h: 763 },
  engine: { src: media('captures/05-moteur-a-demarrer.jpg'), w: 1400, h: 762 },
  about: { src: media('captures/06-a-propos.jpg'), w: 1400, h: 762 },
  first: { src: media('captures/00-version-0.0.0-streamlit.jpg'), w: 1400, h: 640 },
  testResults: { src: media('captures/07-apercu-resultats-donnees-test.jpg'), w: 1280, h: 800 },
} as const

/** Cartes réelles produites sur le vol test décrit dans le rapport du projet (118 photos). */
export const maps = {
  ortho: { src: media('resultats/orthomosaique.jpg'), w: 1000, h: 1167 },
  vari: { src: media('resultats/vigueur-vari.jpg'), w: 900, h: 668 },
  zoning: { src: media('resultats/zonage.jpg'), w: 900, h: 718 },
  relief: { src: media('resultats/relief-mnt.jpg'), w: 900, h: 737 },
  slopes: { src: media('resultats/pentes.jpg'), w: 748, h: 756 },
  lowZones: { src: media('resultats/zones-basses.jpg'), w: 610, h: 730 },
  beforePhotos: media('resultats/comparaison-photos.webp'),
  afterZoning: media('resultats/comparaison-zonage.webp'),
} as const

/** Chiffres mesurés sur le vol test (rapport du projet, section 4.8). Ils ne valent que pour ce vol. */
export const testFlight = [
  { value: 118, decimals: 0, unit: 'photos', label: 'Photos alignées', detail: '118 sur 118, soit 100 %' },
  { value: 1.8, decimals: 1, unit: 'cm / pixel', label: 'Résolution au sol', detail: 'Seuil visé : moins de 5 cm' },
  { value: 2.17, decimals: 2, unit: 'ha', label: 'Surface cartographiée', detail: 'Parcelle du vol test' },
  { value: 28, decimals: 0, unit: 'min', extra: { value: 34, unit: 's' }, label: 'Temps de traitement', detail: 'Pour ces 118 photos' },
] as const

export const steps = [
  { n: '01', title: 'Choisissez vos photos', text: 'Indiquez le dossier du vol de votre drone.' },
  { n: '02', title: 'Décrivez votre parcelle', text: 'Quelques informations utiles : parcelle, exploitant, date.' },
  { n: '03', title: 'Recevez votre rapport', text: 'Consultez et partagez le PDF.' },
] as const

export const benefits = [
  { icon: 'map', title: 'Une carte de santé de vos cultures', text: 'Les zones vigoureuses et les zones faibles, d’un coup d’œil.' },
  { icon: 'grid', title: 'Un zonage de la parcelle', text: 'Où agir en priorité, où tout va bien.' },
  { icon: 'drop', title: 'Pentes et zones basses', text: 'Repérez l’eau qui stagne ou qui ruisselle.' },
  { icon: 'check', title: 'Un verdict en mots simples', text: 'La santé globale de la parcelle, sans jargon.' },
  { icon: 'file', title: 'Un rapport PDF en français', text: 'Prêt à imprimer ou à partager.' },
  { icon: 'settings', title: 'Des fichiers pour les techniciens', text: 'Zonage et courbes de niveau pour QGIS et la DAO, ajoutés automatiquement.' },
] as const

export const gallery = [
  { shot: shots.photos, caption: 'Étape 1 : choisissez le dossier des photos de votre drone.', alt: 'Étape 1 de l’application : choisir le dossier des photos du drone, formats acceptés JPG et PNG.' },
  { shot: shots.engine, caption: 'Moteur pas encore démarré ? L’application vous guide en trois étapes.', alt: 'Écran d’aide qui explique, en trois étapes, comment démarrer le moteur de traitement dans Docker Desktop.' },
  { shot: shots.exports, caption: 'Les fichiers pour QGIS et la DAO sont créés automatiquement, sans réglage.', alt: 'Réglages avancés : la section Exports SIG explique que le zonage et les courbes de niveau sont produits automatiquement.' },
  { shot: shots.settings, caption: 'Réglages pour le technicien. La qualité « Rapide » est recommandée sur 8 Go.', alt: 'Réglages avancés : moteur de traitement, dossier de sortie du rapport et qualité par défaut « Rapide (recommandé sur 8 Go) ».' },
  { shot: shots.about, caption: 'À propos : version 1.1.0, licence MIT.', alt: 'Écran À propos : logo de Vision Agricole, version 1.1.0, licence MIT et technologies utilisées.' },
] as const

export const why = [
  { n: '01', title: 'Simple et guidé, en 3 étapes', text: 'Un parcours pensé pour l’agriculteur et son technicien.' },
  { n: '02', title: '100 % en français', text: 'Les écrans, les explications et le rapport PDF.' },
  { n: '03', title: 'Vos photos restent sur votre ordinateur', text: 'Le traitement se fait chez vous. Vos photos ne sont pas envoyées sur Internet.' },
  { n: '04', title: 'Gratuit et libre, licence MIT', text: 'Le code est public sur GitHub.' },
  { n: '05', title: 'Pour les drones courants', text: 'Testé avec un DJI Mavic 3 Enterprise (photos RGB).' },
] as const

export const team = [
  { photo: media('equipe/degue-jaime-jordi.jpg'), w: 487, h: 680, name: 'Jaime Jordi DEGUE', role: 'Chef d’équipe', detail: 'Meilleur participant de l’ÉlectroChallenge 2026.' },
  { photo: media('equipe/gbaguidi-constantino.jpg'), w: 512, h: 680, name: 'Constantino GBAGUIDI', role: 'Adjoint au chef d’équipe', detail: 'Auteur de la version 0.0.0.' },
  { photo: media('equipe/adigbli-serge-olivier.jpg'), w: 499, h: 680, name: 'Serge-Olivier ADIGBLI', role: 'Technique', detail: 'Gestion des dépendances.' },
  { photo: media('equipe/oyeniran-aweni.jpg'), w: 509, h: 680, name: 'Awèni OYENIRAN', role: 'Valorisation', detail: 'Marketing.' },
] as const

export const faqs = [
  { q: 'Quel drone faut-il ?', a: ['Des photos aériennes JPG ou PNG de bonne qualité, avec un recouvrement entre les images. L’application a été testée avec un DJI Mavic 3 Enterprise (photos RGB).'] },
  { q: 'Faut-il Internet ?', a: ['Pas pour le traitement. Il faut Internet la première fois, pour télécharger Docker et le moteur de traitement.', 'L’estimation du sol en ligne (SoilGrids), qui est facultative, utilise aussi Internet.'] },
  { q: 'Mes photos sont-elles envoyées quelque part ?', a: ['Non. Tout reste sur votre ordinateur.'] },
  { q: 'Combien de temps dure un traitement ?', a: ['Cela dépend du nombre de photos et de la puissance de votre PC. L’application affiche la progression et le temps écoulé. Ne la fermez pas et ne mettez pas le PC en veille pendant le traitement.'] },
  { q: 'C’est payant ?', a: ['Non. Vision Agricole est gratuit et libre, sous licence MIT.'] },
  { q: 'Où trouver de l’aide ?', a: ['Le README explique l’installation pas à pas. Pour poser une question, ouvrez une demande dans les Issues du dépôt GitHub.'] },
] as const

/** Frise de « Notre histoire » (site/contenu.md). */
export const timeline = [
  { date: 'Mi-juillet', title: 'Candidatures et sélection', text: 'Candidatures individuelles, puis test de sélection. Constitution des équipes et premiers échanges avec le mentor, Renaud DANVI.' },
  { date: '2 août', title: 'Début des phases préparatoires', text: 'Le Groupe 2 – Impact Connexion, Catégorie Orange, se met en route.' },
  { date: '13 août', title: 'Le vrai travail commence', text: 'Première cartographie sur un vrai terrain et début du développement de l’application. Séance jusqu’à 22 h.' },
  { date: 'Même semaine', title: 'Un ordinateur assez puissant', text: 'Trouver une machine capable du traitement photogrammétrique n’est pas simple : l’équipe rentre très tard.' },
  { date: 'Samedi', title: 'Derniers réglages', text: 'Derniers réglages de l’application et début du PowerPoint, avec de vrais débats.' },
  { date: 'Lundi 17 août', title: 'Début de la finale', text: 'Le soir, le diaporama prend forme.' },
  { date: 'Mardi', title: 'Les répétitions', text: 'Fin du PowerPoint et premières répétitions : chacun voit ses points faibles et travaille dessus.' },
  { date: 'Mercredi 19 août', title: 'Pitch devant le jury', text: 'Victoire en Catégorie Orange. Jaime reçoit le titre de meilleur participant de la catégorie.', award: true },
  { date: 'Depuis', title: 'L’aventure continue', text: 'Version 1.1.0 de Vision Agricole et projets en cours avec l’application.' },
] as const

/** Sorties de l'application (README, section « Utiliser les résultats dans QGIS »). */
export const outputs = [
  { name: 'Rapport', format: 'PDF', use: 'Synthèse en français, prête à imprimer ou à partager.' },
  { name: 'Orthomosaïque, relief, vigueur', format: 'GeoTIFF', use: 'Cartes géoréférencées (orthomosaique.tif, mnt.tif, carte_vari.tif).' },
  { name: 'Zonage', format: 'GeoTIFF / Shapefile', use: 'Zones de gestion, avec surface et part de chaque zone.' },
  { name: 'Courbes de niveau', format: 'Shapefile / DXF', use: 'Pour QGIS et les logiciels de DAO.' },
  { name: 'Mode d’emploi', format: 'Texte', use: 'LISEZMOI_QGIS.txt : système de coordonnées et points à noter.' },
] as const

export const limits = [
  'VARI et ExG sont des approximations calculées sur des images RGB. Ce ne sont pas des NDVI : le DJI Mavic 3 Enterprise n’a pas de capteur multispectral.',
  'Le zonage exporté est lissé : il est plus net que l’image du rapport. Le champ PCT_BRUT donne la part de chaque zone avant lissage.',
  'Les exports ont été vérifiés par relecture avec GDAL, le moteur de lecture de QGIS. Ils n’ont pas encore été ouverts dans QGIS lui-même.',
  'L’altitude de vol n’est pas bloquée par l’application : elle est simplement reportée dans le PDF.',
  'La version Mac n’a pas été testée sur un vrai Mac.',
  'Les suggestions de cultures et les interprétations du rapport sont des aides à la décision. Elles ne remplacent pas l’avis d’un agronome ni une analyse de sol.',
] as const
