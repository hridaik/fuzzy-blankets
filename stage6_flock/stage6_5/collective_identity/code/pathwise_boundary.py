"""Part 6: pathwise one-step boundary-screening diagnostic L_t^{(1)}.

Direct Monte-Carlo exterior-corruption test, reusing Stage 6's OWN validated
method (STAGE6_SYNTHESIS.md Part H / H1-H2: "confirmed... by empirically
corrupting everything outside it with zero effect", itself described there
as "mean-field Monte-Carlo marginalization") rather than fitting a
regression per timestep. A regression-based estimate (Part 1's method) would
need, for each t, its own classifier fit from samples AT THAT TRANSITION
ONLY -- and because I_t/B_t change bird identity every step under I^L/I^F,
those samples cannot be pooled across t (a per-t classifier would need its
own conditioning-set shape). A workable per-t sample size (tens, not
hundreds) is nowhere near enough to fit a several-hundred-parameter
multinomial classifier, so this diagnostic uses direct intervention on the
simulator instead: from a bird's realized state at time t, hold
X_{I_t,t}, X_{B_t,t} fixed at their observed values, redraw
X_{E_t,t} to iid-uniform, and see how much the resulting one-step-ahead
distribution of X_{I_t,t+1} moves relative to the honest (uncorrupted)
one-step-ahead distribution -- a direct Monte-Carlo estimate of
I(X_{I_t,t+1}; X_{E_t,t} | X_{I_t,t}, X_{B_t,t}), not an exact one, matching
Part 6's own instruction not to attempt an exact CMI estimate.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))
from flock_sim.simulation import run_simulation  # noqa: E402

NU = 4
EPS = 1e-3  # Laplace-style smoothing for the empirical per-bird next-heading distribution


def _empirical_dist(samples: np.ndarray, nu: int = NU) -> np.ndarray:
    counts = np.bincount(samples, minlength=nu).astype(float)
    counts += EPS
    return counts / counts.sum()


def kl(p: np.ndarray, q: np.ndarray) -> float:
    return float(np.sum(p * (np.log(p) - np.log(q))))


def one_step_leakage(z_t: np.ndarray, I_t: np.ndarray, B_t: np.ndarray, nn: int, lattice,
                      n_honest: int, n_corrupt: int, seed_offset: int,
                      rng: np.random.Generator) -> dict:
    """L_t^{(1)} proxy: mean over i in I_t of
    KL(p_honest(X_{i,t+1}) || p_corrupted(X_{i,t+1})), where 'corrupted'
    redraws every exterior-outside-(I_t U B_t) bird's heading to
    iid-uniform at t, immediately before ONE simulated step."""
    I_set = set(int(i) for i in I_t.tolist())
    B_set = set(int(b) for b in B_t.tolist())
    E_ids = np.array([j for j in range(nn) if j not in I_set and j not in B_set], dtype=int)

    honest_next = np.zeros((n_honest, len(I_t)), dtype=int)
    for r in range(n_honest):
        res = run_simulation(nn=nn, nt=1, seed=seed_offset + r, init_z=z_t, lattice=lattice)
        honest_next[r] = res.z_hist[1][I_t]

    corrupt_next = np.zeros((n_corrupt, len(I_t)), dtype=int)
    for r in range(n_corrupt):
        z_c = z_t.copy()
        if len(E_ids):
            z_c[E_ids] = rng.integers(0, NU, size=len(E_ids))
        res = run_simulation(nn=nn, nt=1, seed=seed_offset + 10_000 + r, init_z=z_c, lattice=lattice)
        corrupt_next[r] = res.z_hist[1][I_t]

    kls = []
    for k in range(len(I_t)):
        p_h = _empirical_dist(honest_next[:, k])
        p_c = _empirical_dist(corrupt_next[:, k])
        kls.append(kl(p_h, p_c))
    return dict(mean_leakage=float(np.mean(kls)) if kls else float("nan"),
                max_leakage_bird=float(np.max(kls)) if kls else float("nan"),
                per_bird_kl=kls, n_exterior_corrupted=len(E_ids), boundary_size=len(B_t),
                interior_size=len(I_t))


def pathwise_leakage(z_hist: np.ndarray, I_track: list[np.ndarray], B_track: list[np.ndarray],
                      nn: int, lattice, t_values: list[int], n_honest: int = 30, n_corrupt: int = 30,
                      seed_offset: int = 700_000, rng: np.random.Generator | None = None) -> dict:
    rng = rng or np.random.default_rng(0)
    rows = []
    for t in t_values:
        res = one_step_leakage(z_hist[t], I_track[t], B_track[t], nn, lattice, n_honest, n_corrupt,
                                seed_offset=seed_offset + 1000 * t, rng=rng)
        res["t"] = int(t)
        rows.append(res)
    mean_leakages = [r["mean_leakage"] for r in rows]
    boundary_turnover = [0] + [
        len(set(B_track[t_values[k - 1]].tolist()) ^ set(B_track[t_values[k]].tolist()))
        for k in range(1, len(t_values))
    ]
    return dict(
        rows=rows,
        mean_leakage=float(np.mean(mean_leakages)),
        max_leakage=float(np.max(mean_leakages)),
        boundary_sizes=[r["boundary_size"] for r in rows],
        boundary_turnover=boundary_turnover,
    )


def time_above_tolerance(pathwise_result: dict, tol: float) -> int:
    return sum(1 for r in pathwise_result["rows"] if r["mean_leakage"] > tol)
