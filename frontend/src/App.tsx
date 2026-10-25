import { useEffect, useState } from 'react'
import { api } from './api'
import { mockState } from './mock/state'
import type { LinkInfo, StateOut } from './types'
import LinkBar from './components/LinkBar'
import NodePanel from './components/NodePanel'
import Spacetime from './components/Spacetime'
import Receipts from './components/Receipts'
import PolicyPicker from './components/PolicyPicker'
import FairnessLab from './components/FairnessLab'

const USE_MOCK = false
const DEFAULT_DATE = '2040-01-01'
type Tab = 'receipts' | 'policy' | 'fairness' | 'naive'

export default function App() {
  const [state, setState] = useState<StateOut | null>(USE_MOCK ? mockState : null)
  const [link, setLink] = useState<LinkInfo | null>(null)
  const [date, setDate] = useState(DEFAULT_DATE)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('receipts')

  useEffect(() => {
    if (USE_MOCK) return
    api.link(date).then(setLink).catch((e) => setError(String(e)))
  }, [date])

  useEffect(() => {
    if (USE_MOCK) return
    const tick = () =>
      api
        .state()
        .then((s) => {
          setState(s)
          setError(null)
        })
        .catch((e) => setError(String(e)))
    tick()
    const id = setInterval(tick, 500)
    return () => clearInterval(id)
  }, [])

  const refresh = () => api.state().then(setState).catch((e) => setError(String(e)))

  return (
    <div className="min-h-screen flex flex-col gap-4 p-4">
      <LinkBar link={link} state={state} date={date} onDateChange={setDate} />
      {error && (
        <div className="rounded border border-mars px-3 py-2 text-sm text-mars">
          Backend unreachable: {error}
        </div>
      )}
      {!state ? (
        <p className="text-muted">Loading…</p>
      ) : (
        <>
          <div className="grid grid-cols-[280px_1fr_280px] gap-4">
            <NodePanel node="earth" state={state} onBooked={refresh} />
            <Spacetime state={state} />
            <NodePanel node="mars" state={state} onBooked={refresh} />
          </div>
          <nav className="flex gap-2">
            {(['receipts', 'policy', 'fairness', 'naive'] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`rounded px-3 py-1 text-sm ${tab === t ? 'bg-panel text-text' : 'text-muted'}`}
              >
                {t === 'receipts' ? 'Receipts' : t === 'policy' ? 'Policy' : t === 'fairness' ? 'Fairness Lab' : 'Naive vs Lightcone'}
              </button>
            ))}
          </nav>
          <section className="rounded bg-panel p-4">
            {tab === 'receipts' && <Receipts state={state} />}
            {tab === 'policy' && <PolicyPicker state={state} date={date} onDateChange={setDate} onChanged={setState} />}
            {tab === 'fairness' && <FairnessLab date={date} />}
            {tab === 'naive' && (
              <div className="grid grid-cols-2 gap-4 font-mono text-sm">
                <div>
                  <h3 className="mb-2 font-sans text-muted">Central Earth server</h3>
                  {Object.entries(state.naive_allocations).map(([id, kg]) => (
                    <div key={id}>{id}: {kg} {state.resource.unit}</div>
                  ))}
                </div>
                <div>
                  <h3 className="mb-2 font-sans text-muted">Lightcone</h3>
                  {Object.entries(state.nodes.earth.allocations).map(([id, kg]) => (
                    <div key={id}>{id}: {kg} {state.resource.unit}</div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}
