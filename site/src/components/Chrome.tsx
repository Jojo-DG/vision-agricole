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

/* Blocage du défilement de la page quand le menu est ouvert, sans perdre la position :
   le corps de page est figé (position: fixed) et la position est rétablie à la fermeture. */
let lockedY: number | null = null
const isScrollLocked = () => lockedY !== null
function lockScroll() {
  if (lockedY !== null) return
  lockedY = window.scrollY
  const st = document.body.style
  st.position = 'fixed'; st.top = `-${lockedY}px`; st.left = '0'; st.right = '0'; st.width = '100%'
}
function unlockScroll() {
  if (lockedY === null) return
  const y = lockedY
  lockedY = null
  const st = document.body.style
  st.position = ''; st.top = ''; st.left = ''; st.right = ''; st.width = ''
  window.scrollTo({ top: y, behavior: 'instant' as ScrollBehavior })
}

export function Header({ page }: { page: Page }) {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    // Pendant que le menu est ouvert, la page est figée : on ignore ces faux événements de défilement.
    const onScroll = () => { if (!isScrollLocked()) setScrolled(window.scrollY > 24) }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  useEffect(() => {
    if (!open) return
    lockScroll()
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => { window.removeEventListener('keydown', onKey); unlockScroll() }
  }, [open])
  // Si l'écran s'élargit (rotation, bureau) alors que le menu est ouvert, on le ferme.
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 981px)')
    const onChange = () => { if (mq.matches) setOpen(false) }
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  /* Clic sur un lien du menu : on rend d'abord la page (position rétablie), puis on va à la section. */
  const go = (id: string) => (e: MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault()
    unlockScroll()
    setOpen(false)
    if (page === 'home') {
      requestAnimationFrame(() => {
        const calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches
        document.getElementById(id)?.scrollIntoView({ behavior: calm ? 'auto' : 'smooth', block: 'start' })
        history.replaceState(null, '', `#${id}`)
      })
    } else {
      pendingSection = id
      window.location.hash = '#/'
    }
  }

  return (
    <>
      <header className={`site-header ${scrolled || page !== 'home' ? 'is-scrolled' : ''} ${page !== 'home' ? 'is-solid' : ''} ${open ? 'menu-open' : ''}`}>
        <div className="header-inner">
          <a className="logo" href={page === 'home' ? '#accueil' : '#/'} aria-label="Vision Agricole, accueil" onClick={() => setOpen(false)}>
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
      </header>
      {/* Menu mobile : frère du <header> (et non enfant), car un parent avec backdrop-filter
          ferait de lui le repère de position: fixed et le tronquerait à la hauteur de l'en-tête. */}
      <div id="menu-mobile" className={`mobile-menu ${open ? 'is-open' : ''}`} aria-hidden={!open}>
        {links.map(([name, id], i) => (
          <a key={id} href={page === 'home' ? `#${id}` : '#/'} onClick={go(id)} tabIndex={open ? 0 : -1}><span>0{i + 1}</span>{name}</a>
        ))}
        <a href={page === 'home' ? '#telecharger' : '#/'} className="button button-primary" onClick={go('telecharger')} tabIndex={open ? 0 : -1}>Télécharger pour Windows</a>
      </div>
    </>
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
