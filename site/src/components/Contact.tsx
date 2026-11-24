import { CONTACT } from '../data'
import { Icon } from './ui'

/** Adresse e-mail et téléphone pour poser une question. */
export function Contact({ className = '' }: { className?: string }) {
  return (
    <ul className={`contact-list ${className}`.trim()}>
      <li><Icon name="mail" size={18} /><a href={`mailto:${CONTACT.email}`}>{CONTACT.email}</a></li>
      <li><Icon name="phone" size={18} /><a href={`tel:${CONTACT.tel}`}>{CONTACT.phone}</a></li>
    </ul>
  )
}
