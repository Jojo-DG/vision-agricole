# Argumentaire – Vision Agricole (le site est un site PRODUIT)

Le site présente **l'application**, comme une mise en avant de produit. Nom de marque : **Vision Agricole**
(signature discrète : « Groupe 2 – Impact Connexion »). L'histoire et l'équipe sont deux sections courtes, pas le cœur du site.

## Promesse (accroche d'accueil)
- Titre : **De vos photos de drone à un rapport clair pour votre parcelle.**
- Sous-titre : Transformer les images du ciel en décisions simples pour le terrain.
- Boutons : **Télécharger pour Windows** · Voir comment ça marche
- Preuve juste dessous : Lauréat de l'ÉlectroChallenge 2026, Catégorie Orange.

## Le problème, en deux phrases
Une parcelle vue du sol cache l'essentiel : où les plantes souffrent, où l'eau stagne, où intervenir en premier.
Un drone voit tout, mais ses photos brutes ne disent rien à un agriculteur.

## Comment ça marche (3 étapes, ton direct)
1. **Choisissez vos photos** : indiquez le dossier du vol de votre drone.
2. **Décrivez votre parcelle** : quelques informations utiles (parcelle, exploitant, date).
3. **Recevez votre rapport** : consultez et partagez le PDF.

## Ce que vous obtenez (bénéfices, pas technique)
- **Une carte de santé de vos cultures** : les zones vigoureuses et les zones faibles, d'un coup d'œil.
- **Un zonage de la parcelle** : où agir en priorité, où tout va bien.
- **Pentes et zones basses** : repérer l'eau qui stagne ou qui ruisselle.
- **Un verdict en mots simples** pour la santé globale de la parcelle.
- **Un rapport PDF en français**, prêt à imprimer ou à partager.
- **Des fichiers pour les techniciens** (QGIS, DAO) : zonage, courbes de niveau, ajoutés automatiquement.

## Pourquoi Vision Agricole (arguments de réassurance)
- **Simple et guidé** : un parcours en 3 étapes, pensé pour l'agriculteur et son technicien.
- **100 % en français.**
- **Vos photos restent sur votre ordinateur** : traitement local, rien n'est envoyé sur Internet.
- **Gratuit et libre** (licence MIT) ; le code est public sur GitHub.
- **Conçu au Bénin**, lauréat de l'ÉlectroChallenge 2026 (Catégorie Orange).
- Pensé pour les photos de drones courants (testé avec un DJI Mavic 3 Enterprise, photos RGB).

## Section « Télécharger » (clair et rassurant)
- Bouton principal : Vision Agricole 1.1.0 pour Windows (lien Release v1.1.0).
- Prérequis, en 3 lignes : Windows ; Docker Desktop + le moteur de traitement (NodeODM), expliqués pas à pas dans le README ; PC de 8 Go : choisir la qualité « Rapide ».
- Encadré « Windows affiche un avertissement ? » : c'est normal pour un nouveau logiciel non signé. Cliquer sur « Informations complémentaires » puis « Exécuter quand même ». Empreinte SHA-256 et analyse VirusTotal fournies pour vérifier.
- Onglet « Mac » à côté de « Windows » (même section, et page Installation) : bouton « Télécharger pour Mac » (Release v1.1.0, `Vision-Agricole-1.1.0-Mac.zip`).
  Compatibilité : Mac à puce Apple Silicon (M1, M2, M3…) ; pas de version Intel pour l'instant.
  Empreinte SHA-256 avec bouton « Copier », commande de vérification `shasum -a 256 "Vision-Agricole-1.1.0-Mac.zip"` et lien VirusTotal.
  Premier lancement : décompresser, glisser dans Applications, clic droit > Ouvrir > Ouvrir ; si macOS bloque : `xattr -dr com.apple.quarantine "/Applications/Vision Agricole.app"`.
  Rappel : Docker Desktop et le moteur NodeODM restent nécessaires ; commande `docker run -d -p 3000:3000 --platform linux/amd64 --name nodeodm opendronemap/nodeodm`. Sur Apple Silicon le moteur tourne en émulation, donc plus lentement.
  Repli, dans un bloc repliable « Je préfère construire moi-même » : 1) installer Python 3.12 (python.org) et Docker Desktop ; 2) télécharger le code (bouton « Download ZIP » sur GitHub) ; 3) dans le Terminal : `chmod +x build_mac.sh` puis `./build_mac.sh` ; 4) glisser `dist/Vision Agricole.app` dans Applications ; 5) premier lancement : clic droit > Ouvrir ; 6) démarrer le moteur (commande ci-dessus).

## FAQ (4 à 6 questions)
- Quel drone faut-il ? Des photos aériennes JPG/PNG de bonne qualité, avec recouvrement.
- Faut-il Internet ? Non pour le traitement ; oui pour télécharger Docker et le moteur la première fois.
- Mes photos sont-elles envoyées quelque part ? Non, tout reste sur votre ordinateur.
- Combien de temps dure un traitement ? Dépend du nombre de photos et du PC (ne pas promettre de durée précise).
- C'est payant ? Non, licence MIT.
- Où trouver de l'aide ? Le dépôt GitHub (Issues) et le README.

## Preuve sociale / histoire (COURT, 5 à 8 lignes sur l'accueil + page dédiée « Notre histoire »)
Accroche : « Né en quelques jours, validé devant un jury. »
Contenu : voir `contenu.md`. Sur l'accueil, seulement : ÉlectroChallenge 2026, Catégorie Orange, lauréat, meilleur participant (Jaime), mentor Renaud DANVI, le projet continue avec des projets réels.

## L'équipe (cartes simples : photo, nom, rôle ; pas de long texte)
Voir `contenu.md`.

## Ton à tenir
Chaleureux, concret, phrases courtes, verbes d'action. Le bénéfice avant la technique.
Pas de jargon (photogrammétrie, k-means, VARI) sur l'accueil : si nécessaire, une page « Pour les techniciens ».
Ne rien promettre qui n'a pas été testé (précision, rendement, durée). Pas d'invention de chiffres.
