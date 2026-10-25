import secrets
from dataclasses import dataclass, field

INDEX = {"earth": 0, "mars": 1}
PREFIX = {"earth": "E", "mars": "M"}


@dataclass
class Request:
    id: str
    node: str
    actor: str
    qty: float
    priority: str
    vc: list[int]
    sim_t: float
    nonce: str
    min_qty: float = 0.0
    can_defer: bool = False
    text: str | None = None
    next_ship_value: float = 0.0
    yield_to_medical: bool = False
    yield_max_qty: float = 0.0


@dataclass
class Node:
    name: str
    vc: list[int] = field(default_factory=lambda: [0, 0])
    log: list[Request] = field(default_factory=list)

    @property
    def index(self) -> int:
        return INDEX[self.name]

    def create(
        self,
        actor: str,
        qty: float,
        priority: str,
        sim_t: float,
        min_qty: float | None = None,
        can_defer: bool = False,
        text: str | None = None,
        next_ship_value: float = 0.0,
        yield_to_medical: bool = False,
        yield_max_qty: float = 0.0,
    ) -> Request:
        self.vc[self.index] += 1
        request = Request(
            id=f"{PREFIX[self.name]}-{self.vc[self.index]}",
            node=self.name,
            actor=actor,
            qty=qty,
            priority=priority,
            vc=list(self.vc),
            sim_t=sim_t,
            nonce=secrets.token_hex(4),
            min_qty=qty if min_qty is None else min_qty,
            can_defer=can_defer,
            text=text,
            next_ship_value=next_ship_value,
            yield_to_medical=yield_to_medical,
            yield_max_qty=yield_max_qty,
        )
        self.log.append(request)
        return request

    def receive(self, request: Request) -> None:
        self.vc = [max(a, b) for a, b in zip(self.vc, request.vc)]
        self.log.append(request)
