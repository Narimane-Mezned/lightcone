import { Suspense } from 'react'
import { Outlet } from 'react-router-dom'
import { useLightcone } from '../context/LightconeContext'
import LinkBar from '../components/LinkBar'
import Sidebar from './Sidebar'

/** Layout commun : barre physique en haut, menu à gauche, page courante au centre. */
export default function AppShell() {
  const { link, state, date, setDate, error } = useLightcone()
  return (
    <div className="flex min-h-screen flex-col gap-4 p-4">
      <LinkBar link={link} state={state} date={date} onDateChange={setDate} />
      {error && (
        <div className="rounded border border-mars px-3 py-2 text-sm text-mars">Backend unreachable: {error}</div>
      )}
      <div className="flex flex-1 gap-4">
        <Sidebar />
        <main className="min-w-0 flex-1">
          <Suspense fallback={<p className="text-muted">Loading…</p>}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  )
}
