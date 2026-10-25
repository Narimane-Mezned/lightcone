import { useState } from 'react'
import { api } from '../api'
import type { Policy, StateOut } from '../types'

interface Props {
  state: StateOut
  date: string
  onDateChange: (date: string) => void
  onChanged: (state: StateOut) => void
}

const POLICIES: { id: Policy; name: string; text: string }[] = [
  { id: 'needs', name: 'Needs-aware', text: 'Minimums first (cannot-wait before can-wait, then medical > science > commercial), rest shared fairly, next-ship guarantee for flexible requesters.' },
  { id: 'lottery', name: 'Verifiable lottery', text: 'Random order anyone can recompute from the requests themselves.' },
  { id: 'prorata', name: 'Pro-rata', text: 'Share capacity in proportion to what each requested.' },
  { id: 'priority', name: 'Priority classes', text: 'Medical > science > commercial, lottery inside a class.' },
]

export default function PolicyPicker({ state, date, onDateChange, onChanged }: Props) {
  const [policy, setPolicy] = useState<Policy>(state.policy)
  const [day, setDay] = useState(date)
  const [capacity, setCapacity] = useState(state.resource.capacity)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async (action: 'apply' | 'reset') => {
    setBusy(true)
    setError(null)
    try {
      const next =
        action === 'apply'
          ? await api.scenario({ date: day, compression: state.compression, resource: { ...state.resource, capacity }, policy })
          : await api.reset()
      onChanged(next)
      if (action === 'apply') onDateChange(day)
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-[2fr_1fr]">
      <div className="flex flex-col gap-2">
        <h3 className="text-sm text-muted">Fairness rule for true ties (chosen in advance by the operator)</h3>
        {POLICIES.map((p) => (
          <label
            key={p.id}
            className={`flex cursor-pointer gap-3 rounded border p-2 ${policy === p.id ? 'border-tie' : 'border-line'}`}
          >
            <input type="radio" name="policy" checked={policy === p.id} onChange={() => setPolicy(p.id)} />
            <span>
              <span className="font-semibold">{p.name}</span>
              <span className="block text-xs text-muted">{p.text}</span>
            </span>
          </label>
        ))}
      </div>

      <div className="flex flex-col gap-3 text-sm">
        <label className="flex flex-col gap-1">
          <span className="text-muted">Scenario date (sets the real light delay)</span>
          <input
            type="date"
            min="1900-01-01"
            max="2049-12-31"
            className="rounded border border-line bg-ink px-2 py-1 font-mono"
            value={day}
            onChange={(e) => setDay(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-muted">{state.resource.name} ({state.resource.unit})</span>
          <input
            type="number"
            min={1}
            className="rounded border border-line bg-ink px-2 py-1 font-mono"
            value={capacity}
            onChange={(e) => setCapacity(Number(e.target.value))}
          />
        </label>
        <div className="flex gap-2">
          <button
            onClick={() => run('apply')}
            disabled={busy || capacity <= 0}
            className="flex-1 rounded bg-tie px-3 py-2 font-semibold text-ink disabled:opacity-40"
          >
            Apply
          </button>
          <button
            onClick={() => run('reset')}
            disabled={busy}
            className="flex-1 rounded border border-line px-3 py-2 disabled:opacity-40"
          >
            Reset
          </button>
        </div>
        <p className="text-xs text-muted">Apply and Reset clear current bookings.</p>
        <p className="text-xs text-muted">
          AI: {state.ai_enabled ? <span className="text-tie">online</span> : <span className="text-signal">offline (rule-based fallback)</span>}
        </p>
        {error && <p className="text-xs text-mars">{error}</p>}
      </div>
    </div>
  )
}
