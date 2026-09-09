"""Boundary inference in the translating frame (task brief §34).

For gate-passing episodes, runs the same hierarchy Stage 6.8 established --
    I_t  ->  Bhat_t^pred  ->  Bhat_t^causal
-- online, at consecutive timepoints, while the collective moves. Interface
turnover is measured BOTH in world coordinates and relative to the co-moving
frame, so "the interface changed" can be separated from "the interface moved
with the group".

Stage 6.8's inference modules are imported read-only. `oracle_69` quantities
are computed only after the inference results are written to disk.
"""
from __future__ import annotations

import sys
import time

import numpy as np

from common_69 import (ModelParams, dump_json, load_json, DATA_DIR, N_BIRDS, L_BOX,
                       R_RADIUS, V_SPEED, BETA, RHO, OMEGA, UV4)
from moving_flock import MovingFlock
from intervention_api_69 import FiniteProbeMoving, ExactPropagatorMoving, near_exterior
import detect_69 as det

# Stage 6.8 inference modules, read-only
import probing
import predictive_boundary_68 as pb
from heading_stratified import source_pool
from observer import Observation

# Disclosed compute restrictions, fixed before the runs. The moving flock is
# much denser than the lattice (a clustered group puts ~113 birds inside a 2.6
# radius), so the pools are tightened relative to Stage 6.8 and the probe
# budget is smaller; both are stated rather than hidden, and both make the
# inference problem HARDER, not easier.
PROBE_ROLLOUTS = 60
PROBE_REPEATS = 3
PROBE_RADIUS_FACTOR = 1.1     # probe candidates within 1.1*R of the collective
W_WINDOW = 10
R_REPLICATES = 60
R_POOL = 1.9                  # ~1.2*R, still wider than the interaction radius
SHORTLIST_K = 8
MAX_TARGETS = 12
N_BOOT_STABILITY = 4
K_MAX = 12
SERIES_LEN = 6


def replicate_window(mf, r0, z0, n_steps, n_rep, seed_offset=990_000):
    """Repeated observation of the same flock state, as at Stage 6.6-6.8."""
    Z = np.zeros((n_rep, n_steps + 1, mf.N), dtype=int)
    for k in range(n_rep):
        rng = np.random.default_rng(seed_offset + k)
        r, z = r0.copy(), z0.copy()
        Z[k, 0] = z
        for t in range(n_steps):
            r, z, _ = mf.step(r, z, rng)
            Z[k, t + 1] = z
    return Z


def splits_from(Z, split_seed=0):
    n_rep = Z.shape[0]
    rng = np.random.default_rng(split_seed)
    order = rng.permutation(n_rep)
    n_tr, n_va = int(round(0.6 * n_rep)), int(round(0.2 * n_rep))
    def flat(ids):
        p, n = [], []
        for k in ids:
            p.append(Z[k, :-1]); n.append(Z[k, 1:])
        return np.concatenate(p), np.concatenate(n)
    return (flat(order[:n_tr]), flat(order[n_tr:n_tr + n_va]))


def _viable_targets(targets, I, positions):
    """Drop targets for which the predictive machinery is undefined.

    The moving flock is far sparser in places than the lattice: with
    `R_POOL = 1.9` a peripheral bird can have a source pool of size 1, and the
    leave-one-source-out step then fits a model with ZERO features, which
    sklearn rejects. It can also have no interior member inside the pool, which
    leaves `InteriorModel`'s conditioning set empty for the same reason.

    Rather than patch Stage 6.8's frozen inference module -- whose inputs never
    produced either case, so its published numbers are unaffected either way --
    the unusable targets are filtered out here and the count is reported, so the
    restriction is visible instead of silent.
    """
    Iset = set(int(x) for x in I)
    out = []
    for i in targets:
        i = int(i)
        pool = source_pool(positions, i, R_POOL)
        if len(pool) < 2:
            continue
        if not any(int(m) in Iset for m in pool):
            continue
        out.append(i)
    return np.array(sorted(out), dtype=int)


def infer_at(mf, r_t, z_t, I, seed) -> dict:
    """Blind predictive + causal interface at one timepoint."""
    I = np.array(sorted(int(x) for x in I))
    positions = np.asarray(r_t)
    cands = near_exterior(mf, positions, I, radius_factor=PROBE_RADIUS_FACTOR)

    # ---- predictive (blind) ------------------------------------------------
    Z = replicate_window(mf, r_t, z_t, W_WINDOW - 1, R_REPLICATES)
    (trp, trn), (vap, van) = splits_from(Z)
    targets = pb.interior_targets(I, positions, max_targets=MAX_TARGETS,
                                  periphery_radius=1.2 * mf.R)
    targets = _viable_targets(targets, I, positions)
    if len(targets) == 0:
        return dict(I=I.tolist(), I_size=len(I), probe_candidates=cands,
                    B_pred=[], pred_pool=[], pred_stop="no_viable_target",
                    B_causal=[], influence_matrix={}, budget={},
                    timing=dict(pred_s=0.0, causal_s=0.0), skipped_predictive=True)
    t0 = time.time()
    infl = pb.stable_influence_pool(targets, I, positions, trp, trn, vap, van,
                                    n_boot=N_BOOT_STABILITY, shortlist_k=SHORTLIST_K,
                                    r_pool=R_POOL, rng=np.random.default_rng(seed))
    pool = infl["pool"][:pb.POOL_CAP]
    full = pb.fit_eval(targets, I, pool, trp, trn, vap, van, positions)
    B_pred, trace, stop = pb.construct(targets, I, pool, trp, trn, vap, van, full,
                                       k_max=K_MAX, positions=positions)
    t_pred = time.time() - t0

    # ---- causal (finite active probing, blind) -----------------------------
    t0 = time.time()
    probe = FiniteProbeMoving(mf, r_t, n_rollouts=PROBE_ROLLOUTS, seed=seed + 11)
    causal = probing.probe_sources(probe, I, cands, [z_t] * PROBE_REPEATS,
                                   rng=np.random.default_rng(seed + 3))
    t_causal = time.time() - t0
    return dict(I=I.tolist(), I_size=len(I), probe_candidates=cands,
                B_pred=B_pred, pred_pool=infl["pool"], pred_stop=stop,
                n_targets=len(targets), n_targets_dropped=int(MAX_TARGETS - len(targets)),
                B_causal=causal["B_causal"],
                influence_matrix=probing.influence_matrix(causal, I),
                budget=probe.budget(),
                timing=dict(pred_s=t_pred, causal_s=t_causal))


def main():
    gate = load_json(DATA_DIR / "translation_gate.json")
    passing = [e for e in gate["episodes"] if e["passes"]]
    if not passing:
        raise SystemExit("translation gate did not pass; no boundary inference is run")
    seeds = [e["seed"] for e in passing][:2]
    mf = MovingFlock(N=N_BIRDS, L=L_BOX, R=R_RADIUS, v=V_SPEED,
                     params=ModelParams(beta=BETA, precB=RHO, precC=OMEGA))
    out = dict(protocol="stage6_9 boundary inference in the translating frame",
               model=gate["model"], seeds=seeds, runs=[])
    for seed in seeds:
        ep = next(e for e in gate["episodes"] if e["seed"] == seed)
        t0 = ep["t_start"] + 20
        res = mf.run(nt=t0 + SERIES_LEN + 2, seed=seed)
        tracker, prev = None, None
        for t in range(t0, t0 + SERIES_LEN):
            zw = res.z_hist[max(0, t - det.W_AFFINITY + 1):t + 1]
            cands = det.propose(res.r_hist[t], zw, mf.L)
            if not cands:
                continue
            if tracker is None:
                tracker = det.TranslatingTracker(mf.L)
                tracker.start(cands[0], res.r_hist[t], res.z_hist[t], t)
            elif not tracker.update(cands, res.r_hist[t], res.z_hist[t], t):
                break
            I = tracker.state.members
            r = infer_at(mf, res.r_hist[t], res.z_hist[t], I, seed)
            r.update(seed=seed, t=t, centroid=tracker.state.centre.tolist(),
                     record=tracker.records[-1])
            out["runs"].append(r)
            print(f"seed {seed:<3} t={t:<4} |I|={r['I_size']:<4} |Bpred|={len(r['B_pred']):<3} "
                  f"|Bcausal|={len(r['B_causal']):<3} cands={len(r['probe_candidates']):<3} "
                  f"[{r['timing']['pred_s']:.0f}+{r['timing']['causal_s']:.0f}s]", flush=True)
            dump_json(out, DATA_DIR / "boundary_69.json")
    dump_json(out, DATA_DIR / "boundary_69.json")
    print("wrote", DATA_DIR / "boundary_69.json")


if __name__ == "__main__":
    main()
