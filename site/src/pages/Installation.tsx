import type { ReactNode } from 'react'
import { Accordion, Button, Icon, Reveal, Topography } from '../components/ui'
import { Checksum, CodeBlock } from '../components/Copy'
import { Contact } from '../components/Contact'
import { MacBuildFromSource, MacFirstLaunch } from '../components/MacContent'
import { PlatformPanel, PlatformTabs, usePlatform } from '../components/platform'
import { ENGINE_CMD_WINDOWS, LINKS, MAC, shots } from '../data'

const DOCKER = 'https://www.docker.com/products/docker-desktop/'

function Step({ n, title, last = false, children }: { n: string; title: string; last?: boolean; children: ReactNode }) {
  return (
    <Reveal as="section" className={`install-step ${last ? 'is-last' : ''}`} aria-labelledby={`etape-${n}`}>
      <div className="install-num" aria-hidden="true">{n}</div>
      <div className="install-body">
        <h2 id={`etape-${n}`}>{title}</h2>
        {children}
      </div>
    </Reveal>
  )
}

function Shot({ shot, alt, caption }: { shot: { src: string; w: number; h: number }; alt: string; caption: string }) {
  return (
    <figure className="install-shot">
      <div className="shot"><img src={shot.src} width={shot.w} height={shot.h} loading="lazy" alt={alt} /></div>
      <figcaption>{caption}</figcaption>
    </figure>
  )
}

const Check = ({ children }: { children: ReactNode }) => (
  <li><Icon name="check" size={18} /><span>{children}</span></li>
)

export default function Installation() {
  const mac = usePlatform() === 'mac'
  return (
    <main className="inner-page" id="contenu">
      <section className="inner-hero">
        <Topography />
        <div className="container">
          <a href="#/" className="back-link"><Icon name="arrow" size={16} /> Retour à l’accueil</a>
          <span className="section-kicker light"><i />Installation</span>
          <h1>Installer Vision Agricole, <em>pas à pas.</em></h1>
          <p>De votre ordinateur (Windows ou Mac) jusqu’à votre premier rapport, en trois étapes : l’application, le moteur de traitement, puis votre première mission.</p>
        </div>
      </section>

      <section className="section install-intro" aria-labelledby="avant">
        <div className="container">
          <Reveal className="prose">
            <span className="section-kicker"><i />Avant de commencer</span>
            <h2 id="avant">Ce qu’il vous faut.</h2>
            <p className="choose-os">Choisissez votre ordinateur :</p>
            <PlatformTabs idBase="inst" />
            <PlatformPanel idBase="inst">
              <ul className="checklist">
                {mac ? (
                  <>
                    <Check>Un <b>Mac à puce Apple Silicon</b> (M1, M2, M3…). Il n’y a pas de version Intel pour l’instant. Pour connaître votre puce : menu Pomme, puis « À propos de ce Mac ».</Check>
                    <Check>Environ <b>8 Go de mémoire</b> au total. Dans Docker Desktop, réglez la mémoire dans Réglages &gt; Resources : 4 à 5 Go sur un Mac de 8 Go.</Check>
                  </>
                ) : (
                  <>
                    <Check>Un ordinateur sous <b>Windows</b>.</Check>
                    <Check>Environ <b>8 Go de mémoire</b> disponibles pour Docker. Sur un PC de 8 Go, vous choisirez la qualité « Rapide ».</Check>
                  </>
                )}
                <Check>Les photos de votre drone (JPG ou PNG), réunies dans un dossier.</Check>
                <Check>Une connexion Internet <b>la première fois</b>, pour télécharger Docker et le moteur de traitement. Ensuite, le traitement de vos photos n’en a plus besoin.</Check>
              </ul>
            </PlatformPanel>
          </Reveal>
        </div>
      </section>

      <section className="section install-steps" style={{ background: '#fff' }}>
        <div className="container">
          <Step n="01" title="Téléchargez l’application">
            {mac ? (
              <>
                <p>Vision Agricole pour Mac est une application à glisser dans <b>Applications</b>. Elle est faite pour les Mac à puce <b>Apple Silicon</b> (M1, M2, M3…) ; il n’y a pas de version Intel pour l’instant.</p>
                <div className="install-actions">
                  <Button href={MAC.download}>Télécharger pour Mac</Button>
                  <span className="install-note">Version 1.1.0 · gratuit · <a href="#/licence">licence MIT</a></span>
                </div>
                <h3>Premier lancement</h3>
                <MacFirstLaunch />
                <Accordion title="Vérifier le fichier avant de l’ouvrir">
                  <Checksum platform="mac" />
                </Accordion>
                <Accordion title="Je préfère construire moi-même">
                  <MacBuildFromSource />
                </Accordion>
              </>
            ) : (
              <>
                <p>Vision Agricole tient dans <b>un seul fichier</b> : pas besoin d’installer Python. Double-cliquez dessus pour la lancer. Le premier lancement est un peu plus lent que les suivants.</p>
                <div className="install-actions">
                  <Button href={LINKS.download}>Télécharger pour Windows</Button>
                  <span className="install-note">Version 1.1.0 · gratuit · <a href="#/licence">licence MIT</a></span>
                </div>
                <div className="callout callout-warn" role="note">
                  <h3><Icon name="alert" size={18} /> Windows affiche un avertissement ?</h3>
                  <p>C’est normal : le logiciel est nouveau et n’est pas encore signé. Pour le lancer :</p>
                  <ol>
                    <li>Cliquez sur <b>Informations complémentaires</b>.</li>
                    <li>Puis sur <b>Exécuter quand même</b>.</li>
                  </ol>
                </div>
                <Accordion title="Vérifier le fichier avant de le lancer">
                  <Checksum />
                </Accordion>
              </>
            )}
          </Step>

          <Step n="02" title="Installez le moteur de traitement">
            <p>L’application ne traite pas les photos elle-même : elle les confie à un moteur, <b>NodeODM</b>, qui tourne sur votre ordinateur grâce à <b>Docker</b>. Cette étape se fait <b>une seule fois</b>.</p>

            <h3>A. Installez Docker Desktop</h3>
            <p>Téléchargez-le {mac ? <>(version pour Mac) </> : null}depuis le <a href={DOCKER} rel="noopener">site officiel de Docker</a>, installez-le puis démarrez-le. Attendez que l’indication en bas à gauche affiche <b>« Engine running »</b>.</p>

            <h3>B. Créez le moteur</h3>
            {mac ? (
              <>
                <p>Ouvrez le <b>Terminal</b>, collez cette commande, puis validez. Elle crée le moteur et le démarre en arrière-plan.</p>
                <CodeBlock code={MAC.engineCmd} label="créer le moteur de traitement NodeODM sur Mac" />
                <p className="install-aside">Sur Apple Silicon, l’option <span className="mono">--platform linux/amd64</span> fait tourner le moteur en émulation : le traitement est donc plus lent.</p>
              </>
            ) : (
              <>
                <p>Ouvrez l’<b>Invite de commandes</b> (ou PowerShell), collez cette commande, puis validez. Elle crée le moteur et le démarre en arrière-plan.</p>
                <CodeBlock code={ENGINE_CMD_WINDOWS} label="créer le moteur de traitement NodeODM" />
              </>
            )}

            <h3>C. Vérifiez qu’il répond</h3>
            <p>Ouvrez <span className="mono">http://localhost:3000</span> dans votre navigateur. Une page d’information (du texte JSON) doit s’afficher : le moteur est prêt.</p>

            <h3>Les fois suivantes</h3>
            <p>Il suffit de démarrer Docker Desktop, puis le moteur : dans l’onglet <b>Containers</b>, cliquez sur le bouton <b>▷</b> de la ligne <b>nodeodm</b>. Si vous préférez les commandes : <span className="mono">docker start nodeodm</span> pour le démarrer, <span className="mono">docker stop nodeodm</span> pour l’arrêter.</p>
            <Shot shot={shots.engine} alt="Écran d’aide de l’application : le moteur de traitement n’est pas encore démarré, avec les trois étapes pour le démarrer dans Docker Desktop."
              caption="Si le moteur n’est pas démarré, l’application vous l’explique et vous guide en trois étapes." />
          </Step>

          <Step n="03" title="Lancez votre première mission" last>
            {mac && <p className="install-aside">Les captures de cette étape viennent de la version Windows de l’application.</p>}
            <ol className="mission-steps">
              <li>
                <h3>L’accueil</h3>
                <p>Cliquez sur <b>« Démarrer une mission »</b>. L’indicateur en haut à droite montre si le moteur est prêt. S’il ne l’est pas, un clic dessus affiche les trois étapes pour le démarrer.</p>
                <Shot shot={shots.home} alt="Écran d’accueil de l’application avec le bouton « Démarrer une mission » et l’indicateur « Moteur non démarré » en haut à droite."
                  caption="L’accueil : démarrer une mission, ou ouvrir une mission précédente." />
              </li>
              <li>
                <h3>Étape 1 : vos photos</h3>
                <p>Choisissez le dossier du vol. L’application compte les photos et vous en montre un aperçu.</p>
                <Shot shot={shots.photos} alt="Étape 1 de l’application : choisir le dossier des photos du drone, formats acceptés JPG et PNG."
                  caption="Formats acceptés : JPG et PNG." />
              </li>
              <li>
                <h3>Étape 2 : votre parcelle</h3>
                <p>Indiquez le <b>nom de la parcelle</b>, l’<b>exploitant</b> et la <b>date</b> (obligatoires). Vous pouvez aussi ajouter l’altitude, le pilote, l’équipe et le nombre de zones (de 2 à 6), ainsi que des informations sur le sol (pH, texture, observation) ou une estimation en ligne avec SoilGrids. Tout cela est facultatif.</p>
              </li>
              <li>
                <h3>Étape 3 : vérification</h3>
                <p>Relisez le récapitulatif et choisissez la qualité : <b>« Rapide »</b> est recommandée sur un PC de 8 Go ; « Équilibré » et « Précis » demandent plus de mémoire. Cliquez ensuite sur <b>« Lancer le traitement »</b>.</p>
              </li>
              <li>
                <h3>Le traitement</h3>
                <p>Cinq étapes en langage simple, un pourcentage et le temps écoulé s’affichent. <b>Ne fermez pas l’application et ne mettez pas le PC en veille</b> pendant ce temps.</p>
              </li>
              <li>
                <h3>Vos résultats</h3>
                <p>L’application affiche une phrase de synthèse, quatre indicateurs et les cartes avec leur légende. Des boutons ouvrent le rapport PDF, le dossier des résultats et les fichiers pour QGIS. Plus tard, « Ouvrir une mission précédente » sur l’accueil permet de revoir une mission sans relancer le calcul.</p>
                <Shot shot={shots.testResults} alt="Écran de résultats de l’application, avec une parcelle fictive : synthèse, quatre indicateurs et onglets de cartes."
                  caption="Exemple sur données de test (parcelle fictive)." />
              </li>
            </ol>
          </Step>
        </div>
      </section>

      <section className="section" aria-labelledby="depannage">
        <div className="container">
          <Reveal className="prose">
            <span className="section-kicker"><i />Un souci ?</span>
            <h2 id="depannage">Dépannage.</h2>
          </Reveal>
          <Reveal className="install-faq">
            <Accordion title="L’application dit que le moteur n’est pas démarré" defaultOpen>
              <ol className="plain-steps">
                <li>Ouvrez <b>Docker Desktop</b> et attendez que l’indication en bas à gauche affiche « Engine running ».</li>
                <li>Dans l’onglet <b>Containers</b>, cliquez sur le bouton ▷ (démarrer) de la ligne <b>nodeodm</b>.</li>
                <li>Revenez à l’application et cliquez sur <b>« Vérifier à nouveau »</b>.</li>
              </ol>
              <p>Le moteur n’a jamais été créé ? Reprenez l’étape 02 (B).</p>
            </Accordion>
            <Accordion title="Mon ordinateur est lent ou manque de mémoire">
              <p>Le traitement des photos est gourmand en mémoire : Docker a besoin d’environ 8 Go disponibles. Choisissez la qualité <b>« Rapide »</b>, recommandée sur un PC de 8 Go. Sur un Mac Apple Silicon, le moteur tourne en émulation : il est plus lent.</p>
            </Accordion>
            <Accordion title="Sur Mac, macOS bloque l’ouverture de l’application">
              <MacFirstLaunch />
            </Accordion>
            <Accordion title="Sous Windows, l’application ne s’ouvre pas comme prévu">
              <p>La nouvelle interface a besoin de WebView2, déjà présent sur Windows 11 et sur la plupart des Windows 10 à jour. Si elle ne peut pas s’ouvrir, l’application bascule d’elle-même sur l’interface classique : le calcul est le même.</p>
            </Accordion>
            <Accordion title="Où sont mes résultats ?">
              <p>Dans le dossier de sortie choisi dans les <b>réglages avancés</b> (la roue dentée, en haut à droite). Les fichiers pour QGIS sont dans le sous-dossier <span className="mono">livrables/qgis</span> de chaque mission.</p>
            </Accordion>
            <Accordion title="Changer l’adresse du moteur ou le dossier des rapports">
              <p>Ouvrez les <b>réglages avancés</b> (la roue dentée). Vous y trouvez l’adresse et le port du moteur (par défaut <span className="mono">localhost</span> et <span className="mono">3000</span>), un bouton <b>« Tester la connexion »</b>, le dossier de sortie du rapport et la qualité proposée par défaut.</p>
              <Shot shot={shots.settings} alt="Réglages avancés : moteur de traitement, dossier de sortie du rapport et qualité par défaut." caption="Les réglages avancés, pour le technicien." />
            </Accordion>
          </Reveal>
          <Reveal className="prose" style={{ marginTop: 36 }}>
            <p>Toujours bloqué ? Écrivez-nous ou appelez-nous, nous vous aiderons :</p>
            <Contact />
            <p style={{ marginTop: 18 }}>Vous êtes technicien ? Le <a href="#/techniciens">détail du fonctionnement</a> est sur sa page dédiée.</p>
          </Reveal>
        </div>
      </section>

      <section className="section install-cta">
        <div className="container">
          <Reveal className="install-cta-box">
            <h2>Prêt à <em>commencer&nbsp;?</em></h2>
            <p>Téléchargez Vision Agricole et lancez votre première mission.</p>
            <div className="hero-actions" style={{ margin: '8px 0 0' }}>
              <Button href={LINKS.download} variant="light">Télécharger pour Windows</Button>
              <a href="#/techniciens" className="button button-ghost">Pour les techniciens <Icon name="arrow" /></a>
            </div>
          </Reveal>
        </div>
      </section>
    </main>
  )
}
