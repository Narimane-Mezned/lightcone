import json
from pathlib import Path

import numpy as np

SOL_HOURS = 24.66
BIN_S = 600
SOLS = 365
OUT = Path(__file__).resolve().parent / "app" / "ghost_model.json"


def true_rate_per_hour(planet: int, hour: np.ndarray, days_to_launch: np.ndarray) -> np.ndarray:
    base = np.where(planet == 1, 0.8, 1.2)
    daily = 1 + 0.6 * np.sin(2 * np.pi * (hour - 9) / SOL_HOURS)
    rush = 1 + 4 * np.exp(-days_to_launch / 3)
    return base * daily * rush


def features(planet, hour, days_to_launch) -> np.ndarray:
    planet = np.asarray(planet, dtype=float)
    hour = np.asarray(hour, dtype=float)
    days_to_launch = np.asarray(days_to_launch, dtype=float)
    angle = 2 * np.pi * hour / SOL_HOURS
    return np.column_stack([
        np.ones_like(hour),
        np.sin(angle),
        np.cos(angle),
        np.sin(2 * angle),
        np.cos(2 * angle),
        np.exp(-days_to_launch / 3),
        np.exp(-days_to_launch / 10),
        days_to_launch / 365,
        planet,
    ])


def simulate(rng: np.random.Generator):
    rows = []
    bins_per_sol = int(SOL_HOURS * 3600 // BIN_S)
    for planet in (0, 1):
        for sol in range(SOLS):
            days_to_launch = np.full(bins_per_sol, SOLS - sol, dtype=float)
            hour = (np.arange(bins_per_sol) * BIN_S / 3600) % SOL_HOURS
            lam = true_rate_per_hour(planet, hour, days_to_launch) * BIN_S / 3600
            counts = rng.poisson(lam)
            rows.append((np.full(bins_per_sol, planet), hour, days_to_launch, counts))
    planet = np.concatenate([r[0] for r in rows])
    hour = np.concatenate([r[1] for r in rows])
    dtl = np.concatenate([r[2] for r in rows])
    counts = np.concatenate([r[3] for r in rows])
    return planet, hour, dtl, counts


def fit_poisson(X: np.ndarray, y: np.ndarray, iters: int = 30) -> np.ndarray:
    beta = np.zeros(X.shape[1])
    beta[0] = np.log(y.mean() + 1e-9)
    for _ in range(iters):
        mu = np.exp(X @ beta)
        grad = X.T @ (y - mu)
        hess = X.T @ (X * mu[:, None]) + 1e-6 * np.eye(X.shape[1])
        step = np.linalg.solve(hess, grad)
        beta += step
        if np.abs(step).max() < 1e-8:
            break
    return beta


def deviance(y: np.ndarray, mu: np.ndarray) -> float:
    term = np.where(y > 0, y * np.log(np.where(y > 0, y, 1) / mu), 0.0)
    return float(2 * np.sum(term - (y - mu)))


def main() -> None:
    rng = np.random.default_rng(2040)
    planet, hour, dtl, counts = simulate(rng)
    X = features(planet, hour, dtl)
    idx = rng.permutation(len(counts))
    split = int(0.8 * len(idx))
    train, test = idx[:split], idx[split:]

    beta = fit_poisson(X[train], counts[train])
    mu_model = np.exp(X[test] @ beta)
    mu_naive = np.full(len(test), counts[train].mean())
    y = counts[test]

    lam_true = true_rate_per_hour(planet[test], hour[test], dtl[test]) * BIN_S / 3600
    rush = dtl[test] <= 3
    metrics = {
        "train_bins": int(len(train)),
        "test_bins": int(len(test)),
        "test_deviance_model": round(deviance(y, mu_model), 1),
        "test_deviance_naive_constant": round(deviance(y, mu_naive), 1),
        "deviance_explained_vs_naive": round(1 - deviance(y, mu_model) / deviance(y, mu_naive), 4),
        "mae_rate_model": round(float(np.mean(np.abs(mu_model - lam_true))), 5),
        "mae_rate_naive": round(float(np.mean(np.abs(mu_naive - lam_true))), 5),
        "mae_rate_model_rush": round(float(np.mean(np.abs(mu_model[rush] - lam_true[rush]))), 5),
        "mae_rate_naive_rush": round(float(np.mean(np.abs(mu_naive[rush] - lam_true[rush]))), 5),
    }

    kg_rng = np.random.default_rng(7)
    mean_kg = {
        "earth": round(float(np.mean(kg_rng.lognormal(np.log(220), 0.5, 20000))), 1),
        "mars": round(float(np.mean(kg_rng.lognormal(np.log(180), 0.5, 20000))), 1),
    }

    model = {
        "description": "Poisson regression of booking requests per 10-minute bin, trained on one simulated year of Earth and Mars colony traffic.",
        "features": ["bias", "sin(sol)", "cos(sol)", "sin(2 sol)", "cos(2 sol)", "exp(-days_to_launch/3)", "exp(-days_to_launch/10)", "days_to_launch/365", "is_mars"],
        "bin_s": BIN_S,
        "sol_hours": SOL_HOURS,
        "coefficients": [round(float(b), 6) for b in beta],
        "mean_kg": mean_kg,
        "metrics": metrics,
        "data": "synthetic: no real interplanetary booking traffic exists yet",
    }
    OUT.write_text(json.dumps(model, indent=2))
    print(json.dumps(metrics, indent=2))
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
