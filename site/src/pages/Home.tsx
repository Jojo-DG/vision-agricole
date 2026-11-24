import { Accordion, Button, Counter, Icon, Reveal, Topography } from '../components/ui'
import type { IconName } from '../components/ui'
import { BeforeAfter, Gallery } from '../components/Interactive'
import { Checksum, CodeBlock } from '../components/Copy'
import { MacBuildFromSource, MacFirstLaunch } from '../components/MacContent'
import { PlatformPanel, PlatformTabs, setPlatform, usePlatform } from '../components/platform'
import { Contact } from '../components/Contact'
import { benefits, faqs, LINKS, MAC, maps, shots, steps, team, testFlight, why } from '../data'

function Kicker({ children, light = false }: { children: string; light?: boolean }) {
  return <Reveal as="span" className={`section-kicker ${light ? 'light' : ''}`}><i />{children}</Reveal>
}

function Hero() {
  return (
    <section className="hero" id="accueil" aria-labelledby="titre-accueil">
      <Topography />
      <div className="health-orbit" aria-hidden="true"><img src={maps.afterZoning} width="900" height="1050" alt="" decoding="async" /></div>
      <div className="container hero-grid">
        <div className="hero-copy">
          <span className="section-kicker"><i />Analyse agricole, simplement</span>
          <h1 id="titre-accueil">De vos photos de drone à un rapport clair pour votre <em>parcelle.</em></h1>
          <p>Transformer les images du ciel en décisions simples pour le terrain.</p>
          <div className="hero-actions">
            <Button href="#telecharger">Télécharger pour Windows</Button>
            <Button href="#fonctionnement" variant="secondary">Voir comment ça marche</Button>
          </div>
          <p className="hero-mac">Aussi pour Mac (Apple Silicon) : <a href="#telecharger" onClick={() => setPlatform('mac')}>voir le téléchargement</a>.</p>
          <div className="proof-pill">
            <span className="award-mark"><Icon name="award" size={20} /></span>
            <span><b>Lauréat de l’ÉlectroChallenge 2026</b><small>Catégorie Orange</small></span>
          </div>
        </div>
        <div className="hero-visual">
          <figure className="shot window-angle">
            <img src={shots.home.src} width={shots.home.w} height={shots.home.h}
              alt="Écran d’accueil de Vision Agricole : le bouton « Démarrer une mission » et les trois étapes du parcours." />
          </figure>
          <div className="map-legend" aria-hidden="true"><span>Zones faibles</span><i /><span>Zones vigoureuses</span></div>
        </div>
      </div>
      <a href="#probleme" className="scroll-cue">Découvrir <span aria-hidden="true">↓</span></a>
    </section>
  )
}

function Problem() {
  return (
    <section className="problem" id="probleme" aria-labelledby="titre-probleme">
      <Topography />
      <Reveal className="container narrow">
        <span className="section-kicker light"><i />Le constat</span>
        <h2 id="titre-probleme">Une parcelle vue du sol cache l’essentiel : <em>où les plantes souffrent, où l’eau stagne, où intervenir en premier.</em></h2>
        <p>Un drone voit tout. Mais ses photos brutes ne disent rien à un agriculteur.</p>
      </Reveal>
    </section>
  )
}

function Transformation() {
  return (
    <section className="section transformation" id="resultats" aria-labelledby="titre-transformation">
      <div className="container">
        <Reveal className="section-heading split">
          <div><Kicker>La transformation</Kicker><h2 id="titre-transformation">Du ciel à la <em>décision.</em></h2></div>
          <p>Faites glisser le curseur pour voir comment des photos difficiles à lire deviennent une carte directement utile.</p>
        </Reveal>
        <Reveal variant="scale"><BeforeAfter /></Reveal>
        <div className="comparison-caption">
          <span><i className="red-dot" />Rouge : à traiter en priorité</span>
          <p>Les zones grises (sol nu, bâtiments, eau) sont exclues de l’analyse.</p>
          <span><i className="green-dot" />Vert : en bonne santé</span>
        </div>
        <small className="test-note">Résultat réel d’un vol test de 118 photos, sur une parcelle de 2,17 ha</small>
        <ul className="flight-stats" aria-label="Chiffres du vol test" style={{ listStyle: 'none', margin: '56px 0 0', paddingInline: 0, paddingBottom: 0 }}>
          {testFlight.map((s, i) => (
            <Reveal as="li" key={s.label} delay={i * 0.1}>
              <strong>
                <Counter to={s.value} decimals={s.decimals} /><small>{s.unit}</small>
                {'extra' in s && <> <Counter to={s.extra.value} /><small>{s.extra.unit}</small></>}
              </strong>
              <b>{s.label}</b>
              <span className="detail">{s.detail}</span>
            </Reveal>
          ))}
        </ul>
      </div>
    </section>
  )
}

function Steps() {
  return (
    <section className="section steps-section" id="fonctionnement" aria-labelledby="titre-etapes">
      <Topography />
      <div className="container">
        <Reveal className="section-heading centered">
          <Kicker>Une méthode guidée</Kicker>
          <h2 id="titre-etapes">Trois étapes. <em>Pas une de plus.</em></h2>
          <p>Vision Agricole vous accompagne du choix des images jusqu’au rapport final.</p>
        </Reveal>
        <Reveal as="div" className="steps">
          <article className="step-card">
            <span className="step-number">{steps[0].n}</span>
            <div><h3>{steps[0].title}</h3><p>{steps[0].text}</p></div>
            <div className="step-visual"><img src={shots.photos.src} width={shots.photos.w} height={shots.photos.h} loading="lazy"
              alt="Écran de l’application pour choisir le dossier des photos du drone." /></div>
          </article>
          <article className="step-card">
            <span className="step-number">{steps[1].n}</span>
            <div><h3>{steps[1].title}</h3><p>{steps[1].text}</p></div>
            <div className="step-visual" aria-hidden="true">
              <div className="step-form">
                <div><small>Nom de la parcelle</small><i /></div>
                <div><small>Exploitant</small><i /></div>
                <div><small>Date du vol</small><i /></div>
              </div>
            </div>
          </article>
          <article className="step-card">
            <span className="step-number">{steps[2].n}</span>
            <div><h3>{steps[2].title}</h3><p>{steps[2].text}</p></div>
            <div className="step-visual"><div className="step-map"><img src={maps.afterZoning} width="900" height="1050" loading="lazy"
              alt="Carte de zonage d’une parcelle, produite par l’application." /></div></div>
          </article>
          <svg className="flight-path" viewBox="0 0 1000 80" preserveAspectRatio="none" aria-hidden="true">
            <path d="M20 42c170-67 238 64 390 0S680 3 980 41" /><circle cx="20" cy="42" r="5" /><circle cx="980" cy="41" r="5" />
          </svg>
        </Reveal>
      </div>
    </section>
  )
}

function Benefits() {
  const media: Record<number, { src: string; w: number; h: number; alt: string }> = {
    0: { ...maps.vari, alt: 'Carte de vigueur de la végétation (VARI) d’une parcelle.' },
    1: { ...maps.zoning, alt: 'Carte de zonage d’une parcelle en quatre classes.' },
    2: { ...maps.lowZones, alt: 'Carte des zones basses où l’eau peut s’accumuler, en bleu.' },
  }
  return (
    <section className="section benefits-section" aria-labelledby="titre-benefices">
      <div className="container">
        <Reveal className="section-heading split">
          <div><Kicker>Des résultats utiles</Kicker><h2 id="titre-benefices">Ce que vous <em>obtenez.</em></h2></div>
          <p>Pas une accumulation de données. Des réponses visuelles, organisées pour décider et agir.</p>
        </Reveal>
        <div className="bento">
          {benefits.map((b, i) => (
            <Reveal as="article" key={b.title} delay={(i % 3) * 0.08} className={`benefit-card benefit-${i + 1} ${media[i] && i > 0 ? 'has-media' : ''}`}>
              <span className="icon-box"><Icon name={b.icon as IconName} /></span>
              <div><h3>{b.title}</h3><p>{b.text}</p></div>
              {i === 0 && (
                <div className="benefit-map"><img src={media[0].src} width={media[0].w} height={media[0].h} loading="lazy" alt={media[0].alt} style={{ borderRadius: 14 }} /></div>
              )}
              {i > 0 && media[i] && (
                <div className="benefit-media"><img src={media[i].src} width={media[i].w} height={media[i].h} loading="lazy" alt={media[i].alt} /></div>
              )}
              {i === 4 && <div className="pdf-mini" aria-hidden="true"><span>VA</span><i /><i /><i /></div>}
              {i === 5 && <div className="format-chips" aria-hidden="true"><span>GeoTIFF</span><span>Shapefile</span><span>DXF</span><span>QGIS</span></div>}
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}

function GallerySection() {
  return (
    <section className="section gallery-section" aria-labelledby="titre-galerie">
      <div className="container gallery-heading">
        <Reveal className="section-heading split">
          <div><Kicker light>Dans l’application</Kicker><h2 id="titre-galerie">Une interface qui vous <em>guide.</em></h2></div>
          <p>Chaque écran explique clairement la prochaine action, sans vous noyer dans les réglages.</p>
        </Reveal>
      </div>
      <Gallery />
    </section>
  )
}

function Why() {
  return (
    <section className="section why-section" aria-labelledby="titre-pourquoi">
      <div className="container why-grid">
        <Reveal className="why-intro">
          <Kicker>Pensé pour le terrain</Kicker>
          <h2 id="titre-pourquoi">Pourquoi Vision <em>Agricole&nbsp;?</em></h2>
          <p>La technologie reste en arrière-plan. Vous gardez le contrôle, du premier clic au rapport final.</p>
          <div className="benin-line"><span aria-hidden="true">229</span><b>Conçu au Bénin.</b></div>
        </Reveal>
        <div className="why-list">
          {why.map((w, i) => (
            <Reveal key={w.n} delay={i * 0.08}>
              <span>{w.n}</span>
              <div><h3>{w.title}</h3><p>{w.text}{'link' in w && <> <a className="inline-link" href={w.link.href}>{w.link.label}</a>.</>}</p></div>
              <Icon name="check" />
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}

function Story() {
  return (
    <section className="story-strip" id="histoire" aria-labelledby="titre-histoire">
      <div className="container story-grid">
        <Reveal variant="scale" className="award-seal" aria-hidden="true"><span>Lauréat</span><b>2026</b><small>Catégorie Orange</small></Reveal>
        <Reveal>
          <span className="section-kicker light"><i />Notre histoire</span>
          <h2 id="titre-histoire">Né en quelques jours, <em>validé devant un jury.</em></h2>
          <p>Porté par le Groupe 2 d’Impact Connexion, Vision Agricole a remporté la Catégorie Orange de l’ÉlectroChallenge 2026. Accompagnée par son mentor, Renaud DANVI, l’équipe compte aussi le meilleur participant de la catégorie. Depuis, l’application continue d’évoluer et sert déjà dans des projets.</p>
          <a className="text-link" href="#/histoire">Lire toute l’histoire <Icon name="arrow" /></a>
        </Reveal>
      </div>
    </section>
  )
}

function Team() {
  return (
    <section className="section team-section" id="equipe" aria-labelledby="titre-equipe">
      <div className="container">
        <Reveal className="section-heading split">
          <div><Kicker>Le Groupe 2</Kicker><h2 id="titre-equipe">Une équipe, <em>un même terrain.</em></h2></div>
          <p>Quatre compétences réunies pour transformer une idée ambitieuse en outil concret.</p>
        </Reveal>
        <div className="team-grid">
          {team.map((m, i) => (
            <Reveal as="article" key={m.name} delay={i * 0.1} className="team-card">
              <div className="team-portrait"><img src={m.photo} width={m.w} height={m.h} loading="lazy" alt={`Portrait de ${m.name}`} /></div>
              <div><small>{m.role}</small><h3>{m.name}</h3><p>{m.detail}</p></div>
            </Reveal>
          ))}
        </div>
        <p className="mentor">Mentor : <b>Renaud DANVI</b></p>
      </div>
    </section>
  )
}

function Download() {
  const platform = usePlatform()
  const mac = platform === 'mac'
  return (
    <section className="section download-section" id="telecharger" aria-labelledby="titre-telecharger">
      <div className="container">
        <Reveal variant="scale" className="download-card">
          <Topography />
          <div className="download-tabs"><PlatformTabs idBase="dl" light /></div>
          <PlatformPanel idBase="dl" className="download-panel">
            <div className="download-main">
              <span className="section-kicker light"><i />Version 1.1.0</span>
              <h2 id="titre-telecharger">Prêt à voir votre parcelle <em>autrement&nbsp;?</em></h2>
              <p>Téléchargez Vision Agricole et transformez votre prochain vol en décisions claires.</p>
              {mac ? (
                <>
                  <a href={MAC.download} className="button button-light"><Icon name="download" />Télécharger pour Mac</a>
                  <div className="requirements">
                    <span><Icon name="check" size={16} />Mac Apple Silicon (M1, M2, M3…)</span>
                    <span><Icon name="check" size={16} />Pas de version Intel pour l’instant</span>
                    <span><Icon name="check" size={16} />Gratuit</span>
                  </div>
                </>
              ) : (
                <>
                  <a href={LINKS.download} className="button button-light"><Icon name="download" />Télécharger Vision Agricole 1.1.0 pour Windows</a>
                  <div className="requirements">
                    <span><Icon name="check" size={16} />Windows</span>
                    <span><Icon name="check" size={16} />Un seul fichier, sans installer Python</span>
                    <span><Icon name="check" size={16} />Gratuit</span>
                  </div>
                </>
              )}
              <a className="text-link" href="#/installation">Guide d’installation pas à pas <Icon name="arrow" /></a>
            </div>
            <div className="download-details">
              <h3>Avant de commencer</h3>
              {mac ? (
                <>
                  <ul>
                    <li>Un Mac à puce <b>Apple Silicon</b> (M1, M2, M3…). Il n’y a pas de version Intel pour l’instant.</li>
                    <li><b>Docker Desktop</b> et le moteur de traitement (NodeODM) restent nécessaires, expliqués dans le <a href="#/installation">guide d’installation</a>.</li>
                  </ul>
                  <p className="engine-label">Créez le moteur une seule fois, dans le Terminal :</p>
                  <CodeBlock code={MAC.engineCmd} label="créer le moteur de traitement NodeODM sur Mac" />
                  <p className="verify-tip">Sur Apple Silicon, le moteur tourne en émulation : le traitement est plus lent.</p>
                  <Accordion title="Premier lancement sur Mac"><MacFirstLaunch /></Accordion>
                  <Accordion title="Je préfère construire moi-même"><MacBuildFromSource /></Accordion>
                  <Checksum platform="mac" />
                </>
              ) : (
                <>
                  <ul>
                    <li>Un ordinateur Windows.</li>
                    <li>Docker Desktop et le moteur de traitement (NodeODM), expliqués pas à pas dans le <a href="#/installation">guide d’installation</a>.</li>
                    <li>Sur un PC de 8 Go, choisissez la qualité « Rapide ».</li>
                  </ul>
                  <Accordion title="Windows affiche un avertissement ?">
                    <p>C’est normal pour un nouveau logiciel qui n’est pas encore signé. Cliquez sur <b>Informations complémentaires</b>, puis sur <b>Exécuter quand même</b>.</p>
                    <p>Vous préférez vérifier d’abord ? Utilisez l’empreinte et l’analyse ci-dessous.</p>
                  </Accordion>
                  <Checksum />
                </>
              )}
            </div>
          </PlatformPanel>
        </Reveal>
      </div>
    </section>
  )
}

function Faq() {
  return (
    <section className="section faq-section" aria-labelledby="titre-faq">
      <div className="container faq-grid">
        <Reveal>
          <Kicker>Questions fréquentes</Kicker>
          <h2 id="titre-faq">Avant votre premier <em>vol.</em></h2>
          <p>Les réponses essentielles pour démarrer sereinement.</p>
          <p className="faq-contact">Une autre question ? Écrivez-nous ou appelez-nous.</p>
          <Contact />
        </Reveal>
        <Reveal delay={0.1}>
          {faqs.map((f, i) => (
            <Accordion key={f.q} title={f.q} defaultOpen={i === 0}>
              {f.a.map((line, j) => <p key={j}>{line}</p>)}
              {'link' in f && <p><a className="inline-link" href={f.link.href}>{f.link.label}</a></p>}
              {'contact' in f && <Contact />}
            </Accordion>
          ))}
        </Reveal>
      </div>
    </section>
  )
}

export default function Home() {
  return (
    <>
      <Hero />
      <Problem />
      <Transformation />
      <Steps />
      <Benefits />
      <GallerySection />
      <Why />
      <Story />
      <Team />
      <Download />
      <Faq />
    </>
  )
}
