import type { LinkInfo, StateOut } from '../types'

interface Props {
  link: LinkInfo | null
  state: StateOut | null
  date: string
  onDateChange: (date: string) => void
}

const fmt = (s: number) => {
  const t = Math.round(s)
  const h = String(Math.floor(t / 3600)).padStart(2, '0')
  const m = String(Math.floor((t % 3600) / 60)).padStart(2, '0')
  const sec = String(t % 60).padStart(2, '0')
  return `${h}:${m}:${sec}`
}

const minSec = (s: number) => `${Math.floor(s / 60)} m ${String(Math.round(s % 60)).padStart(2, '0')} s`

export default function LinkBar({ link, state, date }: Props) {
  const oneWay = state?.one_way_s ?? link?.one_way_s ?? 0
  const conjunction = state?.conjunction ?? link?.conjunction ?? false

  return (
    <header
      className={`flex flex-wrap items-center justify-between gap-3 rounded border px-4 py-3 ${
        conjunction ? 'border-signal bg-panel' : 'border-line bg-panel'
      }`}
    >
      <div className="flex items-baseline gap-3">
        <span className="text-lg font-semibold tracking-wide">Lightcone</span>
        <span className="text-sm text-muted">Fair "first" for a multi-planet world</span>
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 font-mono text-sm">
        <span>
          <span className="text-earth">EARTH</span>
          <span className="text-muted"> ⟷ </span>
          <span className="text-mars">MARS</span>
        </span>
        <span>{link ? `${link.distance_au.toFixed(3)} AU` : '…'}</span>
        <span>
          <span className="text-muted">light delay </span>
          <span className="text-signal">{minSec(oneWay)}</span>
        </span>
        <span>
          <span className="text-muted">round trip </span>
          {minSec(2 * oneWay)}
        </span>
        <span className="text-muted">date {date}</span>
        <span className="text-muted">sim ×{state?.compression ?? 60}</span>
        <span>
          <span className="text-muted">t = </span>
          {fmt(state?.sim_t ?? 0)}
        </span>
      </div>

      {conjunction && (
        <div className="w-full text-sm text-signal">
          Solar conjunction: the Sun is within 2° of Mars. Finality is paused until the link returns.
        </div>
      )}
    </header>
  )
}
