import { useState } from 'react'
import { api } from '../api'
import type { IntentOut, NeedSpec, NodeId, Priority, StateOut } from '../types'

interface Props {
  node: NodeId
  state: StateOut
  onBooked: () => void
}

const DEFAULTS: Record<NodeId, { actor: string; text: string; needs: NeedSpec }> = {
  earth: {
    actor: 'Helios Freight',
    text: 'We would like 400 kg of cargo space, but we can wait for the next ship if needed.',
    needs: { min_qty: 400, max_qty: 400, category: 'commercial', can_defer: true, summary: '' },
  },
  mars: {
    actor: 'Jezero Clinic',
    text: 'We need at least 250 kg of medical supplies before the March launch window. Anything above 300 kg is useless.',
    needs: { min_qty: 250, max_qty: 300, category: 'medical', can_defer: false, summary: '' },
  },
}

export default function NodePanel({ node, state, onBooked }: Props) {
  const [actor, setActor] = useState(DEFAULTS[node].actor)
  const [text, setText] = useState(DEFAULTS[node].text)
  const [needs, setNeeds] = useState<NeedSpec>(DEFAULTS[node].needs)
  const [intent, setIntent] = useState<IntentOut | null>(null)
  const [thinking, setThinking] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const view = state.nodes[node]
  const isEarth = node === 'earth'
  const other = isEarth ? 'Mars' : 'Earth'
  const accent = isEarth ? 'text-earth' : 'text-mars'
  const button = isEarth ? 'bg-earth' : 'bg-mars'
  const unit = state.resource.unit
  const byId = Object.fromEntries(view.log.map((r) => [r.id, r]))
  const valid = needs.max_qty > 0 && needs.min_qty >= 0 && needs.min_qty <= needs.max_qty && actor.trim().length > 0
  const risk = Math.round(view.tie_risk * 100)

  const understand = async () => {
    setThinking(true)
    setError(null)
    try {
      const out = await api.intent({ node, actor, text })
      setIntent(out)
      setNeeds(out.needs)
    } catch (e) {
      setError(String(e))
    } finally {
      setThinking(false)
    }
  }

  const book = async () => {
    setBusy(true)
    setError(null)
    try {
      await api.request({ node, actor, qty: needs.max_qty, priority: needs.category, needs, text })
      onBooked()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  const field = 'rounded border border-line bg-ink px-2 py-1'

  return (
    <aside className="flex flex-col gap-4 rounded border border-line bg-panel p-4">
      <div className="flex items-baseline justify-between">
        <h2 className={`text-lg font-semibold ${accent}`}>{isEarth ? 'Earth node' : 'Mars node'}</h2>
        <span className="font-mono text-xs text-muted">vc [{view.vc.join(', ')}]</span>
      </div>

      <div className="flex flex-col gap-2 text-sm">
        <input className={field} value={actor} onChange={(e) => setActor(e.target.value)} aria-label="Requester" />
        <textarea
          className={`${field} min-h-[84px] resize-y leading-snug`}
          value={text}
          onChange={(e) => setText(e.target.value)}
          aria-label="Describe your need"
        />
        <button
          onClick={understand}
          disabled={thinking || !text.trim()}
          className="rounded border border-tie px-3 py-1.5 text-tie disabled:opacity-40"
        >
          {thinking ? 'Reading your need…' : 'Understand my need'}
        </button>

        <div className="rounded border border-line bg-ink p-2">
          <div className="mb-1 flex flex-col text-xs">
            <span className="text-muted">Constraints sent with the request</span>
            {intent && (
              <span className={intent.source === 'llm' ? 'text-tie' : 'text-signal'}>
                {intent.source === 'llm' ? `understood by AI · ${intent.model}` : 'understood by rule-based fallback'}
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2">
            <label className="flex flex-col text-xs text-muted">
              min ({unit})
              <input
                type="number"
                className={`${field} font-mono text-text`}
                value={needs.min_qty}
                onChange={(e) => setNeeds({ ...needs, min_qty: Number(e.target.value) })}
              />
            </label>
            <label className="flex flex-col text-xs text-muted">
              max ({unit})
              <input
                type="number"
                className={`${field} font-mono text-text`}
                value={needs.max_qty}
                onChange={(e) => setNeeds({ ...needs, max_qty: Number(e.target.value) })}
              />
            </label>
            <select
              className={`${field} text-xs`}
              value={needs.category}
              onChange={(e) => setNeeds({ ...needs, category: e.target.value as Priority })}
            >
              <option value="medical">Medical</option>
              <option value="science">Science</option>
              <option value="commercial">Commercial</option>
            </select>
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={needs.can_defer}
                onChange={(e) => setNeeds({ ...needs, can_defer: e.target.checked })}
              />
              can wait for next ship
            </label>
          </div>
          {intent?.needs.summary && <p className="mt-2 text-xs italic text-muted">"{intent.needs.summary}"</p>}
          {intent?.notes.map((n) => (
            <p key={n} className="mt-1 text-xs text-signal">
              {n}
            </p>
          ))}
        </div>

        <p className="text-xs text-muted">
          Tie-risk forecast: <span className={risk >= 30 ? 'text-tie' : 'text-text'}>{risk}%</span> that a request from{' '}
          {other} you cannot see yet collides with yours.
        </p>

        <button
          onClick={book}
          disabled={busy || !valid}
          className={`rounded px-3 py-2 font-semibold text-ink disabled:opacity-40 ${button}`}
        >
          {busy ? 'Booking…' : `Book from ${isEarth ? 'Earth' : 'Mars'}`}
        </button>
        {error && <p className="text-xs text-mars">{error}</p>}
      </div>

      <div className="flex flex-col gap-1 text-sm">
        <h3 className="text-muted">What this node knows</h3>
        {Object.keys(view.allocations).length === 0 ? (
          <p className="text-muted">No requests seen yet.</p>
        ) : (
          Object.entries(view.allocations).map(([id, kg]) => {
            const r = byId[id]
            return (
              <div key={id} className="flex justify-between gap-2 font-mono text-xs">
                <span className="truncate">
                  <span className={r?.node === 'earth' ? 'text-earth' : 'text-mars'}>{id}</span>{' '}
                  <span className="text-muted">{r?.actor}</span>
                </span>
                <span className={`shrink-0 ${r?.status === 'final' ? 'text-final' : ''}`}>
                  {kg} {unit}
                  {view.deferred[id] ? <span className="text-signal"> +{view.deferred[id]} next</span> : null}
                </span>
              </div>
            )
          })
        )}
      </div>

      <div className="mt-auto font-mono text-xs text-muted">
        settlement hash <span className="text-text">{view.hash.slice(0, 12)}</span>
      </div>
    </aside>
  )
}
