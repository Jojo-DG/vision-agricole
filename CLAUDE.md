# Vision Agricole – site vitrine

## Contexte
Application Windows de cartographie agricole par drone, créée par le Groupe 2 – Impact Connexion
(ÉlectroChallenge 2026, Catégorie Orange, mentor Renaud DANVI). Dépôt : Jojo-DG/vision-agricole. Licence MIT.
Le groupe a remporté la Catégorie Orange le 19 août 2026 ; Jaime DEGUE a été meilleur participant de la catégorie.
L'équipe continue de faire évoluer l'application et de la promouvoir.

## Objectif du site
UN SITE PRODUIT : présenter et faire télécharger l'application, comme une mise en avant de produit
(promesse, bénéfices, preuves, appel à l'action). Ce n'est PAS un site sur le groupe Impact Connexion.
La marque est « Vision Agricole ». Le groupe n'apparaît qu'en signature discrète, dans une courte section
« Notre histoire » et dans la section « L'équipe ».
Public : agriculteurs d'abord, puis techniciens, jury et partenaires.

## À lire avant de commencer
- `site/argumentaire.md` : la structure et les textes du site, orientés produit. C'est la référence.
- `site/contenu.md` : matière première (équipe, rôles, histoire détaillée). À condenser, jamais à copier en bloc.
- `site/medias/` : captures de la vraie application, photos de l'équipe.

## Règles
- Tout le texte est en français, chaleureux, concret, phrases courtes. Le bénéfice avant la technique.
- Accueil : accroche, bénéfices, 3 étapes, captures, réassurance, téléchargement. L'histoire y tient en 5 à 8 lignes.
- Ne rien inventer : pas de chiffres, de précision ou de durée non fournis. Sources autorisées : `site/argumentaire.md`, `site/contenu.md`, le README et le rapport du projet (`main (1).pdf`, chiffres du vol test à présenter comme tels). Les textes « À COMPLÉTER » restent signalés.
- Site en React + TypeScript + Vite + Tailwind CSS, dans `site/` (voir `site/DEVELOPPEMENT.md`), compilé et publié sur Vercel (dossier racine du projet Vercel : `site`, réglages dans `site/vercel.json`). Il suit la maquette Figma Make.
- Lisible sur téléphone, léger, sans bibliothèque ni ressource externe sans nécessité (polices auto-hébergées, aucun CDN, aucun suivi).
- Animations sobres (CSS et `IntersectionObserver`), coupées avec `prefers-reduced-motion`.
- Charte : pétrole #0B4F5C, vert #0B7D5C, orange #DF7E26 ; logo `assets/logo_vision_agricole.svg`.
- Icônes en SVG (style Feather Icons, MIT), jamais d'emojis.
- Les photos de l'équipe sont publiques avec l'accord des membres.
- Ne jamais toucher à `app/`, aux scripts de build ni à la Release.
- Travailler sur une branche, jamais directement sur `main`.

## Téléchargement
Lien : https://github.com/Jojo-DG/vision-agricole/releases/download/v1.1.0/Vision.Agricole.exe
SHA-256 : ecf9f03b36ac40f7828d46675f0bd0000a16663846c9f8efcf3a6da1eadc9c0e
Licences : MIT (application) ; NodeODM/ODM AGPL-3.0 ; Feather Icons MIT.
