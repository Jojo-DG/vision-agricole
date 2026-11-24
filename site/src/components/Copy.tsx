import { useState } from 'react'
import { LINKS, MAC } from '../data'
import type { Platform } from './platform'
import { Icon } from './ui'

/** Copie un texte dans le presse-papiers ; renvoie true si c'est réussi. */
function useCopy(text: string) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch { /* copie impossible : le texte reste sélectionnable à la main */ }
  }
  return { copied, copy }
}

/** Commande à copier-coller (fond sombre). */
export function CodeBlock({ code, label }: { code: string; label: string }) {
  const { copied, copy } = useCopy(code)
  return (
    <div className="code-copy">
      <pre className="code-block" aria-label={label} tabIndex={0}><code>{code}</code></pre>
      <button type="button" onClick={copy} aria-live="polite" aria-label={copied ? 'Commande copiée' : `Copier la commande : ${label}`}>
        <Icon name={copied ? 'check' : 'copy'} size={16} />{copied ? 'Copié' : 'Copier'}
      </button>
    </div>
  )
}

/** Empreinte SHA-256 du fichier publié, avec bouton de copie et conseil de vérification. */
export function Checksum({ platform = 'windows' }: { platform?: Platform }) {
  const mac = platform === 'mac'
  const sha = mac ? MAC.sha256 : LINKS.sha256
  const { copied, copy } = useCopy(sha)
  return (
    <>
      <div className="checksum">
        <div><span>Empreinte SHA-256</span><code>{sha}</code></div>
        <button type="button" onClick={copy} aria-live="polite"><Icon name={copied ? 'check' : 'copy'} size={16} />{copied ? 'Copié' : 'Copier'}</button>
      </div>
      {mac ? (
        <>
          <p className="verify-tip">Pour vérifier le fichier, dans le Terminal : <code>{MAC.verifyCmd}</code>. Le résultat doit être identique.</p>
          <a className="virus-link" href={MAC.virustotal} rel="noopener">Voir l’analyse VirusTotal <Icon name="arrow" /></a>
        </>
      ) : (
        <>
          <p className="verify-tip">Sous Windows, dans l’Invite de commandes : <code>certutil -hashfile Vision.Agricole.exe SHA256</code> (avec le nom du fichier téléchargé). Le résultat doit être identique.</p>
          <a className="virus-link" href={LINKS.virustotal} rel="noopener">Voir l’analyse VirusTotal <Icon name="arrow" /></a>
        </>
      )}
    </>
  )
}
