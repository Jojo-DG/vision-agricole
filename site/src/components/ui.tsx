import { createElement, useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'

/* ---------- Icônes (style Feather, trait de 1,7 px) ---------- */

export type IconName =
  | 'arrow' | 'award' | 'check' | 'chevron' | 'copy' | 'download' | 'drop' | 'file'
  | 'github' | 'grid' | 'lock' | 'map' | 'menu' | 'photo' | 'settings' | 'x' | 'zoom'

const paths: Record<IconName, ReactNode> = {
  arrow: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
  award: <><circle cx="12" cy="8" r="6" /><path d="m8.2 13.4-1.2 8.6 5-3 5 3-1.2-8.6" /></>,
  check: <path d="m5 12 4 4L19 6" />,
  chevron: <path d="m6 9 6 6 6-6" />,
  copy: <><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3" /></>,
  download: <><path d="M12 3v12" /><path d="m7 10 5 5 5-5" /><path d="M5 21h14" /></>,
  drop: <path d="M12 3s6 6.2 6 11a6 6 0 0 1-12 0c0-4.8 6-11 6-11Z" />,
  file: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6M8 13h8M8 17h6" /></>,
  github: <><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3.3-.4 6.8-1.6 6.8-7A5.4 5.4 0 0 0 19.4 4 5 5 0 0 0 19.3.6S18.2.2 15 2a13.4 13.4 0 0 0-7 0C4.8.2 3.7.6 3.7.6A5 5 0 0 0 3.6 4a5.4 5.4 0 0 0-1.4 3.7c0 5.4 3.5 6.6 6.8 7A4.8 4.8 0 0 0 8 18v4" /><path d="M8 19c-3 .9-3-1.5-4-2" /></>,
  grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
  lock: <><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
  map: <><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z" /><path d="M9 3v15M15 6v15" /></>,
  menu: <path d="M4 7h16M4 17h16" />,
  photo: <><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="8.5" cy="9" r="1.5" /><path d="m21 15-5-5L5 20" /></>,
  settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" /></>,
  x: <path d="m6 6 12 12M18 6 6 18" />,
  zoom: <><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3M11 8v6M8 11h6" /></>,
}

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return (
    <svg aria-hidden="true" focusable="false" className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      {paths[name]}
    </svg>
  )
}

/** Courbes de niveau décoratives (dessinées progressivement à l'affichage). */
export function Topography({ className = '' }: { className?: string }) {
  return (
    <svg className={`topography ${className}`} viewBox="0 0 800 500" fill="none" aria-hidden="true">
      {[
        'M-40 160C80 10 214 10 270 108c66 115 145 36 240 5 109-35 203 8 330 123',
        'M-40 196C84 51 200 48 250 137c59 105 151 65 251 26 116-45 222 8 339 113',
        'M-30 238C72 109 175 83 226 160c72 108 151 93 269 40 116-52 228 10 337 113',
        'M-20 282C74 163 167 121 211 191c68 109 151 108 279 51 130-58 235 12 332 109',
        'M14 330C80 234 156 172 198 228c80 107 163 114 292 58 132-57 228 9 303 83',
        'M66 389c48-78 100-132 143-94 101 90 176 91 292 43 121-49 205-3 269 59',
        'M150 444c29-48 62-77 95-52 80 61 166 60 258 25 94-37 154-8 204 33',
        'M-15 80C100-39 245-25 312 54c75 88 159 31 228 6 99-35 201-12 297 62',
      ].map((d, i) => <path key={i} d={d} />)}
    </svg>
  )
}

export function Button({ children, href, variant = 'primary', icon = 'auto', external = false, onClick }: {
  children: ReactNode
  href: string
  variant?: 'primary' | 'secondary' | 'light'
  icon?: IconName | 'auto' | 'none'
  external?: boolean
  onClick?: () => void
}) {
  const name: IconName | null = icon === 'none' ? null : icon === 'auto' ? (variant === 'secondary' ? 'arrow' : 'download') : icon
  return (
    <a href={href} className={`button button-${variant}`} onClick={onClick} {...(external ? { rel: 'noopener' } : {})}>
      {children}
      {name && <Icon name={name} />}
    </a>
  )
}

/* ---------- Animations d'apparition au défilement ---------- */

const reducedMotion = () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

let sharedObserver: IntersectionObserver | null = null
const watchers = new Map<Element, () => void>()

function watch(el: Element, onVisible: () => void, margin = '0px 0px -8% 0px') {
  if (typeof IntersectionObserver === 'undefined' || reducedMotion()) { onVisible(); return () => {} }
  if (!sharedObserver) {
    sharedObserver = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue
        const cb = watchers.get(e.target)
        if (cb) { watchers.delete(e.target); sharedObserver?.unobserve(e.target); cb() }
      }
    }, { rootMargin: margin, threshold: 0.12 })
  }
  watchers.set(el, onVisible)
  sharedObserver.observe(el)
  return () => { watchers.delete(el); sharedObserver?.unobserve(el) }
}

type RevealTag = 'div' | 'section' | 'article' | 'li' | 'figure' | 'p' | 'span' | 'h2' | 'small'

/** Fait apparaître son contenu (fondu + glissement) quand il entre à l'écran. */
export function Reveal({ as = 'div', delay = 0, variant, className = '', children, ...rest }: {
  as?: RevealTag
  delay?: number
  variant?: 'scale' | 'left'
  className?: string
  children?: ReactNode
  [key: string]: unknown
}) {
  const ref = useRef<HTMLElement>(null)
  useEffect(() => {
    const el = ref.current
    return el ? watch(el, () => el.classList.add('is-in')) : undefined
  }, [])
  const cls = `reveal ${variant ? `reveal-${variant}` : ''} ${className}`.trim()
  return createElement(as, { ref, className: cls, style: { '--d': `${delay}s` }, ...rest }, children)
}

/** Chiffre qui défile jusqu'à sa valeur quand il devient visible. */
export function Counter({ to, decimals = 0 }: { to: number; decimals?: number }) {
  const ref = useRef<HTMLSpanElement>(null)
  const format = (v: number) => v.toLocaleString('fr-FR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
  useLayoutEffect(() => {
    const el = ref.current
    if (!el || reducedMotion()) return
    el.textContent = format(0)
    let raf = 0
    const stop = watch(el, () => {
      const start = performance.now(), dur = 1700
      const tick = (now: number) => {
        const t = Math.min(1, (now - start) / dur)
        el.textContent = format(to * (1 - Math.pow(1 - t, 3)))
        if (t < 1) raf = requestAnimationFrame(tick)
      }
      raf = requestAnimationFrame(tick)
    })
    return () => { stop(); cancelAnimationFrame(raf) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [to, decimals])
  return <span ref={ref}>{format(to)}</span>
}

/* ---------- Accordéon accessible ---------- */

export function Accordion({ title, children, defaultOpen = false }: { title: string; children: ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  const id = useId()
  return (
    <div className={`accordion ${open ? 'open' : ''}`}>
      <button type="button" aria-expanded={open} aria-controls={id} onClick={() => setOpen(!open)}>
        <span>{title}</span><Icon name="chevron" />
      </button>
      <div id={id} role="region" aria-label={title} className="accordion-content"><div>{children}</div></div>
    </div>
  )
}
