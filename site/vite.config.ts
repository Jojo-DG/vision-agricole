import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Chemins relatifs (base './') : le site fonctionne à la racine d'un domaine
// comme dans un sous-dossier (GitHub Pages). La navigation utilise le hash (#/histoire).
export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
  build: { target: 'es2020', assetsInlineLimit: 0 },
})
