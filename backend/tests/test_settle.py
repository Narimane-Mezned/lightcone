from app.engine import Engine
from app.fairness import run_fairness
from app.models import RequestIn, Resource, ScenarioIn

L = 600.0


def make_engine(policy="lottery", capacity=500, divisible=True):
    scenario = ScenarioIn(
        date="2040-01-01",
        policy=policy,
        resource=Resource(capacity=capacity, divisible=divisible),
    )
    return Engine(scenario, one_way_s=L, conjunction=False)


def book(engine, node, qty, at, priority="commercial", actor="test"):
    return engine.submit(RequestIn(node=node, actor=actor, qty=qty, priority=priority), at=at)


def test_ordered_requests_are_first_come_first_served():
    e = make_engine()
    book(e, "earth", 400, at=0)
    book(e, "mars", 300, at=L + 10)
    s = e.snapshot(at=3 * L)
    assert s["receipts"] == []
    assert s["nodes"]["mars"]["allocations"] == {"E-1": 400, "M-1": 100}


def test_true_tie_is_detected():
    e = make_engine()
    book(e, "earth", 400, at=0)
    book(e, "mars", 300, at=240)
    s = e.snapshot(at=3 * L)
    assert len(s["receipts"]) == 1
    assert s["receipts"][0]["tie"] == ["E-1", "M-1"]
    assert sum(s["nodes"]["earth"]["allocations"].values()) == 500


def test_both_planets_reach_the_same_result():
    e = make_engine()
    book(e, "earth", 400, at=0)
    book(e, "mars", 300, at=240)
    book(e, "earth", 50, at=300)
    s = e.snapshot(at=4 * L)
    assert s["nodes"]["earth"]["hash"] == s["nodes"]["mars"]["hash"]


def test_prorata_splits_capacity():
    e = make_engine(policy="prorata")
    book(e, "earth", 400, at=0)
    book(e, "mars", 600, at=100)
    s = e.snapshot(at=3 * L)
    assert s["nodes"]["earth"]["allocations"] == {"E-1": 200, "M-1": 300}


def test_priority_beats_commercial_in_a_tie():
    e = make_engine(policy="priority")
    book(e, "earth", 500, at=0, priority="commercial")
    book(e, "mars", 500, at=100, priority="medical")
    s = e.snapshot(at=3 * L)
    assert s["nodes"]["earth"]["allocations"]["M-1"] == 500


def test_status_becomes_final_after_round_trip():
    e = make_engine()
    out = book(e, "earth", 100, at=0)
    assert out["status"] == "provisional"
    s = e.snapshot(at=2 * L + 1)
    assert s["nodes"]["earth"]["log"][0]["status"] == "final"


def test_naive_earth_server_favours_earth():
    e = make_engine()
    book(e, "mars", 400, at=0)
    book(e, "earth", 400, at=300)
    s = e.snapshot(at=3 * L)
    assert s["naive_allocations"]["E-1"] == 400


def test_fairness_lab_is_reproducible():
    a = run_fairness(L, trials=2000)
    b = run_fairness(L, trials=2000)
    assert a == b
    assert a["earth_server_mars_win"] < a["lightcone_mars_win"]
