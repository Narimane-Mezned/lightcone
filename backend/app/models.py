from typing import Literal

from pydantic import BaseModel

Node = Literal["earth", "mars"]
Priority = Literal["medical", "science", "commercial"]
Policy = Literal["lottery", "prorata", "priority"]
Status = Literal["provisional", "final", "frozen"]


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
    policy: Policy = "lottery"


class RequestIn(BaseModel):
    node: Node
    actor: str
    qty: float
    priority: Priority = "commercial"


class RequestOut(BaseModel):
    id: str
    node: Node
    actor: str
    qty: float
    priority: Priority
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


class Receipt(BaseModel):
    tie: list[str]
    evidence: list[Evidence]
    policy: Policy
    seed: str
    order: list[str]
    allocation: dict[str, float]
    explanation: str


class NodeView(BaseModel):
    log: list[RequestOut]
    vc: list[int]
    allocations: dict[str, float]
    hash: str


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


class FairnessOut(BaseModel):
    trials: int
    window_s: float
    earth_server_mars_win: float
    mars_server_mars_win: float
    lightcone_mars_win: float
    tie_rate: float
