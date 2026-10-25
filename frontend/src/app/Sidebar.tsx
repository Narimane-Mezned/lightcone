import { NavLink } from 'react-router-dom'
import { DASHBOARD, SECTIONS } from './routes'

const link = ({ isActive }: { isActive: boolean }) =>
  `block rounded px-3 py-2 text-sm ${isActive ? 'bg-panel text-text' : 'text-muted hover:text-text'}`

export default function Sidebar() {
  return (
    <nav className="flex w-52 shrink-0 flex-col gap-1 border-r border-line p-3">
      <NavLink to="/" end className={link}>{DASHBOARD.label}</NavLink>
      {SECTIONS.map((r) => (
        <NavLink key={r.path} to={`/${r.path}`} className={link}>{r.label}</NavLink>
      ))}
    </nav>
  )
}
