import { Icon, Reveal, Topography } from '../components/ui'
import { Contact } from '../components/Contact'
import { LINKS } from '../data'

// Texte officiel du fichier LICENSE du dépôt (en anglais : seule cette version fait foi).
const MIT_TEXT = `MIT License

Copyright (c) 2026 Groupe 2 – Impact Connexion

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.`

const credits = [
  ['Vision Agricole', 'Licence MIT. Copyright © 2026 Groupe 2 – Impact Connexion. Le logo appartient au Groupe 2.'],
  ['NodeODM / OpenDroneMap', 'Licence AGPL-3.0. C’est un logiciel indépendant : il n’est pas inclus dans Vision Agricole, il fonctionne séparément dans Docker et l’application le contacte par le réseau.'],
  ['Bibliothèques de l’application', 'PyODM, rasterio, NumPy, scikit-learn, Matplotlib, ReportLab, pypdf, Pillow, CustomTkinter, pyshp, ezdxf et contourpy, chacune sous sa propre licence libre. Merci à leurs auteurs.'],
  ['Icônes', 'Dessinées d’après Feather Icons (licence MIT).'],
  ['Polices du site', 'Fraunces, Plus Jakarta Sans et DM Mono (licence SIL Open Font License).'],
] as const

export default function License() {
  return (
    <main className="inner-page" id="contenu">
      <section className="inner-hero">
        <Topography />
        <div className="container">
          <a href="#/" className="back-link"><Icon name="arrow" size={16} /> Retour à l’accueil</a>
          <span className="section-kicker light"><i />Licence</span>
          <h1>Gratuit et libre, <em>licence MIT.</em></h1>
          <p>Vision Agricole est un logiciel libre. Voici, en mots simples, ce que cela vous permet de faire.</p>
        </div>
      </section>

      <section className="section" aria-labelledby="en-bref">
        <div className="container">
          <Reveal className="section-heading">
            <span className="section-kicker"><i />En bref</span>
            <h2 id="en-bref">Ce que la licence <em>vous permet.</em></h2>
          </Reveal>
          <div className="license-grid">
            <Reveal className="license-card">
              <span className="icon-box"><Icon name="check" /></span>
              <h3>Vous pouvez</h3>
              <ul>
                <li>utiliser l’application, gratuitement, pour votre exploitation ou votre travail ;</li>
                <li>la copier et la donner à d’autres ;</li>
                <li>lire son code et le modifier ;</li>
                <li>la redistribuer, même dans un projet qui rapporte de l’argent.</li>
              </ul>
            </Reveal>
            <Reveal delay={0.1} className="license-card">
              <span className="icon-box"><Icon name="file" /></span>
              <h3>À une condition</h3>
              <ul>
                <li>conserver la mention de copyright et le texte de la licence dans les copies que vous partagez.</li>
              </ul>
            </Reveal>
            <Reveal delay={0.2} className="license-card">
              <span className="icon-box"><Icon name="alert" /></span>
              <h3>À savoir</h3>
              <ul>
                <li>le logiciel est fourni « tel quel », sans garantie ;</li>
                <li>les auteurs ne sont pas responsables des dommages liés à son usage ;</li>
                <li>le rapport est une aide à la décision : il ne remplace ni un agronome ni une analyse de sol.</li>
              </ul>
            </Reveal>
          </div>
        </div>
      </section>

      <section className="section" style={{ background: '#fff' }} aria-labelledby="texte">
        <div className="container">
          <Reveal className="prose">
            <span className="section-kicker"><i />Texte officiel</span>
            <h2 id="texte">Le texte de la licence.</h2>
            <p>Le texte ci-dessous est celui du fichier <span className="mono">LICENSE</span> du projet. Il est en anglais, et c’est cette version qui fait foi : le résumé ci-dessus est donné à titre d’information.</p>
          </Reveal>
          <Reveal as="div"><pre className="license-text" tabIndex={0} aria-label="Texte de la licence MIT">{MIT_TEXT}</pre></Reveal>
          <p className="license-note">Le code source est public : <a className="inline-link" href={LINKS.github} rel="noopener">voir le projet sur GitHub</a>.</p>
        </div>
      </section>

      <section className="section" aria-labelledby="credits">
        <div className="container">
          <Reveal className="prose">
            <span className="section-kicker"><i />Crédits</span>
            <h2 id="credits">Les autres logiciels utilisés.</h2>
            <p>Vision Agricole s’appuie sur des logiciels libres, chacun sous sa propre licence.</p>
          </Reveal>
          <Reveal as="div">
            <ul className="credit-list">
              {credits.map(([name, text]) => <li key={name}><b>{name}</b><span>{text}</span></li>)}
            </ul>
          </Reveal>
          <Reveal className="prose" style={{ marginTop: 40 }}>
            <h2 style={{ fontSize: 28 }}>Une question sur la licence ?</h2>
            <p>Écrivez-nous ou appelez-nous :</p>
            <Contact />
          </Reveal>
        </div>
      </section>
    </main>
  )
}
