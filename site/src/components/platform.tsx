import { useSyncExternalStore } from 'react'
import type { KeyboardEvent, ReactNode } from 'react'

/* Choix du système (Windows / Mac), partagé entre l'accueil et le guide d'installation. */

export type Platform = 'windows' | 'mac'

const guess = (): Platform => {
  if (typeof navigator === 'undefined') return 'windows'
  const ua = `${navigator.userAgent} ${navigator.platform ?? ''}`
  return /Macintosh|MacIntel|MacPPC/i.test(ua) && !/iPhone|iPad|iPod|Mobile/i.test(ua) ? 'mac' : 'windows'
}

let current: Platform = guess()
const listeners = new Set<() => void>()

export function setPlatform(p: Platform) {
  if (p === current) return
  current = p
  listeners.forEach((l) => l())
}

export function usePlatform(): Platform {
  return useSyncExternalStore(
    (cb) => { listeners.add(cb); return () => { listeners.delete(cb) } },
    () => current,
    () => 'windows',
  )
}

const tabs: { id: Platform; label: string }[] = [
  { id: 'windows', label: 'Windows' },
  { id: 'mac', label: 'Mac' },
]

/** Onglets accessibles : flèches gauche/droite, Début, Fin. */
export function PlatformTabs({ idBase, light = false }: { idBase: string; light?: boolean }) {
  const platform = usePlatform()
  const onKey = (e: KeyboardEvent<HTMLButtonElement>) => {
    const i = tabs.findIndex((t) => t.id === platform)
    let next = i
    if (e.key === 'ArrowRight') next = (i + 1) % tabs.length
    else if (e.key === 'ArrowLeft') next = (i - 1 + tabs.length) % tabs.length
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = tabs.length - 1
    else return
    e.preventDefault()
    setPlatform(tabs[next].id)
    document.getElementById(`${idBase}-tab-${tabs[next].id}`)?.focus()
  }
  return (
    <div className={`platform-tabs ${light ? 'is-light' : ''}`} role="tablist" aria-label="Choisissez votre ordinateur">
      {tabs.map((t) => (
        <button key={t.id} type="button" role="tab" id={`${idBase}-tab-${t.id}`} aria-selected={platform === t.id}
          aria-controls={`${idBase}-panel`} tabIndex={platform === t.id ? 0 : -1}
          onClick={() => setPlatform(t.id)} onKeyDown={onKey}>{t.label}</button>
      ))}
    </div>
  )
}

/** Contenu de l'onglet actif (un seul panneau, relié à l'onglet sélectionné). */
export function PlatformPanel({ idBase, children, className = '' }: { idBase: string; children: ReactNode; className?: string }) {
  const platform = usePlatform()
  return <div role="tabpanel" id={`${idBase}-panel`} aria-labelledby={`${idBase}-tab-${platform}`} className={className}>{children}</div>
}
