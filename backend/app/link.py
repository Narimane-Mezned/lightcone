from datetime import date
from pathlib import Path

from skyfield.api import Loader

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
C_KM_S = 299_792.458
KM_PER_AU = 149_597_870.7
CONJUNCTION_DEG = 2.0

_load = Loader(str(DATA_DIR))
_ts = _load.timescale()
_eph = _load("de421.bsp")
_earth, _mars, _sun = _eph["earth"], _eph["mars"], _eph["sun"]


def compute_link(day: date) -> dict:
    t = _ts.utc(day.year, day.month, day.day)
    observer = _earth.at(t)
    mars_pos = observer.observe(_mars)
    sun_pos = observer.observe(_sun)
    distance_km = mars_pos.distance().km
    one_way_s = distance_km / C_KM_S
    sun_angle = sun_pos.separation_from(mars_pos).degrees
    return {
        "date": day.isoformat(),
        "distance_km": round(distance_km),
        "distance_au": round(distance_km / KM_PER_AU, 4),
        "one_way_s": round(one_way_s, 1),
        "round_trip_s": round(2 * one_way_s, 1),
        "sun_angle_deg": round(sun_angle, 2),
        "conjunction": bool(sun_angle < CONJUNCTION_DEG),
    }
