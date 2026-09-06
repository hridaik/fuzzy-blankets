"""Part 3: extends v1_mechanism_audit/code/predictive_screening.py's one-step
methodology (M_full vs M_B, Monte-Carlo mean-field marginalization of
everything outside I union B) to a HORIZON SWEEP tau=1..tau_max, for both
B=B^D_0 and B=B^F_0, on 4 development flocks. No control/forcing is applied
anywhere in this script -- this is a pure predictive-screening / information
question about the model's NATURAL (uncontrolled) dynamics.

Efficiency note: for a fixed sampled time t, one length-tau_max Monte Carlo
rollout yields the predictive state at EVERY tau in 1..tau_max along the
way, so tau_max rollouts of length tau_max are not needed -- one rollout of
length tau_max per MC replicate suffices, with intermediate states harvested
at each step.
"""
from __future__ import annotations

import time

import numpy as np

from common_v3 import (
    V3_DIR, dump_json, load_dev_flocks, dynamical_shell, run_simulation, analyze_window,
)
from flock_sim.active_inference import build_model, step as ai_step
from flock_sim.model import ModelParams

FLOCK_SEEDS = [2, 3, 8, 13]
TAU_MAX = 6
N_TRAJ = 40
N_MC = 24
SAMPLE_STRIDE = 2
T_U = 20
EPS = 1e-12


def compute_B_F0(fl):
    """B^F_0: Fiedler boundary at t0, from a window ending at t0. Deterministic
    given (seed, t0): rerunning with nt=t0 reproduces the same z_hist prefix
    as the longer run used to find the flock (RNG draws are sequential)."""
    seed, t0, lattice = fl["seed"], fl["t0"], fl["lattice"]
    res = run_simulation(nn=lattice.nn, nt=t0, seed=seed, lattice=lattice)
    TW = 5
    window = res.z_hist[t0 - TW + 1: t0 + 1]
    sr = analyze_window(window, refclust=fl["I0"])
    return sr.boundary_nodes


def predictive_permeability_for_boundary(fl, B, pm, lattice, rng):
    """Returns per-tau excess log-loss (M_B - M_full) pooled over all
    sampled (trajectory, time, I0-bird) triples."""
    I0, z_t0 = fl["I0"], fl["z_t0"]
    nn = lattice.nn
    I0_set = set(I0.tolist())
    B_set = set(int(b) for b in B.tolist())
    known_set = I0_set | B_set
    unknown_ids = np.array(sorted(set(range(nn)) - known_set))

    trajs = [run_simulation(nn=nn, nt=T_U, seed=800_000 + fl["seed"] * 1000 + r,
                             init_z=z_t0, lattice=lattice, params=pm.params) for r in range(N_TRAJ)]
    z_hists = np.stack([tr.z_hist for tr in trajs])  # (N_TRAJ, T_U+1, nn)

    sample_times = list(range(0, T_U - TAU_MAX + 1, SAMPLE_STRIDE))

    # pooled empirical marginal per timestep (for MC fill-in of unknown birds)
    marginals = {}
    for t in range(T_U + 1):
        zt = z_hists[:, t, :]
        counts = np.array([np.bincount(zt[:, b], minlength=4) for b in range(nn)])
        marginals[t] = (counts.sum(axis=0) + 1.0) / (counts.sum() + 4.0)

    logloss_full = {tau: [] for tau in range(1, TAU_MAX + 1)}
    logloss_B = {tau: [] for tau in range(1, TAU_MAX + 1)}

    for t in sample_times:
        for r in range(N_TRAJ):
            z_now = z_hists[r, t, :]
            z_future = z_hists[r]  # full realized trajectory for this replicate

            # M_full: N_MC forward rollouts from the EXACT true state (average
            # over forward stochastic dynamics only).
            counts_full = {tau: np.zeros((nn, 4)) for tau in range(1, TAU_MAX + 1)}
            for _ in range(N_MC):
                z = z_now.copy()
                for tau in range(1, TAU_MAX + 1):
                    out = ai_step(pm, lattice, z, rng)
                    z = out["z_new"]
                    counts_full[tau][np.arange(nn), z] += 1

            # M_B: N_MC forward rollouts, marginalizing unknown (non I, non B)
            # birds by resampling them from the pooled empirical marginal at
            # t, then letting them evolve under the SAME natural dynamics.
            counts_B = {tau: np.zeros((nn, 4)) for tau in range(1, TAU_MAX + 1)}
            for _ in range(N_MC):
                z = z_now.copy()
                if len(unknown_ids) > 0:
                    z[unknown_ids] = rng.choice(4, size=len(unknown_ids), p=marginals[t])
                for tau in range(1, TAU_MAX + 1):
                    out = ai_step(pm, lattice, z, rng)
                    z = out["z_new"]
                    counts_B[tau][np.arange(nn), z] += 1

            for tau in range(1, TAU_MAX + 1):
                if t + tau > T_U:
                    continue
                p_full = counts_full[tau] / N_MC
                p_B = counts_B[tau] / N_MC
                z_real = z_future[t + tau]
                for i in I0.tolist():
                    logloss_full[tau].append(-np.log(p_full[i, z_real[i]] + EPS))
                    logloss_B[tau].append(-np.log(p_B[i, z_real[i]] + EPS))

    out = {}
    for tau in range(1, TAU_MAX + 1):
        if not logloss_full[tau]:
            continue
        lf = np.array(logloss_full[tau])
        lb = np.array(logloss_B[tau])
        out[tau] = dict(n_samples=len(lf), mean_logloss_full=float(lf.mean()),
                         mean_logloss_B=float(lb.mean()), excess_logloss=float(lb.mean() - lf.mean()))
    return out


def main():
    t_start = time.time()
    params = ModelParams()
    pm = build_model(params)
    rng = np.random.default_rng(555_555)

    flocks = {fl["seed"]: fl for fl in load_dev_flocks()}
    results = []
    for seed in FLOCK_SEEDS:
        fl = flocks[seed]
        lattice, I0 = fl["lattice"], fl["I0"]
        B_D0 = dynamical_shell(lattice, I0)
        B_F0 = compute_B_F0(fl)
        print(f"seed {seed}: |I0|={len(I0)} |B^D_0|={len(B_D0)} |B^F_0|={len(B_F0)}  "
              f"({time.time()-t_start:.1f}s elapsed)")

        res_D = predictive_permeability_for_boundary(fl, B_D0, pm, lattice, rng)
        print(f"  B^D_0 done ({time.time()-t_start:.1f}s elapsed)")
        res_F = predictive_permeability_for_boundary(fl, B_F0, pm, lattice, rng)
        print(f"  B^F_0 done ({time.time()-t_start:.1f}s elapsed)")

        for tau in sorted(res_D):
            print(f"    tau={tau}: excess_logloss B^D={res_D[tau]['excess_logloss']:.5f}  "
                  f"B^F={res_F[tau]['excess_logloss']:.5f}")

        results.append(dict(seed=seed, size_I0=len(I0), size_B_D0=len(B_D0), size_B_F0=len(B_F0),
                             B_D0=B_D0.tolist(), B_F0=B_F0.tolist(),
                             predictive_permeability_B_D0=res_D, predictive_permeability_B_F0=res_F))

    dump_json(dict(tau_max=TAU_MAX, n_traj=N_TRAJ, n_mc=N_MC, sample_stride=SAMPLE_STRIDE,
                    flocks=results), V3_DIR / "data" / "predictive_permeability.json")
    print(f"\nDone in {time.time()-t_start:.1f}s. Wrote data/predictive_permeability.json")


if __name__ == "__main__":
    main()
