# Vision Agricole – site vitrine

## Contexte
Application Windows de cartographie agricole par drone (Groupe 2 – Impact Connexion,
ÉlectroChallenge 2026, Catégorie Orange, mentor Renaud DANVI). Dépôt : Jojo-DG/vision-agricole. Licence MIT.
Le Groupe 2 a remporté l'ÉlectroChallenge 2026 ; l'équipe promeut maintenant l'application.

## Objectif du site
Présenter l'application, l'équipe et l'histoire du projet, et proposer le téléchargement.
Public : agriculteurs d'abord, puis techniciens, jury et partenaires.

## Contenus fournis
Tout est dans `site/contenu.md` (équipe, rôles, histoire à compléter) et `site/medias/`
(captures de la vraie application, photos de l'équipe, capture de la version 0.0.0).
Les textes marqués « À COMPLÉTER » restent visibles comme tels : ne pas inventer de faits.

## Règles
- Tout le texte est en français, ton simple et chaleureux, sans jargon.
- Site statique (HTML/CSS/JS sans framework ni build), dans `site/`, publiable via GitHub Pages.
- Lisible sur téléphone. Léger. Pas de bibliothèque externe sans nécessité.
- Charte : pétrole #0B4F5C, vert #0B7D5C, orange #DF7E26 ; logo dans `assets/logo_vision_agricole.svg`.
- Icônes en SVG (Feather Icons, MIT), jamais d'emojis.
- Ne jamais toucher à `app/`, aux scripts de build ni à la Release.
- Travailler sur une branche, jamais directement sur `main`.

## Sections
Accueil, Comment ça marche (3 étapes : photos, parcelle, rapport), Captures, Équipe, Notre histoire,
Télécharger (lien Release v1.1.0, prérequis Docker/NodeODM, alerte SmartScreen,
SHA-256 ecf9f03b36ac40f7828d46675f0bd0000a16663846c9f8efcf3a6da1eadc9c0e),
Licence et crédits (MIT ; NodeODM/ODM AGPL-3.0 ; Feather Icons MIT).
Lien de téléchargement : https://github.com/Jojo-DG/vision-agricole/releases/download/v1.1.0/Vision.Agricole.exe
