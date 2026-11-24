import { useCallback, useEffect, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import { gallery, maps } from '../data'
import { Icon } from './ui'

/* ---------- Comparateur avant / après (vraies données du vol test) ---------- */

export function BeforeAfter() {
  const [position, setPosition] = useState(52)
  const wrap = useRef<HTMLDivElement>(null)
  const touched = useRef(false)

  // Petite démonstration au premier affichage : le curseur balaie l'image une fois.
  useEffect(() => {
    const el = wrap.current
    if (!el || window.matchMedia('(prefers-reduced-motion: reduce)').matches || typeof IntersectionObserver === 'undefined') return
    let raf = 0
    const io = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return
      io.disconnect()
      const start = performance.now(), dur = 3200
      const tick = (now: number) => {
        if (touched.current) return
        const t = Math.min(1, (now - start) / dur)
        // 52 -> 90 -> 14 -> 52
        const v = t < .3 ? 52 + 38 * ease(t / .3) : t < .75 ? 90 - 76 * ease((t - .3) / .45) : 14 + 38 * ease((t - .75) / .25)
        setPosition(v)
        if (t < 1) raf = requestAnimationFrame(tick)
      }
      raf = requestAnimationFrame(tick)
    }, { threshold: 0.45 })
    io.observe(el)
    return () => { io.disconnect(); cancelAnimationFrame(raf) }
  }, [])

  return (
    <div className="comparison" ref={wrap} style={{ '--pos': `${position}%` } as CSSProperties}>
      <div className="comparison-layer">
        <img src={maps.afterZoning} width="900" height="1050" loading="lazy" alt="Carte de zonage de la parcelle : rouge pour les zones à traiter en priorité, vert pour les zones saines, gris pour les surfaces exclues." />
      </div>
      <div className="comparison-layer comparison-before" aria-hidden="true">
        <img src={maps.beforePhotos} width="900" height="1050" loading="lazy" alt="" />
      </div>
      <div className="comparison-label label-before">Vos photos</div>
      <div className="comparison-label label-after">Zonage</div>
      <div className="comparison-divider" aria-hidden="true" />
      <input
        type="range" min="4" max="96" step="0.5" value={position}
        aria-label="Comparer les photos assemblées et le zonage de la parcelle"
        aria-valuetext={`${Math.round(position)} % de photos visibles`}
        onPointerDown={() => { touched.current = true }}
        onKeyDown={() => { touched.current = true }}
        onChange={(e) => { touched.current = true; setPosition(Number(e.target.value)) }}
      />
      <div className="comparison-handle" aria-hidden="true"><span><Icon name="chevron" /><Icon name="chevron" /></span></div>
    </div>
  )
}

const ease = (t: number) => (t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2)

/* ---------- Galerie de captures : défilement, points, visionneuse ---------- */

export function Gallery() {
  const track = useRef<HTMLDivElement>(null)
  const dialog = useRef<HTMLDialogElement>(null)
  const [active, setActive] = useState(0)
  const [zoom, setZoom] = useState<number | null>(null)

  const onScroll = useCallback(() => {
    const el = track.current
    if (!el) return
    const figs = Array.from(el.children) as HTMLElement[]
    let best = 0, dist = Infinity
    figs.forEach((f, i) => {
      const d = Math.abs(f.offsetLeft - el.scrollLeft - (parseFloat(getComputedStyle(el).paddingLeft) || 0))
      if (d < dist) { dist = d; best = i }
    })
    setActive(best)
  }, [])

  const goTo = (i: number) => {
    const el = track.current
    const fig = el?.children[i] as HTMLElement | undefined
    if (!el || !fig) return
    const pad = parseFloat(getComputedStyle(el).paddingLeft) || 0
    el.scrollTo({ left: fig.offsetLeft - pad, behavior: 'smooth' })
  }

  useEffect(() => {
    const d = dialog.current
    if (!d) return
    if (zoom !== null && !d.open) d.showModal()
    if (zoom === null && d.open) d.close()
  }, [zoom])

  const current = zoom !== null ? gallery[zoom] : null

  return (
    <>
      <div className="gallery-track" ref={track} onScroll={onScroll} role="region" aria-label="Captures de l’application" tabIndex={0}>
        {gallery.map((g, i) => (
          <figure key={g.shot.src}>
            <div className="shot">
              <button type="button" className="zoom" onClick={() => setZoom(i)} aria-label={`Agrandir la capture : ${g.caption}`}>
                <img src={g.shot.src} width={g.shot.w} height={g.shot.h} loading="lazy" alt={g.alt} />
              </button>
            </div>
            <figcaption>{g.caption}</figcaption>
          </figure>
        ))}
      </div>
      <div className="container">
        <div className="gallery-nav">
          <button type="button" aria-label="Capture précédente" onClick={() => goTo(Math.max(0, active - 1))}><span style={{ display: 'grid', transform: 'rotate(180deg)' }}><Icon name="arrow" /></span></button>
          <button type="button" aria-label="Capture suivante" onClick={() => goTo(Math.min(gallery.length - 1, active + 1))}><Icon name="arrow" /></button>
        </div>
        <div className="gallery-dots">
          {gallery.map((g, i) => (
            <button key={g.shot.src} type="button" className={i === active ? 'active' : ''} aria-label={`Aller à la capture ${i + 1} sur ${gallery.length}`}
              aria-current={i === active} onClick={() => goTo(i)} />
          ))}
        </div>
      </div>
      <dialog ref={dialog} className="lightbox" aria-label="Capture agrandie" onClose={() => setZoom(null)}
        onClick={(e) => { if (e.target === dialog.current) setZoom(null) }}>
        {current && (
          <div>
            <button type="button" className="close" aria-label="Fermer l’image" onClick={() => setZoom(null)}><Icon name="x" /></button>
            <img src={current.shot.src} alt={current.alt} />
            <p>{current.caption}</p>
          </div>
        )}
      </dialog>
    </>
  )
}
