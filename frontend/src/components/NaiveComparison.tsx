import type { StateOut } from '../types'

export default function NaiveComparison({ state }: { state: StateOut }) {
  const unit = state.resource.unit
  return (
    <div className="grid grid-cols-2 gap-4 font-mono text-sm">
      <div>
        <h3 className="mb-2 font-sans text-muted">Central Earth server</h3>
        {Object.entries(state.naive_allocations).map(([id, kg]) => (
          <div key={id}>{id}: {kg} {unit}</div>
        ))}
      </div>
      <div>
        <h3 className="mb-2 font-sans text-muted">Lightcone</h3>
        {Object.entries(state.nodes.earth.allocations).map(([id, kg]) => (
          <div key={id}>{id}: {kg} {unit}</div>
        ))}
      </div>
    </div>
  )
}
