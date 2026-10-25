import type { StateOut } from '../types'

const CLINIC = 'We need at least 250 kg of medical supplies before the March launch window. Anything above 300 kg is useless.'
const FREIGHT = 'We would like 400 kg of cargo space, but we can wait for the next ship if needed.'

const e1 = { id: 'E-1', node: 'earth' as const, actor: 'Helios Freight', qty: 400, priority: 'commercial' as const, min_qty: 400, can_defer: true, text: FREIGHT, vc: [1, 0], sim_t: 120, nonce: 'a91f', status: 'provisional' as const, final_at: 1498 }
const m1 = { id: 'M-1', node: 'mars' as const, actor: 'Jezero Clinic', qty: 300, priority: 'medical' as const, min_qty: 250, can_defer: false, text: CLINIC, vc: [0, 1], sim_t: 360, nonce: '4c2e', status: 'provisional' as const, final_at: 1738 }

export const mockState: StateOut = {
  sim_t: 900,
  one_way_s: 689,
  compression: 60,
  conjunction: false,
  resource: { name: 'Cargo space, ship ARES-7', capacity: 500, unit: 'kg', divisible: true },
  policy: 'needs',
  nodes: {
    earth: { log: [e1, m1], vc: [1, 1], allocations: { 'M-1': 300, 'E-1': 200 }, deferred: { 'E-1': 200 }, hash: '7d3a91c0e19b', tie_risk: 0.42 },
    mars: { log: [m1, e1], vc: [1, 1], allocations: { 'M-1': 300, 'E-1': 200 }, deferred: { 'E-1': 200 }, hash: '7d3a91c0e19b', tie_risk: 0.38 },
  },
  in_flight: [
    { id: 'E-1', from_node: 'earth', to_node: 'mars', sent_t: 120, arrive_t: 809, delivered: true },
    { id: 'M-1', from_node: 'mars', to_node: 'earth', sent_t: 360, arrive_t: 1049, delivered: false },
  ],
  receipts: [
    {
      tie: ['E-1', 'M-1'],
      evidence: [{ a: 'E-1', b: 'M-1', t_a: 120, t_b: 360, news_arrival: 809 }],
      policy: 'needs',
      seed: '9f2c41ab77d0',
      order: ['M-1', 'E-1'],
      allocation: { 'M-1': 300, 'E-1': 200 },
      deferred: { 'E-1': 200 },
      needs_met: 2,
      lottery: { allocation: { 'E-1': 400, 'M-1': 100 }, deferred: {}, needs_met: 1 },
      explanation: 'E-1 (Earth, 00:02:00) and M-1 (Mars, 00:06:00) are a true tie: news of E-1 could only reach Mars at 00:13:29, after M-1 was made. Needs-aware resolution: everyone\'s minimum first, the rest shared fairly. Result: M-1 gets 300 kg, E-1 gets 200 kg. E-1 is guaranteed 200 kg with priority on the next ship. Needs met: 2 of 2 (a plain lottery would meet 1 of 2).',
      narrative: 'Neither Jezero Clinic nor Helios Freight could have known about the other: light needed 11.5 minutes to cross. The clinic receives the 300 kg its patients need on this ship, and Helios Freight receives 200 kg now plus 200 kg guaranteed with priority on the next ship. A blind lottery would have left the clinic with 100 kg, below its 250 kg minimum.',
      narrative_source: 'llm',
    },
  ],
  naive_allocations: { 'E-1': 400, 'M-1': 100 },
  ai_enabled: true,
}
