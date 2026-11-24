import { GITHUB, MAC } from '../data'
import { CodeBlock } from './Copy'

/** Premier lancement de l'application Mac (non signée par Apple). */
export function MacFirstLaunch() {
  return (
    <>
      <ol className="plain-steps mac-steps">
        <li>Décompressez <span className="mono">{MAC.file}</span> (double-clic sur le fichier).</li>
        <li>Glissez <b>Vision Agricole</b> dans le dossier <b>Applications</b>.</li>
        <li>Au premier lancement : clic droit sur l’application, puis <b>Ouvrir</b>, puis <b>Ouvrir</b> dans la fenêtre qui s’affiche.</li>
      </ol>
      <p><b>Si macOS bloque l’ouverture</b>, ouvrez le Terminal, collez cette commande, puis relancez l’application :</p>
      <CodeBlock code={MAC.quarantineCmd} label="autoriser l’ouverture de Vision Agricole sur macOS" />
    </>
  )
}

/** Solution de repli : construire l'application soi-même à partir du code source. */
export function MacBuildFromSource({ engineNote = true }: { engineNote?: boolean }) {
  return (
    <>
      <p>Vous pouvez aussi construire l’application vous-même, sur votre Mac :</p>
      <ol className="plain-steps mac-steps">
        <li>Installez <b>Python 3.12</b> (depuis python.org) et <b>Docker Desktop</b>.</li>
        <li>Téléchargez le code : bouton <b>« Download ZIP »</b> sur la <a href={GITHUB} rel="noopener">page du projet</a>.</li>
        <li>Dans le Terminal, dans le dossier du projet : <span className="mono">chmod +x build_mac.sh</span> puis <span className="mono">./build_mac.sh</span>.</li>
        <li>Glissez <span className="mono">dist/Vision Agricole.app</span> dans Applications.</li>
        <li>Au premier lancement : clic droit, puis <b>Ouvrir</b>.</li>
        {engineNote && <li>Démarrez le moteur de traitement (voir plus haut) avec la commande <span className="mono">{MAC.engineCmd}</span>.</li>}
      </ol>
    </>
  )
}
