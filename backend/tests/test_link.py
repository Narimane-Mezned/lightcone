from datetime import date

from app.link import compute_link


def test_light_delay_is_physical():
    info = compute_link(date(2040, 1, 1))
    assert 180 < info["one_way_s"] < 1400
    assert abs(info["round_trip_s"] - 2 * info["one_way_s"]) < 0.2
