import { useEffect, useRef, useState } from 'react'
import { Footer, Header, pageFromHash, takePendingSection } from './components/Chrome'
import type { Page } from './components/Chrome'
import Home from './pages/Home'
import History from './pages/History'
import Technical from './pages/Technical'

const titles: Record<Page, string> = {
  home: 'Vision Agricole – De vos photos de drone à un rapport clair pour votre parcelle',
  histoire: 'Notre histoire – Vision Agricole',
  techniciens: 'Pour les techniciens – Vision Agricole',
}

function scrollToSection(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

export default function App() {
  const [page, setPage] = useState<Page>(() => pageFromHash(window.location.hash))
  const first = useRef(true)

  useEffect(() => {
    const onHash = () => setPage(pageFromHash(window.location.hash))
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  useEffect(() => {
    document.title = titles[page]
    if (first.current) {
      first.current = false
      // Arrivée directe sur une ancre (ex. #resultats) : le navigateur n'a pas encore le contenu.
      const id = window.location.hash.slice(1)
      if (page === 'home' && id) requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView())
      return
    }
    const target = page === 'home' ? takePendingSection() : null
    if (target) requestAnimationFrame(() => scrollToSection(target))
    else window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior })
  }, [page])

  return (
    <>
      <a className="skip-link" href={page === 'home' ? '#probleme' : '#contenu'}>Aller au contenu</a>
      <Header page={page} />
      {page === 'home' ? <main id="contenu-accueil"><Home /></main> : page === 'histoire' ? <History /> : <Technical />}
      <Footer page={page} />
    </>
  )
}
