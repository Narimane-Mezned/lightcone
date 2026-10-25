import hashlib
import json
from itertools import permutations

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


def effective_min(r: Request, group: list[Request]) -> float:
    if r.yield_to_medical and any(o.priority == "medical" and o.id != r.id for o in group):
        return max(0.0, r.min_qty - r.yield_max_qty)
    return r.min_qty


def utility(r: Request, now: float, later: float, eff_min: float) -> float:
    value = min(now, r.qty) + r.next_ship_value * min(later, max(0.0, r.qty - now))
    u = value / r.qty if r.qty > 0 else 0.0
    covered = now + (later if r.next_ship_value > 0 else 0.0)
    if covered < eff_min - EPS:
        u *= 0.25
    return u


def _baseline(group: list[Request], capacity: float, divisible: bool) -> dict[str, float]:
    orders = list(permutations(group))
    totals = {r.id: 0.0 for r in group}
    for order in orders:
        allocation, _ = _greedy(list(order), capacity, divisible)
        for r in group:
            totals[r.id] += utility(r, allocation[r.id], 0.0, effective_min(r, group))
    return {rid: total / len(orders) for rid, total in totals.items()}


def _candidates(group: list[Request], capacity: float):
    step = max(capacity / 50, 1.0)
    grid = [round(i * step, 3) for i in range(int(capacity / step) + 1)]
    if len(group) == 2:
        a, b = group
        for x in grid:
            yield {a.id: min(x, a.qty), b.id: min(max(capacity - x, 0.0), b.qty)}
    else:
        a, b, c = group
        for x in grid:
            for y in grid:
                if x + y > capacity + EPS:
                    break
                yield {a.id: min(x, a.qty), b.id: min(y, b.qty), c.id: min(max(capacity - x - y, 0.0), c.qty)}


def _envoys(ordered_lottery: list[Request], capacity: float, divisible: bool):
    group = sorted(ordered_lottery, key=lambda r: r.id)
    baseline = _baseline(group, capacity, divisible)
    eff = {r.id: effective_min(r, group) for r in group}
    best = None
    if divisible and 2 <= len(group) <= 3:
        for now in _candidates(group, capacity):
            later = {
                r.id: round(max(0.0, eff[r.id] - now[r.id]), 3) if r.next_ship_value > 0 else 0.0
                for r in group
            }
            utils = {r.id: utility(r, now[r.id], later[r.id], eff[r.id]) for r in group}
            gains = {rid: utils[rid] - baseline[rid] for rid in utils}
            if any(g < -EPS for g in gains.values()):
                continue
            product = 1.0
            for g in gains.values():
                product *= max(g, 0.0)
            key = (round(product, 9), round(sum(gains.values()), 9), tuple(round(now[r.id], 3) for r in group))
            if best is None or key > best[0]:
                best = (key, now, later, utils, gains)
    if best is None:
        allocation, deferred, remaining, order = _needs_aware(ordered_lottery, capacity, divisible)
        utils = {r.id: utility(r, allocation[r.id], deferred.get(r.id, 0.0), eff[r.id]) for r in group}
        gains = {rid: utils[rid] - baseline[rid] for rid in utils}
        method = "fallback"
    else:
        _, now, later, utils, gains = best
        allocation = {rid: round(q, 3) for rid, q in now.items()}
        deferred = {rid: q for rid, q in later.items() if q > EPS}
        remaining = max(capacity - sum(allocation.values()), 0.0)
        order = sorted(group, key=lambda r: -allocation[r.id])
        method = "nash"
    results = [
        {
            "id": r.id,
            "actor": r.actor,
            "mandate": mandate_text(r, eff[r.id]),
            "baseline": round(baseline[r.id], 4),
            "utility": round(utils[r.id], 4),
            "gain": round(gains[r.id], 4),
        }
        for r in group
    ]
    return allocation, deferred, remaining, order, results, method


def mandate_text(r: Request, eff_min: float) -> str:
    parts = [f"{r.priority}", f"min {r.min_qty:g}", f"max {r.qty:g}"]
    if r.next_ship_value > 0:
        parts.append(f"next ship worth {round(r.next_ship_value * 100)}%")
    else:
        parts.append("cannot wait")
    if r.yield_to_medical and eff_min < r.min_qty:
        parts.append(f"yields {r.min_qty - eff_min:g} to medical")
    return ", ".join(parts)


def needs_met(group: list[Request], allocation: dict[str, float], deferred: dict[str, float]) -> int:
    return sum(
        1
        for r in group
        if allocation.get(r.id, 0.0) + deferred.get(r.id, 0.0) >= effective_min(r, group) - EPS
    )


def resolve(group: list[Request], capacity: float, policy: str, divisible: bool) -> dict:
    ordered, seed = lottery(group)
    deferred: dict[str, float] = {}
    envoys: list[dict] = []
    method = ""
    if policy == "envoys":
        allocation, deferred, remaining, ordered, envoys, method = _envoys(ordered, capacity, divisible)
    elif policy == "needs":
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
        "envoys": envoys,
        "method": method,
    }


def settle(requests: list[Request], capacity: float, policy: str = "envoys", divisible: bool = True):
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
                "envoys": result["envoys"],
                "method": result["method"],
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
