import random


def run_fairness(one_way_s: float, trials: int = 10000, window_s: float = 1800.0, seed: int = 42) -> dict:
    rng = random.Random(seed)
    earth_server = mars_server = lightcone = ties = 0
    for _ in range(trials):
        t_earth = rng.uniform(0, window_s)
        t_mars = rng.uniform(0, window_s)
        if t_mars + one_way_s < t_earth:
            earth_server += 1
        if t_mars < t_earth + one_way_s:
            mars_server += 1
        if abs(t_earth - t_mars) < one_way_s:
            ties += 1
            if rng.random() < 0.5:
                lightcone += 1
        elif t_mars < t_earth:
            lightcone += 1
    return {
        "trials": trials,
        "window_s": window_s,
        "earth_server_mars_win": round(earth_server / trials, 4),
        "mars_server_mars_win": round(mars_server / trials, 4),
        "lightcone_mars_win": round(lightcone / trials, 4),
        "tie_rate": round(ties / trials, 4),
    }
