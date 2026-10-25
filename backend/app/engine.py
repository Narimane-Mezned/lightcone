import threading
from dataclasses import dataclass

from . import ghost, llm, narrate
from .clock import SimClock
from .models import RequestIn, ScenarioIn
from .node import Node, Request
from .receipts import build_receipt
from .settle import allocation_hash, settle


@dataclass
class Message:
    request: Request
    from_node: str
    to_node: str
    sent_t: float
    arrive_t: float
    delivered: bool = False
    predicted_p: float | None = None


class Engine:
    def __init__(self, scenario: ScenarioIn, one_way_s: float, conjunction: bool):
        self.lock = threading.Lock()
        self.clock = SimClock(scenario.compression)
        self.configure(scenario, one_way_s, conjunction)

    def configure(self, scenario: ScenarioIn, one_way_s: float, conjunction: bool) -> None:
        self.scenario = scenario
        self.one_way_s = one_way_s
        self.conjunction = conjunction
        self.nodes = {"earth": Node("earth"), "mars": Node("mars")}
        self.messages: list[Message] = []
        self.requests: list[Request] = []
        self.clock.restart(scenario.compression)

    def reset(self) -> None:
        narrate.clear()
        self.configure(self.scenario, self.one_way_s, self.conjunction)

    def _now(self, at: float | None) -> float:
        return self.clock.now() if at is None else at

    def _advance(self, now: float) -> None:
        for message in sorted(self.messages, key=lambda m: m.arrive_t):
            if not message.delivered and message.arrive_t <= now:
                message.predicted_p = ghost.radar(message.to_node, message.arrive_t, self.one_way_s)["p_at_least_one"]
                self.nodes[message.to_node].receive(message.request)
                message.delivered = True

    def _status(self, request: Request, now: float) -> str:
        if self.conjunction:
            return "frozen"
        return "final" if now >= request.sim_t + 2 * self.one_way_s else "provisional"

    def _request_out(self, request: Request, now: float) -> dict:
        return {
            "id": request.id,
            "node": request.node,
            "actor": request.actor,
            "qty": request.qty,
            "priority": request.priority,
            "min_qty": request.min_qty,
            "can_defer": request.can_defer,
            "next_ship_value": request.next_ship_value,
            "yield_to_medical": request.yield_to_medical,
            "yield_max_qty": request.yield_max_qty,
            "text": request.text,
            "vc": request.vc,
            "sim_t": round(request.sim_t, 1),
            "nonce": request.nonce,
            "status": self._status(request, now),
            "final_at": round(request.sim_t + 2 * self.one_way_s, 1),
        }

    def submit(self, body: RequestIn, at: float | None = None) -> dict:
        with self.lock:
            now = self._now(at)
            self._advance(now)
            if body.needs:
                request = self.nodes[body.node].create(
                    body.actor,
                    body.needs.max_qty,
                    body.needs.category,
                    now,
                    min_qty=body.needs.min_qty,
                    can_defer=body.needs.can_defer,
                    text=body.text,
                    next_ship_value=body.needs.next_ship_value,
                    yield_to_medical=body.needs.yield_to_medical,
                    yield_max_qty=body.needs.yield_max_qty,
                )
            else:
                request = self.nodes[body.node].create(body.actor, body.qty, body.priority, now, text=body.text)
            self.requests.append(request)
            other = "mars" if body.node == "earth" else "earth"
            self.messages.append(Message(request, body.node, other, now, now + self.one_way_s))
            return self._request_out(request, now)

    def _naive(self) -> dict[str, float]:
        arrivals = sorted(
            self.requests,
            key=lambda r: (r.sim_t + (self.one_way_s if r.node == "mars" else 0.0), r.id),
        )
        capacity = self.scenario.resource.capacity
        allocation = {}
        for r in arrivals:
            if self.scenario.resource.divisible:
                give = min(r.qty, capacity)
            else:
                give = r.qty if r.qty <= capacity else 0.0
            allocation[r.id] = round(give, 3)
            capacity -= give
        return allocation

    def _forecast(self, node: Node, radar: dict, now: float, allocations: dict[str, float]) -> dict:
        resource = self.scenario.resource
        own = [r for r in node.log if r.node == node.name and now < r.sim_t + 2 * self.one_way_s]
        if not own or radar["p_at_least_one"] <= 0:
            return {}
        other = radar["planet"]
        kg = radar["expected_kg"]
        phantom = Request(
            id="G-1",
            node=other,
            actor="predicted request",
            qty=kg,
            priority="commercial",
            vc=[0, node.vc[1] + 1] if other == "mars" else [node.vc[0] + 1, 0],
            sim_t=now,
            nonce="ghost",
            min_qty=round(0.8 * kg, 1),
        )
        with_ghost, _, _ = settle(node.log + [phantom], resource.capacity, self.scenario.policy, resource.divisible)
        return {
            r.id: {
                "low": round(min(with_ghost.get(r.id, 0.0), allocations.get(r.id, 0.0)), 1),
                "high": round(allocations.get(r.id, 0.0), 1),
                "p_tie": radar["p_at_least_one"],
            }
            for r in own
        }

    def snapshot(self, at: float | None = None) -> dict:
        with self.lock:
            now = self._now(at)
            self._advance(now)
            resource = self.scenario.resource
            policy = self.scenario.policy

            node_views = {}
            receipts_by_key: dict[tuple, dict] = {}
            for name, node in self.nodes.items():
                allocations, deferred, ties = settle(node.log, resource.capacity, policy, resource.divisible)
                radar = ghost.radar(name, now, self.one_way_s)
                node_views[name] = {
                    "log": [self._request_out(r, now) for r in sorted(node.log, key=lambda r: (r.sim_t, r.id))],
                    "vc": list(node.vc),
                    "allocations": allocations,
                    "deferred": deferred,
                    "hash": allocation_hash(allocations, deferred),
                    "tie_risk": radar["p_at_least_one"],
                    "ghost": radar,
                    "forecast": self._forecast(node, radar, now, allocations),
                }
                for tie in ties:
                    key = tuple(sorted(r.id for r in tie["members"]))
                    receipts_by_key[key] = build_receipt(tie, policy, self.one_way_s, resource.unit)

            keys = list(receipts_by_key)
            receipts = [
                receipts_by_key[k]
                for k in keys
                if not any(set(k) < set(other) for other in keys)
            ]

            in_flight = [
                {
                    "id": m.request.id,
                    "from_node": m.from_node,
                    "to_node": m.to_node,
                    "sent_t": round(m.sent_t, 1),
                    "arrive_t": round(m.arrive_t, 1),
                    "delivered": m.delivered,
                    "predicted_p": m.predicted_p,
                }
                for m in self.messages
            ]

            return {
                "sim_t": round(now, 1),
                "one_way_s": self.one_way_s,
                "compression": self.clock.compression,
                "conjunction": self.conjunction,
                "resource": resource.model_dump(),
                "policy": policy,
                "nodes": node_views,
                "in_flight": in_flight,
                "receipts": receipts,
                "naive_allocations": self._naive(),
                "ai_enabled": llm.enabled(),
                "ghost_metrics": ghost.metrics(),
            }
