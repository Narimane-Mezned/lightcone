import json
import math
from pathlib import Path

MODEL = json.loads((Path(__file__).resolve().parent / "ghost_model.json").read_text())
BETA = MODEL["coefficients"]
SOL_HOURS = MODEL["sol_hours"]
BIN_S = MODEL["bin_s"]
DAYS_TO_LAUNCH = 2.0
START_HOUR = 14.0
STEPS = 24


def _features(planet: str, hour: float, days_to_launch: float) -> list[float]:
    angle = 2 * math.pi * hour / SOL_HOURS
    return [
        1.0,
        math.sin(angle),
        math.cos(angle),
        math.sin(2 * angle),
        math.cos(2 * angle),
        math.exp(-days_to_launch / 3),
        math.exp(-days_to_launch / 10),
        days_to_launch / 365,
        1.0 if planet == "mars" else 0.0,
    ]


def rate_per_s(planet: str, sim_t: float) -> float:
    hour = (START_HOUR + sim_t / 3600) % SOL_HOURS
    x = _features(planet, hour, DAYS_TO_LAUNCH)
    per_bin = math.exp(sum(b * v for b, v in zip(BETA, x)))
    return per_bin / BIN_S


def expected_requests(planet: str, start: float, end: float) -> float:
    if end <= start:
        return 0.0
    dt = (end - start) / STEPS
    return sum(rate_per_s(planet, start + (i + 0.5) * dt) * dt for i in range(STEPS))


def radar(observer: str, now: float, one_way_s: float) -> dict:
    other = "mars" if observer == "earth" else "earth"
    start = max(0.0, now - one_way_s)
    mu = expected_requests(other, start, now)
    count = max(int(mu + 0.5), 1 if 1 - math.exp(-mu) >= 0.3 else 0)
    times = [start + (i + 0.5) * (now - start) / count for i in range(count)] if count else []
    return {
        "planet": other,
        "expected_requests": round(mu, 3),
        "p_at_least_one": round(1 - math.exp(-mu), 3),
        "expected_kg": MODEL["mean_kg"][other],
        "window_start": round(start, 1),
        "window_end": round(now, 1),
        "times": [round(t, 1) for t in times],
    }


def metrics() -> dict:
    return MODEL["metrics"]
