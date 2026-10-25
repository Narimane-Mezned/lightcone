import type { NodeId, RequestOut, StateOut } from '../types'

interface Props {
  state: StateOut
}

const W = 600
const H = 560
const TOP = 50
const BOTTOM = 20
const X: Record<NodeId, number> = { earth: 110, mars: 490 }
const COLOR = {
  earth: '#4EA8FF',
  mars: '#E0603A',
  signal: '#F5D27A',
  tie: '#B79CFF',
  final: '#3FB950',
  muted: '#8B93A7',
  line: '#252A35',
}

const fmt = (s: number) => {
  const t = Math.max(0, Math.round(s))
  const h = String(Math.floor(t / 3600)).padStart(2, '0')
  const m = String(Math.floor((t % 3600) / 60)).padStart(2, '0')
  const sec = String(t % 60).padStart(2, '0')
  return `${h}:${m}:${sec}`
}

export default function Spacetime({ state }: Props) {
  const byId = new Map<string, RequestOut>()
  for (const r of [...state.nodes.earth.log, ...state.nodes.mars.log]) byId.set(r.id, r)
  const requests = [...byId.values()]

  const minSpan = Math.max(4 * state.one_way_s, 600)
  const firstRequest = requests.length ? Math.min(...requests.map((r) => r.sim_t)) : Infinity
  const t0 = Math.max(0, Math.min(state.sim_t - minSpan, firstRequest - 0.08 * minSpan))
  const span = Math.max(minSpan, state.sim_t - t0)
  const y = (t: number) => TOP + ((t - t0) / span) * (H - TOP - BOTTOM)

  const tied = new Set(state.receipts.flatMap((rc) => rc.tie))

  const ticks: number[] = []
  const step = span / 4
  for (let i = 0; i <= 4; i++) ticks.push(t0 + i * step)

  return (
    <div className="rounded border border-line bg-panel p-2">
      <svg viewBox={`0 0 ${W} ${H}`} className="h-[560px] w-full">
        <defs>
          <clipPath id="plot">
            <rect x={0} y={TOP - 10} width={W} height={H - TOP + 10} />
          </clipPath>
        </defs>

        <text x={X.earth} y={24} textAnchor="middle" fill={COLOR.earth} fontSize={14} fontWeight={600}>
          EARTH
        </text>
        <text x={X.mars} y={24} textAnchor="middle" fill={COLOR.mars} fontSize={14} fontWeight={600}>
          MARS
        </text>
        <text x={W / 2} y={24} textAnchor="middle" fill={COLOR.muted} fontSize={11}>
          time flows down · gold = news travelling at light speed
        </text>

        {ticks.map((t) => (
          <g key={t}>
            <line x1={X.earth} x2={X.mars} y1={y(t)} y2={y(t)} stroke={COLOR.line} strokeWidth={1} />
            <text x={8} y={y(t) + 4} fill={COLOR.muted} fontSize={10} fontFamily="JetBrains Mono, monospace">
              {fmt(t)}
            </text>
          </g>
        ))}

        <line x1={X.earth} x2={X.earth} y1={TOP - 10} y2={H - BOTTOM} stroke={COLOR.earth} strokeWidth={2} />
        <line x1={X.mars} x2={X.mars} y1={TOP - 10} y2={H - BOTTOM} stroke={COLOR.mars} strokeWidth={2} />

        <g clipPath="url(#plot)">
          {(['earth', 'mars'] as NodeId[]).map((observer) => {
            const g = state.nodes[observer].ghost
            const gx = X[g.planet]
            const top = y(g.window_start)
            const bottom = y(g.window_end)
            const p = Math.round(g.p_at_least_one * 100)
            return (
              <g key={`ghost-${observer}`}>
                <rect x={gx - 12} y={top} width={24} height={Math.max(bottom - top, 0)} fill={COLOR.tie} opacity={0.08} />
                <text
                  x={g.planet === 'earth' ? gx + 16 : gx - 16}
                  y={top + 12}
                  textAnchor={g.planet === 'earth' ? 'start' : 'end'}
                  fill={COLOR.tie}
                  fontSize={9}
                  opacity={0.8}
                >
                  unseen by {observer === 'earth' ? 'Earth' : 'Mars'}
                </text>
                {g.times.map((t) => (
                  <g key={`${observer}-${t}`}>
                    <circle cx={gx} cy={y(t)} r={9} fill="none" stroke={COLOR.tie} strokeWidth={1.5} strokeDasharray="2 3" />
                    <text
                      x={g.planet === 'earth' ? gx + 16 : gx - 16}
                      y={y(t) + 4}
                      textAnchor={g.planet === 'earth' ? 'start' : 'end'}
                      fill={COLOR.tie}
                      fontSize={10}
                      fontFamily="JetBrains Mono, monospace"
                    >
                      ghost {p}%
                    </text>
                  </g>
                ))}
              </g>
            )
          })}

          {state.in_flight.map((m) => {
            const x1 = X[m.from_node]
            const y1 = y(m.sent_t)
            const x2 = X[m.to_node]
            const y2 = y(m.arrive_t)
            const f = m.delivered ? 1 : Math.min(1, Math.max(0, (state.sim_t - m.sent_t) / (m.arrive_t - m.sent_t)))
            return (
              <g key={`${m.id}-${m.to_node}`}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x1 + f * (x2 - x1)}
                  y2={y1 + f * (y2 - y1)}
                  stroke={COLOR.signal}
                  strokeWidth={2}
                  opacity={m.delivered ? 0.45 : 1}
                />
                {!m.delivered && (
                  <circle cx={x1 + f * (x2 - x1)} cy={y1 + f * (y2 - y1)} r={4} fill={COLOR.signal} />
                )}
                {m.delivered && m.predicted_p !== null && (
                  <text
                    x={m.to_node === 'earth' ? x2 + 8 : x2 - 8}
                    y={y2 + 14}
                    textAnchor={m.to_node === 'earth' ? 'start' : 'end'}
                    fill={COLOR.tie}
                    fontSize={9}
                  >
                    arrived · radar said {Math.round(m.predicted_p * 100)}%
                  </text>
                )}
              </g>
            )
          })}

          {state.receipts.map((rc) => {
            const members = rc.tie.map((id) => byId.get(id)).filter((r): r is RequestOut => !!r)
            if (members.length === 0) return null
            const ty = members.reduce((s, r) => s + y(r.sim_t), 0) / members.length
            return (
              <g key={rc.tie.join('-')}>
                <rect x={W / 2 - 52} y={ty - 13} width={104} height={24} rx={4} fill={COLOR.tie} opacity={0.18} />
                <text x={W / 2} y={ty + 4} textAnchor="middle" fill={COLOR.tie} fontSize={12} fontWeight={700}>
                  TRUE TIE
                </text>
              </g>
            )
          })}

          {requests.map((r) => {
            const cx = X[r.node]
            const cy = y(r.sim_t)
            const isTie = tied.has(r.id)
            const stroke = r.status === 'frozen' ? COLOR.signal : r.node === 'earth' ? COLOR.earth : COLOR.mars
            const labelX = r.node === 'earth' ? cx - 14 : cx + 14
            return (
              <g key={r.id}>
                {isTie && <circle cx={cx} cy={cy} r={16} fill={COLOR.tie} opacity={0.3} />}
                <circle
                  cx={cx}
                  cy={cy}
                  r={7}
                  fill={r.status === 'final' ? COLOR.final : '#0B0D12'}
                  stroke={r.status === 'final' ? COLOR.final : stroke}
                  strokeWidth={2}
                  strokeDasharray={r.status === 'provisional' ? '3 2' : undefined}
                />
                <text
                  x={labelX}
                  y={cy + 4}
                  textAnchor={r.node === 'earth' ? 'end' : 'start'}
                  fill="#E8EAF0"
                  fontSize={11}
                  fontFamily="JetBrains Mono, monospace"
                >
                  {r.id} · {r.qty} {state.resource.unit}
                </text>
              </g>
            )
          })}
        </g>

        <line
          x1={40}
          x2={W - 10}
          y1={y(state.sim_t)}
          y2={y(state.sim_t)}
          stroke={COLOR.muted}
          strokeDasharray="4 4"
        />
        <text x={W - 10} y={y(state.sim_t) - 6} textAnchor="end" fill={COLOR.muted} fontSize={10}>
          now {fmt(state.sim_t)}
        </text>
      </svg>

      <div className="flex flex-wrap gap-4 px-2 pb-1 text-xs text-muted">
        <span>◌ provisional</span>
        <span className="text-final">● final (after one round trip)</span>
        <span className="text-signal">— news in flight</span>
        <span className="text-tie">◉ true tie: neither side could have known</span>
        <span className="text-tie">◌ ghost: ML prediction of a request not yet seen</span>
      </div>
    </div>
  )
}
