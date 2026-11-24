import { Button, Icon, Reveal, Topography } from '../components/ui'
import { LINKS, limits, outputs, shots } from '../data'

const columns = ['Sortie', 'Format', 'Usage'] as const

export default function Technical() {
  return (
    <main className="inner-page" id="contenu">
      <section className="inner-hero">
        <Topography />
        <div className="container">
          <a href="#/" className="back-link"><Icon name="arrow" size={16} /> Retour à l’accueil</a>
          <span className="section-kicker light"><i />Pour les techniciens</span>
          <h1>Du traitement brut <br />aux <em>exports métiers.</em></h1>
          <p>Le fonctionnement de Vision Agricole, des photos du drone jusqu’aux livrables. Le détail complet est dans le README du dépôt.</p>
        </div>
      </section>

      <section className="section tech-section" aria-labelledby="t-flux">
        <div className="container">
          <Reveal className="flow" role="list" aria-label="Étapes du traitement">
            <div role="listitem"><Icon name="photo" /><b>Photos</b><small>JPG ou PNG, photos RGB</small></div>
            <Icon name="arrow" />
            <div role="listitem"><Icon name="settings" /><b>NodeODM</b><small>Traitement local, sous Docker</small></div>
            <Icon name="arrow" />
            <div role="listitem"><Icon name="map" /><b>Cartes</b><small>VARI / ExG, zonage, relief</small></div>
            <Icon name="arrow" />
            <div role="listitem"><Icon name="file" /><b>Livrables</b><small>PDF · QGIS · DAO</small></div>
          </Reveal>

          <Reveal className="tech-copy">
            <span className="section-kicker"><i />Interopérable</span>
            <h2 id="t-flux">Des sorties prêtes à intégrer <em>votre flux.</em></h2>
            <p>Vision Agricole s’appuie sur un moteur de photogrammétrie local (NodeODM, le moteur d’OpenDroneMap). L’orthomosaïque et le modèle de terrain en sortent, puis l’application calcule les indices de végétation, le zonage de gestion (2 à 6 zones), les pentes et les courbes de niveau.</p>
          </Reveal>

          <Reveal className="output-table" role="table" aria-label="Fichiers produits par l’application">
            <div className="table-row table-head" role="row">{columns.map((c) => <span key={c} role="columnheader">{c}</span>)}</div>
            {outputs.map((r) => (
              <div className="table-row" role="row" key={r.name}>
                <span role="cell" data-label="Sortie">{r.name}</span>
                <span role="cell" data-label="Format">{r.format}</span>
                <span role="cell" data-label="Usage">{r.use}</span>
              </div>
            ))}
          </Reveal>
          <p className="tech-copy" style={{ margin: '24px 0 0', fontSize: 15 }}>
            Dans QGIS, glissez les fichiers dans la fenêtre : ils se superposent sans réglage, car ils partagent le même système de coordonnées. Les fichiers sont dans le dossier <span className="tech-code">livrables/qgis/</span> de chaque mission.
          </p>

          <Reveal className="prose-figure" as="figure">
            <div className="shot"><img src={shots.testResults.src} width={shots.testResults.w} height={shots.testResults.h} loading="lazy"
              alt="Écran de résultats de l’application, avec une parcelle fictive : message de synthèse, quatre indicateurs et onglets de cartes." /></div>
            <figcaption><b>Exemple sur données de test.</b> Parcelle fictive : ces valeurs ne sont pas des résultats réels.</figcaption>
          </Reveal>

          <Reveal className="tech-block" as="div">
            <span className="section-kicker"><i />Installation</span>
            <h2>Prérequis</h2>
            <ul className="tech-list">
              <li>Windows. L’interface utilise WebView2, présent par défaut sur Windows 11 et sur la plupart des Windows 10 à jour. Sinon, l’application bascule seule sur l’interface classique.</li>
              <li>Docker Desktop, pour le moteur de traitement.</li>
              <li>Environ 8 Go de mémoire disponibles pour Docker. Sur un PC de 8 Go, choisissez la qualité « Rapide ».</li>
            </ul>
            <p>Une fois Docker installé et démarré, une seule commande crée le moteur de traitement :</p>
            <pre className="code-block"><code>docker run -d -p 3000:3000 --name nodeodm opendronemap/nodeodm</code></pre>
            <p>Ouvrez <span className="tech-code">http://localhost:3000</span> dans un navigateur pour vérifier : une page d’information JSON doit s’afficher. Pour l’arrêter puis le redémarrer : <span className="tech-code">docker stop nodeodm</span> et <span className="tech-code">docker start nodeodm</span>. L’adresse et le port du moteur se règlent dans les réglages avancés de l’application.</p>
            <p>NodeODM est un logiciel indépendant, sous licence AGPL-3.0. Il fonctionne séparément dans Docker et l’application le contacte par le réseau.</p>
          </Reveal>

          <Reveal className="tech-block" as="div">
            <span className="section-kicker"><i />Transparence</span>
            <h2>Limites connues</h2>
            <ul className="tech-list">{limits.map((l) => <li key={l}>{l}</li>)}</ul>
          </Reveal>

          <Reveal className="tech-block" as="div">
            <div className="tech-links">
              <Button href={LINKS.readme} icon="arrow" external>Lire le README</Button>
              <Button href={LINKS.github} variant="secondary" icon="github" external>Code source sur GitHub</Button>
            </div>
          </Reveal>
        </div>
      </section>
    </main>
  )
}
