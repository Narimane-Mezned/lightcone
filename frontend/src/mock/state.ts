import type { StateOut } from '../types'

export const mockState: StateOut = {
  sim_t: 900,
  one_way_s: 689,
  compression: 60,
  conjunction: false,
  resource: { name: 'Cargo space, ship ARES-7', capacity: 500, unit: 'kg', divisible: true },
  policy: 'lottery',
  nodes: {
    earth: {
      log: [
        { id: 'E-1', node: 'earth', actor: 'Helios Freight', qty: 400, priority: 'commercial', vc: [1, 0], sim_t: 120, nonce: 'a91f', status: 'provisional', final_at: 1498 },
        { id: 'M-1', node: 'mars', actor: 'Jezero Clinic', qty: 300, priority: 'commercial', vc: [0, 1], sim_t: 360, nonce: '4c2e', status: 'provisional', final_at: 1738 },
      ],
      vc: [1, 1],
      allocations: { 'M-1': 300, 'E-1': 200 },
      hash: '7d3a...e19b',
    },
    mars: {
      log: [
        { id: 'M-1', node: 'mars', actor: 'Jezero Clinic', qty: 300, priority: 'commercial', vc: [0, 1], sim_t: 360, nonce: '4c2e', status: 'provisional', final_at: 1738 },
        { id: 'E-1', node: 'earth', actor: 'Helios Freight', qty: 400, priority: 'commercial', vc: [1, 0], sim_t: 120, nonce: 'a91f', status: 'provisional', final_at: 1498 },
      ],
      vc: [1, 1],
      allocations: { 'M-1': 300, 'E-1': 200 },
      hash: '7d3a...e19b',
    },
  },
  in_flight: [
    { id: 'E-1', from_node: 'earth', to_node: 'mars', sent_t: 120, arrive_t: 809, delivered: true },
    { id: 'M-1', from_node: 'mars', to_node: 'earth', sent_t: 360, arrive_t: 1049, delivered: false },
  ],
  receipts: [
    {
      tie: ['E-1', 'M-1'],
      evidence: [{ a: 'E-1', b: 'M-1', t_a: 120, t_b: 360, news_arrival: 809 }],
      policy: 'lottery',
      seed: '9f2c41ab...',
      order: ['M-1', 'E-1'],
      allocation: { 'M-1': 300, 'E-1': 200 },
      explanation: 'E-1 (Earth, 00:02:00) and M-1 (Mars, 00:06:00) are a true tie: news of E-1 reached Mars only at 00:13:29. Verifiable lottery order: M-1, then E-1.',
    },
  ],
  naive_allocations: { 'E-1': 400, 'M-1': 100 },
}
