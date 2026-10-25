import json

from .narrate import ENVOY_SYSTEM, SYSTEM, get_narrative
from .node import Request

PLANET = {"earth": "Earth", "mars": "Mars"}


def fmt(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def _g(x: float) -> str:
    return f"{x:g}"


def build_receipt(tie: dict, policy: str, one_way_s: float, unit: str) -> dict:
    members: list[Request] = tie["members"]
    by_id = {r.id: r for r in members}

    evidence = []
    ordered_by_time = sorted(members, key=lambda r: (r.sim_t, r.id))
    for i, a in enumerate(ordered_by_time):
        for b in ordered_by_time[i + 1:]:
            if a.node != b.node:
                evidence.append({
                    "a": a.id,
                    "b": b.id,
                    "t_a": round(a.sim_t, 1),
                    "t_b": round(b.sim_t, 1),
                    "news_arrival": round(a.sim_t + one_way_s, 1),
                })

    sentences = []
    for e in evidence:
        a, b = by_id[e["a"]], by_id[e["b"]]
        sentences.append(
            f"{a.id} ({PLANET[a.node]}, {fmt(a.sim_t)}) and {b.id} ({PLANET[b.node]}, {fmt(b.sim_t)}) are a true tie: "
            f"news of {a.id} could only reach {PLANET[b.node]} at {fmt(e['news_arrival'])}, after {b.id} was made."
        )

    order = tie["order"]
    allocation = tie["allocation"]
    deferred = tie["deferred"]
    shares = ", ".join(f"{rid} gets {_g(allocation[rid])} {unit}" for rid in order)
    envoys = tie.get("envoys", [])
    if policy == "envoys":
        if tie.get("method") == "nash":
            sentences.append(
                "AI envoys negotiated for their owners (Nash bargaining over the mandates compiled from their own words): "
                f"each accepted only a deal better than its expected lottery outcome. Result: {shares}."
            )
        else:
            sentences.append(f"No deal beat the lottery for everyone, so the needs-aware rule applied. Result: {shares}.")
        for rid, qty in deferred.items():
            sentences.append(f"{rid} is guaranteed {_g(qty)} {unit} with priority on the next ship.")
        for e in envoys:
            sentences.append(
                f"Envoy for {e['actor']}: {round(e['utility'] * 100)}% of its ideal outcome vs {round(e['baseline'] * 100)}% expected from a lottery."
            )
    elif policy == "needs":
        sentences.append(
            "Needs-aware resolution: everyone's minimum first (requests that cannot wait before those that can, "
            f"then medical, science, commercial), the rest shared fairly. Result: {shares}."
        )
        for rid, qty in deferred.items():
            sentences.append(f"{rid} is guaranteed {_g(qty)} {unit} with priority on the next ship.")
        lot = tie["lottery"]
        sentences.append(
            f"Needs met: {tie['needs_met']} of {len(members)} (a plain lottery would meet {lot['needs_met']} of {len(members)})."
        )
    elif policy == "lottery":
        sentences.append(f"Verifiable lottery order: {', then '.join(order)}. Result: {shares}.")
    elif policy == "prorata":
        sentences.append(f"Capacity shared in proportion to the amounts requested: {shares}.")
    else:
        sentences.append(
            f"Priority classes first (medical, science, commercial), lottery inside a class. Order: {', then '.join(order)}. Result: {shares}."
        )
    explanation = " ".join(sentences)

    facts = {
        "light_delay_minutes": round(one_way_s / 60, 1),
        "policy": policy,
        "unit": unit,
        "requests": [
            {
                "id": r.id,
                "planet": PLANET[r.node],
                "requester": r.actor,
                "made_at": fmt(r.sim_t),
                "need_text": r.text or "",
                "minimum": r.min_qty,
                "maximum": r.qty,
                "category": r.priority,
                "can_wait_for_next_ship": r.can_defer,
                "receives_now": allocation.get(r.id, 0.0),
                "guaranteed_next_ship": deferred.get(r.id, 0.0),
                "lottery_would_give": tie["lottery"]["allocation"].get(r.id, 0.0),
            }
            for r in members
        ],
        "needs_met": tie["needs_met"],
        "needs_met_by_lottery": tie["lottery"]["needs_met"],
    }
    if envoys:
        facts["envoys"] = [
            {
                "requester": e["actor"],
                "mandate": e["mandate"],
                "utility_percent": round(e["utility"] * 100),
                "lottery_expected_percent": round(e["baseline"] * 100),
            }
            for e in envoys
        ]
    facts_text = json.dumps(facts)
    key = (tuple(sorted(by_id)), policy, json.dumps(allocation, sort_keys=True), json.dumps(deferred, sort_keys=True))
    narrative, source = get_narrative(key, facts_text, explanation, ENVOY_SYSTEM if policy == "envoys" else SYSTEM)

    return {
        "tie": sorted(by_id),
        "evidence": evidence,
        "policy": policy,
        "seed": tie["seed"],
        "order": order,
        "allocation": allocation,
        "deferred": deferred,
        "needs_met": tie["needs_met"],
        "lottery": tie["lottery"],
        "envoys": envoys,
        "explanation": explanation,
        "narrative": narrative,
        "narrative_source": source,
    }
