import { Icon, Reveal, Topography } from '../components/ui'
import { SectionLink } from '../components/Chrome'
import { shots, timeline } from '../data'

export default function History() {
  return (
    <main className="inner-page" id="contenu">
      <section className="inner-hero">
        <Topography />
        <div className="container">
          <a href="#/" className="back-link"><Icon name="arrow" size={16} /> Retour à l’accueil</a>
          <span className="section-kicker light"><i />Notre histoire</span>
          <h1>Né en quelques jours, <em>validé devant un jury.</em></h1>
          <p>Comment Vision Agricole est né, pendant l’ÉlectroChallenge 2026.</p>
        </div>
      </section>

      <section className="section" aria-labelledby="h-concours">
        <div className="container">
          <Reveal className="prose">
            <span className="section-kicker"><i />Le concours</span>
            <h2 id="h-concours">Un défi, cinq équipes.</h2>
            <p>L’ÉlectroChallenge a pour promoteur principal Monsieur Goldfrid OBELAKOU. Le concours était ouvert à plusieurs catégories, selon l’âge.</p>
            <p>La nôtre, la <b>Catégorie Orange</b> (18 à 30 ans), portait sur la cartographie agricole par drone. Cinq équipes s’y affrontaient. Les phases préparatoires ont commencé le 2 août, et la finale le 17 août.</p>
          </Reveal>
        </div>
      </section>

      <section className="section" style={{ background: '#fff' }} aria-labelledby="h-recit">
        <div className="container">
          <Reveal className="prose">
            <span className="section-kicker"><i />Le récit</span>
            <h2 id="h-recit">Des journées longues, un pitch.</h2>
            <p>Tout a commencé à la mi-juillet 2026. Nous avions chacun postulé de notre côté, puis passé un test de sélection à la hauteur du défi. Les candidats retenus ont ensuite été répartis en équipes. Le Groupe 2 – Impact Connexion s’est formé autour de notre mentor, Monsieur Renaud DANVI. Avec lui, nous avons commencé à parler du projet.</p>
            <p>Le vrai travail a démarré le 13 août, par une séance de cartographie sur un vrai terrain. Nous avons décidé de développer l’application en parallèle. Ce jour-là, nous avons travaillé jusqu’à 22 h, et la fatigue était bien réelle. Il a ensuite fallu trouver un ordinateur assez puissant pour le traitement photogrammétrique. Ce n’était pas simple : le reste de la semaine, nous rentrions très tard.</p>
            <p>Le samedi, nous avons fait les derniers réglages de l’application et lancé la présentation PowerPoint, avec de vrais débats dans l’équipe. Le lundi soir, nous étions enfin à l’aise avec le diaporama. Le mardi, nous l’avons terminé et nous avons commencé à répéter. Ce moment a été précieux : nous avons vu les points faibles de chacun et travaillé dessus, grâce au matériel de répétition mis à notre disposition par les encadrants.</p>
            <p>Le mercredi 19 août, nous avons pitché devant le jury. Nous n’y croyions pas vraiment : certaines propositions des quatre autres équipes de la catégorie nous avaient impressionnés. Mais nous avions choisi d’être très réalistes, de croire à notre projet et de nous donner à fond. <b>Nous avons remporté le défi.</b> Jaime a en plus reçu le titre de meilleur participant de la catégorie.</p>
          </Reveal>
        </div>
      </section>

      <section className="section timeline-section" aria-labelledby="h-frise">
        <div className="container">
          <Reveal className="section-heading">
            <span className="section-kicker"><i />La frise</span>
            <h2 id="h-frise">Du premier test au <em>podium.</em></h2>
          </Reveal>
          <div className="timeline">
            {timeline.map((t, i) => (
              <Reveal as="article" key={t.date} delay={0.05}>
                <div className="timeline-date"><span>{String(i + 1).padStart(2, '0')}</span><b>{t.date}</b></div>
                <div>
                  <h3>{t.title}</h3>
                  <p>{t.text}</p>
                  {'award' in t && <div className="timeline-award">Lauréat · Catégorie Orange · ÉlectroChallenge 2026</div>}
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="section" style={{ background: '#fff' }} aria-labelledby="h-origine">
        <div className="container">
          <Reveal className="prose">
            <span className="section-kicker"><i />D’où l’on vient</span>
            <h2 id="h-origine">Avant Vision Agricole.</h2>
            <p>Il y a eu AgriDrone Analytics : la version 0.0.0, réalisée par Constantino avec Streamlit et WebODM.</p>
            <figure className="prose-figure" style={{ marginTop: 28 }}>
              <div className="shot"><img src={shots.first.src} width={shots.first.w} height={shots.first.h} loading="lazy" alt="Capture de la toute première version, AgriDrone Analytics, réalisée avec Streamlit." /></div>
              <figcaption>La toute première version : AgriDrone Analytics (version 0.0.0).</figcaption>
            </figure>
          </Reveal>
        </div>
      </section>

      <section className="section" aria-labelledby="h-maintenant">
        <div className="container">
          <Reveal className="prose">
            <span className="section-kicker"><i />Et maintenant</span>
            <h2 id="h-maintenant">L’aventure continue.</h2>
            <p>Nous avons gardé le contact. Nous poursuivons l’aventure : l’application évolue, et nous participons déjà à des projets avec elle.</p>
            <p>Ce site a été créé pour la faire connaître et la mettre à la disposition de ceux qui en ont besoin.</p>
            <div className="hero-actions" style={{ margin: '24px 0 0' }}>
              <SectionLink id="telecharger" page="histoire" className="button button-primary">Télécharger l’application <Icon name="download" /></SectionLink>
              <SectionLink id="equipe" page="histoire" className="button button-secondary">Rencontrer l’équipe <Icon name="arrow" /></SectionLink>
            </div>
          </Reveal>
        </div>
      </section>
    </main>
  )
}
