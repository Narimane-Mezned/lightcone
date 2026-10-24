export type NodeId = 'earth' | 'mars'
export type Priority = 'medical' | 'science' | 'commercial'
export type Policy = 'lottery' | 'prorata' | 'priority'
export type Status = 'provisional' | 'final' | 'frozen'

export interface LinkInfo {
  date: string
  distance_km: number
  distance_au: number
  one_way_s: number
  round_trip_s: number
  sun_angle_deg: number
  conjunction: boolean
}

export interface Resource {
  name: string
  capacity: number
  unit: string
  divisible: boolean
}

export interface ScenarioIn {
  date: string
  compression: number
  resource: Resource
  policy: Policy
}

export interface RequestIn {
  node: NodeId
  actor: string
  qty: number
  priority: Priority
}

export interface RequestOut {
  id: string
  node: NodeId
  actor: string
  qty: number
  priority: Priority
  vc: number[]
  sim_t: number
  nonce: string
  status: Status
  final_at: number
}

export interface InFlight {
  id: string
  from_node: NodeId
  to_node: NodeId
  sent_t: number
  arrive_t: number
  delivered: boolean
}

export interface Evidence {
  a: string
  b: string
  t_a: number
  t_b: number
  news_arrival: number
}

export interface Receipt {
  tie: string[]
  evidence: Evidence[]
  policy: Policy
  seed: string
  order: string[]
  allocation: Record<string, number>
  explanation: string
}

export interface NodeView {
  log: RequestOut[]
  vc: number[]
  allocations: Record<string, number>
  hash: string
}

export interface StateOut {
  sim_t: number
  one_way_s: number
  compression: number
  conjunction: boolean
  resource: Resource
  policy: Policy
  nodes: Record<NodeId, NodeView>
  in_flight: InFlight[]
  receipts: Receipt[]
  naive_allocations: Record<string, number>
}

export interface FairnessOut {
  trials: number
  window_s: number
  earth_server_mars_win: number
  mars_server_mars_win: number
  lightcone_mars_win: number
  tie_rate: number
}
