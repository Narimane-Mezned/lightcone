import hashlib
import json

from .node import Request

PRIORITY_RANK = {"medical": 0, "science": 1, "commercial": 2}
EPS = 1e-9


def happened_before(a: Request, b: Request) -> bool:
    return all(x <= y for x, y in zip(a.vc, b.vc)) and a.vc != b.vc


def concurrent(a: Request, b: Request) -> bool:
    return not happened_before(a, b) and not happened_before(b, a)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def lottery(group: list[Request]) -> tuple[list[Request], str]:
    seed = _sha("".join(sorted(r.id + r.nonce for r in group)))
    ordered = sorted(group, key=lambda r: _sha(seed + r.id))
    return ordered, seed


def _greedy(ordered: list[Request], capacity: float, divisible: bool) -> tuple[dict[str, float], float]:
    allocation = {}
    for r in ordered:
        if divisible:
            give = min(r.qty, capacity)
        else:
            give = r.qty if r.qty <= capacity + EPS else 0.0
        allocation[r.id] = round(give, 3)
        capacity -= give
    return allocation, max(capacity, 0.0)


def _needs_aware(ordered_lottery: list[Request], capacity: float, divisible: bool):
    position = {r.id: i for i, r in enumerate(ordered_lottery)}
    order = sorted(
        ordered_lottery,
        key=lambda r: (r.can_defer, PRIORITY_RANK[r.priority], position[r.id]),
    )
    alloc = {r.id: 0.0 for r in order}
    for r in order:
        if r.min_qty <= capacity + EPS:
            alloc[r.id] = r.min_qty
            capacity -= r.min_qty
    if divisible:
        while capacity > EPS:
            active = [r for r in order if alloc[r.id] < r.qty - EPS]
            if not active:
                break
            share = capacity / len(active)
            for r in active:
                give = min(share, r.qty - alloc[r.id])
                alloc[r.id] += give
                capacity -= give
    deferred = {
        r.id: round(r.min_qty - alloc[r.id], 3)
        for r in order
        if r.can_defer and alloc[r.id] < r.min_qty - EPS
    }
    allocation = {r.id: round(alloc[r.id], 3) for r in order}
    return allocation, deferred, max(capacity, 0.0), order


def needs_met(group: list[Request], allocation: dict[str, float], deferred: dict[str, float]) -> int:
    return sum(
        1
        for r in group
        if allocation.get(r.id, 0.0) + deferred.get(r.id, 0.0) >= r.min_qty - EPS
    )


def resolve(group: list[Request], capacity: float, policy: str, divisible: bool) -> dict:
    ordered, seed = lottery(group)
    deferred: dict[str, float] = {}
    if policy == "needs":
        allocation, deferred, remaining, ordered = _needs_aware(ordered, capacity, divisible)
    elif policy == "prorata" and divisible:
        total = sum(r.qty for r in group)
        if total <= capacity:
            allocation = {r.id: round(r.qty, 3) for r in group}
            remaining = capacity - total
        else:
            allocation = {r.id: round(r.qty * capacity / total, 3) for r in group}
            remaining = 0.0
    else:
        if policy == "priority":
            position = {r.id: i for i, r in enumerate(ordered)}
            ordered = sorted(group, key=lambda r: (PRIORITY_RANK[r.priority], position[r.id]))
        allocation, remaining = _greedy(ordered, capacity, divisible)
    return {
        "allocation": allocation,
        "deferred": deferred,
        "remaining": remaining,
        "order": [r.id for r in ordered],
        "seed": seed,
    }


def settle(requests: list[Request], capacity: float, policy: str = "needs", divisible: bool = True):
    pending = sorted(requests, key=lambda r: r.id)
    allocations: dict[str, float] = {}
    deferred: dict[str, float] = {}
    ties = []
    while pending:
        layer = [r for r in pending if not any(happened_before(o, r) for o in pending if o is not r)]
        before = capacity
        result = resolve(layer, capacity, policy, divisible)
        allocations.update(result["allocation"])
        deferred.update(result["deferred"])
        capacity = result["remaining"]
        if len(layer) > 1:
            lottery_order, _ = lottery(layer)
            lottery_alloc, _ = _greedy(lottery_order, before, divisible)
            ties.append({
                "members": layer,
                "order": result["order"],
                "seed": result["seed"],
                "allocation": result["allocation"],
                "deferred": result["deferred"],
                "needs_met": needs_met(layer, result["allocation"], result["deferred"]),
                "lottery": {
                    "allocation": lottery_alloc,
                    "deferred": {},
                    "needs_met": needs_met(layer, lottery_alloc, {}),
                },
            })
        layer_ids = {r.id for r in layer}
        pending = [r for r in pending if r.id not in layer_ids]
    return allocations, deferred, ties


def allocation_hash(allocations: dict[str, float], deferred: dict[str, float] | None = None) -> str:
    return _sha(json.dumps({"allocations": allocations, "deferred": deferred or {}}, sort_keys=True))
