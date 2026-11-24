# Site vitrine : développement

Site en **React + TypeScript + Vite + Tailwind CSS**, dans ce dossier (`site/`).
Il est compilé puis publié sur GitHub Pages par `.github/workflows/pages.yml`.

## Lancer le site en local

```bash
cd site
npm install
npm run dev      # aperçu avec rechargement automatique
npm run build    # vérification des types + compilation dans site/dist
npm run preview  # sert le site compilé
```

Node 22 ou plus récent est recommandé.

## Où modifier quoi

| Je veux changer… | Fichier |
|---|---|
| Un texte, la FAQ, l'équipe, la frise, les liens de téléchargement | `src/data.ts` (et `src/pages/*.tsx` pour les textes longs) |
| Les couleurs, les polices, les animations | `src/index.css` (variables en haut du fichier) |
| Une image | `public/medias/` (captures, équipe, cartes du vol test) |
| L'en-tête, le pied de page | `src/components/Chrome.tsx` |
| Le comparateur avant/après, la galerie | `src/components/Interactive.tsx` |

`argumentaire.md` et `contenu.md` sont les textes de référence du projet (ils ne sont pas publiés).

## Choix de conception

- **Navigation par hash** : `#/histoire` et `#/techniciens` sont des pages, `#resultats`… sont des sections de l'accueil. Aucune configuration serveur n'est nécessaire sur GitHub Pages.
- **Aucune ressource externe** : les polices (Fraunces, Plus Jakarta Sans, DM Mono) sont dans `src/fonts/`, sans Google Fonts, sans suivi.
- **Animations** : `Reveal` (apparition au défilement) et `Counter` (chiffres qui défilent) dans `src/components/ui.tsx`, en CSS et `IntersectionObserver`, sans bibliothèque. Elles sont coupées si le visiteur a demandé « réduire les animations » (`prefers-reduced-motion`).
- **Images du comparateur** : `public/medias/resultats/comparaison-*.webp` sont deux vues du même vol test, découpées sur la même emprise.
