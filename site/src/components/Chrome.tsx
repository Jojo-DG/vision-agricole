import { useEffect, useState } from 'react'
import type { MouseEvent, ReactNode } from 'react'
import { CONTACT, LINKS } from '../data'
import { Icon, Topography } from './ui'

/* ---------- Navigation : pages par hash (#/histoire), sections par ancre (#resultats) ---------- */

export type Page = 'home' | 'histoire' | 'techniciens' | 'installation' | 'licence'

export function pageFromHash(hash: string): Page {
  if (hash === '#/histoire') return 'histoire'
  if (hash === '#/techniciens') return 'techniciens'
  if (hash === '#/installation') return 'installation'
  if (hash === '#/licence') return 'licence'
  return 'home'
}

let pendingSection: string | null = null
export const takePendingSection = () => { const id = pendingSection; pendingSection = null; return id }

/** Lien vers une section de l'accueil, utilisable depuis n'importe quelle page. */
export function SectionLink({ id, page, className, onClick, children }: {
  id: string; page: Page; className?: string; onClick?: () => void; children: ReactNode
}) {
  const handle = (_e: MouseEvent<HTMLAnchorElement>) => {
    if (page !== 'home') pendingSection = id
    onClick?.()
  }
  return <a href={page === 'home' ? `#${id}` : '#/'} className={className} onClick={handle}>{children}</a>
}

const links = [
  ['Fonctionnement', 'fonctionnement'],
  ['Résultats', 'resultats'],
  ['Télécharger', 'telecharger'],
  ['Notre histoire', 'histoire'],
  ['Équipe', 'equipe'],
] as const

export function Header({ page }: { page: Page }) {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => { window.removeEventListener('keydown', onKey); document.body.style.overflow = '' }
  }, [open])
  const close = () => setOpen(false)
  return (
    <header className={`site-header ${scrolled || page !== 'home' ? 'is-scrolled' : ''} ${page !== 'home' ? 'is-solid' : ''}`}>
      <div className="header-inner">
        <a className="logo" href={page === 'home' ? '#accueil' : '#/'} aria-label="Vision Agricole, accueil">
          <img src="logo.svg" width="127" height="52" alt="Vision Agricole" />
        </a>
        <nav aria-label="Navigation principale">
          {links.map(([name, id]) => <SectionLink key={id} id={id} page={page}>{name}</SectionLink>)}
        </nav>
        <SectionLink id="telecharger" page={page} className="button button-primary">Télécharger</SectionLink>
        <button type="button" className="menu-toggle" aria-label={open ? 'Fermer le menu' : 'Ouvrir le menu'}
          aria-expanded={open} aria-controls="menu-mobile" onClick={() => setOpen(!open)}>
          <Icon name={open ? 'x' : 'menu'} size={26} />
        </button>
      </div>
      <div id="menu-mobile" className={`mobile-menu ${open ? 'is-open' : ''}`}>
        {links.map(([name, id], i) => (
          <SectionLink key={id} id={id} page={page} onClick={close}><span>0{i + 1}</span>{name}</SectionLink>
        ))}
        <SectionLink id="telecharger" page={page} className="button button-primary" onClick={close}>Télécharger pour Windows</SectionLink>
      </div>
    </header>
  )
}

export function Footer({ page }: { page: Page }) {
  return (
    <footer>
      <Topography />
      <div className="container">
        <div className="footer-top">
          <div className="footer-brand">
            <span className="badge"><img src="logo-icon.png" width="42" height="38" alt="" /></span>
            <span>Vision<br />Agricole</span>
          </div>
          <p>Transformer les images du ciel en décisions simples pour le terrain.</p>
          <SectionLink id="telecharger" page={page} className="button button-light">Télécharger <Icon name="download" /></SectionLink>
        </div>
        <div className="footer-links">
          <div>
            <span>Explorer</span>
            <SectionLink id="fonctionnement" page={page}>Fonctionnement</SectionLink>
            <SectionLink id="resultats" page={page}>Résultats</SectionLink>
            <SectionLink id="equipe" page={page}>Équipe</SectionLink>
          </div>
          <div>
            <span>En savoir plus</span>
            <a href="#/histoire">Notre histoire</a>
            <a href="#/techniciens">Pour les techniciens</a>
            <a href="#/installation">Guide d’installation</a>
          </div>
          <div>
            <span>Projet libre</span>
            <a href={LINKS.github}><Icon name="github" size={16} /> Code sur GitHub</a>
            <a href="#/licence">Licence MIT</a>
          </div>
          <div>
            <span>Une question ?</span>
            <a href={`mailto:${CONTACT.email}`}><Icon name="mail" size={16} /> {CONTACT.email}</a>
            <a href={`tel:${CONTACT.tel}`}><Icon name="phone" size={16} /> {CONTACT.phone}</a>
          </div>
        </div>
        <p className="footer-credits">
          Application sous <a href="#/licence">licence MIT</a>. Moteur de traitement : NodeODM / OpenDroneMap, licence AGPL-3.0, qui fonctionne séparément dans Docker.
          Icônes d’après Feather Icons (licence MIT). Polices : Fraunces, Plus Jakarta Sans et DM Mono (licence SIL OFL).
        </p>
        <div className="footer-bottom">
          <span>© 2026 Groupe 2 – Impact Connexion</span>
          <span>Groupe 2 – Impact Connexion · ÉlectroChallenge 2026</span>
        </div>
      </div>
    </footer>
  )
}
