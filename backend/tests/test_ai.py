from app.engine import Engine
from app.intent import parse_rules
from app.models import NeedSpec, RequestIn, Resource, ScenarioIn
from app.narrate import guardrail_ok

L = 600.0
CLINIC = "We need at least 250 kg of medical supplies before the March launch window. Anything above 300 kg is useless."
FREIGHT = "We would like 400 kg of cargo space, but we can wait for the next ship if needed."


def test_rules_parse_clinic():
    needs, _ = parse_rules(CLINIC)
    assert (needs.min_qty, needs.max_qty, needs.category, needs.can_defer) == (250, 300, "medical", False)


def test_rules_parse_freight():
    needs, _ = parse_rules(FREIGHT)
    assert (needs.min_qty, needs.max_qty, needs.category, needs.can_defer) == (400, 400, "commercial", True)


def make(policy="needs"):
    return Engine(ScenarioIn(date="2040-01-01", policy=policy, resource=Resource(capacity=500)), L, False)


def book(e, node, actor, needs, at):
    return e.submit(RequestIn(node=node, actor=actor, qty=needs.max_qty, needs=needs), at=at)


def test_needs_aware_beats_lottery_on_needs_met():
    e = make()
    book(e, "earth", "Helios Freight", NeedSpec(min_qty=400, max_qty=400, category="commercial", can_defer=True), 0)
    book(e, "mars", "Jezero Clinic", NeedSpec(min_qty=250, max_qty=300, category="medical", can_defer=False), 200)
    s = e.snapshot(at=3 * L)
    rc = s["receipts"][0]
    assert rc["allocation"]["M-1"] == 300
    assert rc["allocation"]["E-1"] == 200
    assert rc["deferred"] == {"E-1": 200}
    assert rc["needs_met"] == 2
    assert rc["needs_met"] >= rc["lottery"]["needs_met"]
    assert s["nodes"]["earth"]["hash"] == s["nodes"]["mars"]["hash"]


def test_ghost_radar_predicts_unseen_requests():
    e = make()
    s = e.snapshot(at=L)
    radar = s["nodes"]["earth"]["ghost"]
    assert radar["planet"] == "mars"
    assert 0 < radar["p_at_least_one"] < 1
    assert radar["window_end"] - radar["window_start"] == L
    assert s["nodes"]["earth"]["tie_risk"] == radar["p_at_least_one"]


def test_forecast_gives_a_range_for_provisional_bookings():
    e = make()
    book(e, "earth", "Helios Freight", NeedSpec(min_qty=400, max_qty=400, category="commercial", can_defer=True), 100)
    f = e.snapshot(at=200)["nodes"]["earth"]["forecast"]["E-1"]
    assert f["low"] <= f["high"] == 400


def test_envoys_both_beat_the_lottery():
    e = make(policy="envoys")
    book(e, "earth", "Helios Freight", NeedSpec(min_qty=400, max_qty=400, category="commercial", can_defer=True, next_ship_value=0.7), 0)
    book(e, "mars", "Jezero Clinic", NeedSpec(min_qty=250, max_qty=300, category="medical"), 200)
    s = e.snapshot(at=3 * L)
    rc = s["receipts"][0]
    assert len(rc["envoys"]) == 2
    assert all(env["gain"] >= 0 for env in rc["envoys"])
    assert rc["allocation"]["M-1"] >= 250
    assert s["nodes"]["earth"]["hash"] == s["nodes"]["mars"]["hash"]


def test_rules_parse_yield_to_medical():
    needs, _ = parse_rules("We want 400 kg and can wait for the next ship. We can give up 50 kg for a medical emergency.")
    assert needs.can_defer and needs.next_ship_value == 0.7
    assert needs.yield_to_medical and needs.yield_max_qty == 50


def test_guardrail_rejects_invented_numbers():
    facts = '{"receives_now": 300, "guaranteed_next_ship": 200}'
    assert guardrail_ok("The clinic receives 300 kg and freight 200 kg next ship.", facts)
    assert not guardrail_ok("The clinic receives 350 kg.", facts)


def test_yield_clause_does_not_change_own_category():
    needs, _ = parse_rules("We would like 400 kg of cargo space. We can wait for the next ship for part of it, and we can give up 50 kg for a medical emergency.")
    assert needs.category == "commercial"
    assert needs.yield_to_medical and needs.yield_max_qty == 50
