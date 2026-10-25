from typing import Literal

from pydantic import BaseModel

Node = Literal["earth", "mars"]
Priority = Literal["medical", "science", "commercial"]
Policy = Literal["needs", "lottery", "prorata", "priority"]
Status = Literal["provisional", "final", "frozen"]
IntentSource = Literal["llm", "rules"]


class LinkInfo(BaseModel):
    date: str
    distance_km: float
    distance_au: float
    one_way_s: float
    round_trip_s: float
    sun_angle_deg: float
    conjunction: bool


class Resource(BaseModel):
    name: str = "Cargo space, ship ARES-7"
    capacity: float = 500
    unit: str = "kg"
    divisible: bool = True


class ScenarioIn(BaseModel):
    date: str
    compression: float = 60
    resource: Resource = Resource()
    policy: Policy = "needs"


class NeedSpec(BaseModel):
    min_qty: float
    max_qty: float
    category: Priority = "commercial"
    can_defer: bool = False
    summary: str = ""


class IntentIn(BaseModel):
    node: Node
    actor: str
    text: str


class IntentOut(BaseModel):
    needs: NeedSpec
    source: IntentSource
    model: str
    notes: list[str]


class RequestIn(BaseModel):
    node: Node
    actor: str
    qty: float
    priority: Priority = "commercial"
    needs: NeedSpec | None = None
    text: str | None = None


class RequestOut(BaseModel):
    id: str
    node: Node
    actor: str
    qty: float
    priority: Priority
    min_qty: float
    can_defer: bool
    text: str | None
    vc: list[int]
    sim_t: float
    nonce: str
    status: Status
    final_at: float


class InFlight(BaseModel):
    id: str
    from_node: Node
    to_node: Node
    sent_t: float
    arrive_t: float
    delivered: bool


class Evidence(BaseModel):
    a: str
    b: str
    t_a: float
    t_b: float
    news_arrival: float


class Outcome(BaseModel):
    allocation: dict[str, float]
    deferred: dict[str, float]
    needs_met: int


class Receipt(BaseModel):
    tie: list[str]
    evidence: list[Evidence]
    policy: Policy
    seed: str
    order: list[str]
    allocation: dict[str, float]
    deferred: dict[str, float]
    needs_met: int
    lottery: Outcome
    explanation: str
    narrative: str
    narrative_source: IntentSource


class NodeView(BaseModel):
    log: list[RequestOut]
    vc: list[int]
    allocations: dict[str, float]
    deferred: dict[str, float]
    hash: str
    tie_risk: float


class StateOut(BaseModel):
    sim_t: float
    one_way_s: float
    compression: float
    conjunction: bool
    resource: Resource
    policy: Policy
    nodes: dict[Node, NodeView]
    in_flight: list[InFlight]
    receipts: list[Receipt]
    naive_allocations: dict[str, float]
    ai_enabled: bool


class FairnessOut(BaseModel):
    trials: int
    window_s: float
    earth_server_mars_win: float
    mars_server_mars_win: float
    lightcone_mars_win: float
    tie_rate: float
