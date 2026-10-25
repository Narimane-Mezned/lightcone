import type { Receipt, RequestOut, StateOut } from '../types'

interface Props {
  state: StateOut
}

const POLICY_NAME: Record<string, string> = {
  needs: 'Needs-aware (AI-compiled constraints)',
  lottery: 'Verifiable lottery',
  prorata: 'Pro-rata',
  priority: 'Priority classes',
}

function Comparison({ receipt, byId, unit }: { receipt: Receipt; byId: Record<string, RequestOut>; unit: string }) {
  const met = (id: string, now: number, later: number) => now + later >= (byId[id]?.min_qty ?? 0) - 1e-9
  return (
    <table className="w-full text-left font-mono text-xs">
      <thead className="text-muted">
        <tr>
          <th className="py-1 font-normal">request</th>
          <th className="font-normal">needs</th>
          <th className="font-normal text-text">Lightcone now</th>
          <th className="font-normal text-signal">next ship</th>
          <th className="font-normal">lottery</th>
        </tr>
      </thead>
      <tbody>
        {receipt.tie.map((id) => {
          const r = byId[id]
          const now = receipt.allocation[id] ?? 0
          const later = receipt.deferred[id] ?? 0
          const lot = receipt.lottery.allocation[id] ?? 0
          return (
            <tr key={id} className="border-t border-line">
              <td className="py-1">
                <span className={r?.node === 'earth' ? 'text-earth' : 'text-mars'}>{id}</span>{' '}
                <span className="text-muted">{r?.actor}</span>
              </td>
              <td className="text-muted">
                {r ? `${r.min_qty}–${r.qty} ${unit}${r.can_defer ? ', can wait' : ''}` : ''}
              </td>
              <td className={met(id, now, later) ? 'text-final' : 'text-mars'}>
                {now} {unit} {met(id, now, later) ? '✓' : '✗'}
              </td>
              <td className="text-signal">{later ? `+${later} ${unit}` : '—'}</td>
              <td className={met(id, lot, 0) ? 'text-muted' : 'text-mars'}>
                {lot} {unit} {met(id, lot, 0) ? '✓' : '✗'}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

export default function Receipts({ state }: Props) {
  const byId: Record<string, RequestOut> = {}
  for (const r of [...state.nodes.earth.log, ...state.nodes.mars.log]) byId[r.id] = r

  if (state.receipts.length === 0) {
    return (
      <p className="text-muted">
        No true tie yet. Book from Earth and Mars within one light delay — before either side's news can arrive.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {state.receipts.map((rc) => (
        <article key={rc.tie.join('-')} className="flex flex-col gap-3 rounded border border-line bg-ink p-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded bg-tie/20 px-2 py-0.5 text-xs font-bold text-tie">TRUE TIE</span>
            <span className="font-mono text-sm">{rc.tie.join(' ⟷ ')}</span>
            <span className="text-xs text-muted">{POLICY_NAME[rc.policy] ?? rc.policy}</span>
            {rc.policy === 'needs' && (
              <span className="ml-auto text-sm">
                needs met <span className="text-final">{rc.needs_met}/{rc.tie.length}</span>
                <span className="text-muted"> · lottery {rc.lottery.needs_met}/{rc.tie.length}</span>
              </span>
            )}
          </div>

          <p className="leading-relaxed">{rc.narrative}</p>
          <p className="text-xs text-muted">
            {rc.narrative_source === 'llm'
              ? 'Written by AI from the decision data · every number checked against the decision before display'
              : 'Template explanation (AI offline)'}
          </p>

          {rc.policy === 'needs' && <Comparison receipt={rc} byId={byId} unit={state.resource.unit} />}

          <details className="text-xs text-muted">
            <summary className="cursor-pointer">Proof details</summary>
            <p className="mt-2 leading-relaxed">{rc.explanation}</p>
            <p className="mt-1 font-mono">
              seed {rc.seed.slice(0, 16)}… · order {rc.order.join(' → ')}
            </p>
          </details>
        </article>
      ))}
    </div>
  )
}
