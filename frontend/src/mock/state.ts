import type { StateOut } from '../types'

const CLINIC = 'We need at least 250 kg of medical supplies before the March launch window. Anything above 300 kg is useless.'
const FREIGHT = 'We would like 400 kg of cargo space. We can wait for the next ship for part of it, and we can give up 50 kg for a medical emergency.'

const e1 = { id: 'E-1', node: 'earth' as const, actor: 'Helios Freight', qty: 400, priority: 'commercial' as const, min_qty: 400, can_defer: true, next_ship_value: 0.7, yield_to_medical: true, yield_max_qty: 50, text: FREIGHT, vc: [1, 0], sim_t: 120, nonce: 'a91f', status: 'provisional' as const, final_at: 1498 }
const m1 = { id: 'M-1', node: 'mars' as const, actor: 'Jezero Clinic', qty: 300, priority: 'medical' as const, min_qty: 250, can_defer: false, next_ship_value: 0, yield_to_medical: false, yield_max_qty: 0, text: CLINIC, vc: [0, 1], sim_t: 360, nonce: '4c2e', status: 'provisional' as const, final_at: 1738 }
const ghostEarth = { planet: 'mars' as const, expected_requests: 0.62, p_at_least_one: 0.46, expected_kg: 202.9, window_start: 211, window_end: 900, times: [555] }
const ghostMars = { planet: 'earth' as const, expected_requests: 0.91, p_at_least_one: 0.6, expected_kg: 247.7, window_start: 211, window_end: 900, times: [555] }

export const mockState: StateOut = {
  sim_t: 900,
  one_way_s: 689,
  compression: 60,
  conjunction: false,
  resource: { name: 'Cargo space, ship ARES-7', capacity: 500, unit: 'kg', divisible: true },
  policy: 'envoys',
  nodes: {
    earth: { log: [e1, m1], vc: [1, 1], allocations: { 'M-1': 300, 'E-1': 200 }, deferred: { 'E-1': 150 }, hash: '7d3a91c0e19b', tie_risk: 0.46, ghost: ghostEarth, forecast: { 'E-1': { low: 200, high: 200, p_tie: 0.46 } } },
    mars: { log: [m1, e1], vc: [1, 1], allocations: { 'M-1': 300, 'E-1': 200 }, deferred: { 'E-1': 150 }, hash: '7d3a91c0e19b', tie_risk: 0.6, ghost: ghostMars, forecast: { 'M-1': { low: 250, high: 300, p_tie: 0.6 } } },
  },
  in_flight: [
    { id: 'E-1', from_node: 'earth', to_node: 'mars', sent_t: 120, arrive_t: 809, delivered: true, predicted_p: 0.6 },
    { id: 'M-1', from_node: 'mars', to_node: 'earth', sent_t: 360, arrive_t: 1049, delivered: false, predicted_p: null },
  ],
  receipts: [
    {
      tie: ['E-1', 'M-1'],
      evidence: [{ a: 'E-1', b: 'M-1', t_a: 120, t_b: 360, news_arrival: 809 }],
      policy: 'envoys',
      seed: '9f2c41ab77d0',
      order: ['M-1', 'E-1'],
      allocation: { 'M-1': 300, 'E-1': 200 },
      deferred: { 'E-1': 150 },
      needs_met: 2,
      lottery: { allocation: { 'E-1': 400, 'M-1': 100 }, deferred: {}, needs_met: 1 },
      envoys: [
        { id: 'E-1', actor: 'Helios Freight', mandate: 'commercial, min 400, max 400, next ship worth 70%, yields 50 to medical', baseline: 0.5625, utility: 0.7625, gain: 0.2 },
        { id: 'M-1', actor: 'Jezero Clinic', mandate: 'medical, min 250, max 300, cannot wait', baseline: 0.5417, utility: 1, gain: 0.4583 },
      ],
      explanation: 'E-1 (Earth, 00:02:00) and M-1 (Mars, 00:06:00) are a true tie: news of E-1 could only reach Mars at 00:13:29, after M-1 was made. AI envoys negotiated for their owners (Nash bargaining over the mandates compiled from their own words): each accepted only a deal better than its expected lottery outcome.',
      narrative: 'Envoy for Jezero Clinic: My owner needs at least 250 kg of medicine on this ship and cannot wait.\nEnvoy for Helios Freight: My owner wants 400 kg but accepts the next ship for part of it, and yields 50 kg to a medical need.\nEnvoy for Jezero Clinic: Then 300 kg now covers us fully: 100% of our ideal, against 54% expected from a coin flip.\nEnvoy for Helios Freight: Agreed if we take 200 kg now and 150 kg guaranteed on the next ship: 76% for us, against 56% from a lottery.\nDeal: Jezero Clinic receives 300 kg now; Helios Freight receives 200 kg now and 150 kg on the next ship.',
      narrative_source: 'llm',
    },
  ],
  naive_allocations: { 'E-1': 400, 'M-1': 100 },
  ai_enabled: true,
  ghost_metrics: { mae_rate_model: 0.0038, mae_rate_naive: 0.07082, mae_rate_model_rush: 0.03538, mae_rate_naive_rush: 0.34537, deviance_explained_vs_naive: 0.063 },
}
