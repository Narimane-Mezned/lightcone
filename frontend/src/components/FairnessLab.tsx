import { useState } from 'react'
import { api } from '../api'
import type { FairnessOut } from '../types'

interface Props {
  date: string
}

export default function FairnessLab({ date }: Props) {
  const [result, setResult] = useState<FairnessOut | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    setBusy(true)
    setError(null)
    try {
      setResult(await api.fairness(date, 10000))
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  const bars = result
    ? [
        { label: 'Central server on Earth', value: result.earth_server_mars_win, color: 'bg-earth' },
        { label: 'Central server on Mars', value: result.mars_server_mars_win, color: 'bg-mars' },
        { label: 'Lightcone', value: result.lightcone_mars_win, color: 'bg-tie' },
      ]
    : []

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-4">
        <button
          onClick={run}
          disabled={busy}
          className="rounded bg-tie px-4 py-2 font-semibold text-ink disabled:opacity-40"
        >
          {busy ? 'Simulating…' : 'Run 10,000 races'}
        </button>
        <p className="text-xs text-muted">
          One Earth and one Mars buyer book the same item at random times within 30 minutes, with the real light delay for {date}. How often does Mars win?
        </p>
      </div>

      {error && <p className="text-xs text-mars">{error}</p>}

      {result && (
        <div className="flex flex-col gap-3">
          {bars.map((b) => (
            <div key={b.label} className="grid grid-cols-[200px_1fr_64px] items-center gap-3 text-sm">
              <span className="text-muted">{b.label}</span>
              <div className="h-5 rounded bg-ink">
                <div className={`h-5 rounded ${b.color}`} style={{ width: `${b.value * 100}%` }} />
              </div>
              <span className="text-right font-mono">{Math.round(b.value * 100)}%</span>
            </div>
          ))}
          <p className="text-sm">
            <span className="text-tie">{Math.round(result.tie_rate * 100)}%</span> of these races were true ties: neither buyer could have known about the other.
            A central server turns every one of them into an automatic win for its own planet.
          </p>
          <p className="text-xs text-muted">
            Monte Carlo simulation, {result.trials.toLocaleString()} trials, fixed seed (reproducible). Ties resolved by the verifiable lottery.
          </p>
        </div>
      )}
    </div>
  )
}
