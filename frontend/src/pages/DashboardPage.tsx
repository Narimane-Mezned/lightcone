import { Link } from 'react-router-dom'
import { useLightcone } from '../context/LightconeContext'
import { SECTIONS } from '../app/routes'

const Stat = ({ label, value, tone = '' }: { label: string; value: string | number; tone?: string }) => (
  <div className="rounded border border-line bg-panel p-3">
    <div className="text-xs text-muted">{label}</div>
    <div className={`mt-1 font-mono text-lg ${tone}`}>{value}</div>
  </div>
)

export default function DashboardPage() {
  const { state } = useLightcone()
  if (!state) return <p className="text-muted">Loading…</p>

  const { earth, mars } = state.nodes
  const agree = earth.hash === mars.hash
  const pending = [...earth.log, ...mars.log].filter((r) => r.status !== 'final').length

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-4 gap-3">
        <Stat label="Resource" value={`${state.resource.capacity} ${state.resource.unit}`} />
        <Stat label="Policy" value={state.policy} />
        <Stat label="True ties" value={state.receipts.length} tone="text-tie" />
        <Stat label="Provisional requests" value={pending} tone="text-signal" />
        <Stat label="Earth requests" value={earth.log.length} tone="text-earth" />
        <Stat label="Mars requests" value={mars.log.length} tone="text-mars" />
        <Stat label="Settlement hashes" value={agree ? 'identical' : 'differ'} tone={agree ? 'text-final' : 'text-signal'} />
        <Stat label="Conjunction" value={state.conjunction ? 'active' : 'no'} />
      </div>

      <div className="grid grid-cols-3 gap-3">
        {SECTIONS.map((r) => (
          <Link key={r.path} to={`/${r.path}`} className="rounded border border-line bg-panel p-4 hover:border-tie">
            <div className="font-semibold">{r.label}</div>
            <div className="mt-1 text-sm text-muted">{r.description}</div>
          </Link>
        ))}
      </div>
    </div>
  )
}
