"""Stage 6.8 blind inference pipeline (task brief sections 7-16).

Order, enforced by construction:
    detect candidate  ->  directed predictive influence  ->  Bhat^pred
                      ->  blind challenger certification ->  finite active probing -> Bhat^causal
    -> WRITE EVERYTHING TO DISK
Only then may `run_oracle_reveal.py` be run. This script imports NOTHING that
can compute the FOV graph or B^D: `oracle_68` is not imported, and
`intervention_api_68.FiniteProbe` is a black box that returns numbers only.
`ExactPropagator` is deliberately NOT used here -- it belongs to the reveal.

Usage:
    run_boundary_pipeline.py snapshot     # one timepoint per episode, all valid candidates
    run_boundary_pipeline.py series       # consecutive timepoints, one tracked collective
    run_boundary_pipeline.py gated        # L3: same protocol with edge gates on
"""
from __future__ import annotations

import sys
import time

import numpy as np

from common_68 import dump_json, load_json, DATA_DIR
from episode_data import (make_simulator, run_episode, replicate_window, build_splits,
                          observation_record)
from fov_dynamics import GateParams
from intervention_api_68 import FiniteProbe

import candidate_detection as cd
import spectral_proposal as sp
import predictive_boundary_68 as pb
import probing
from challenger import certify

# ---- frozen Stage 6.8 inference protocol (PROTOCOL_6_8.md sections 7-9) ----
W_WINDOW = 20
R_REPLICATES = 200
R_POOL = 3.5              # observed-position radius of the predictive source pool
SHORTLIST_K = 12
N_BOOT_STABILITY = 6
MAX_TARGETS = 24
K_MAX = 12
PROBE_NEAR_RADIUS = 2.5   # observed-position radius of the probe candidate set
PROBE_ROLLOUTS = 50
PROBE_REPEATS = 6         # independent CRN repeats per (source, alternative heading)
T_SNAPSHOT = 60
SERIES_T = list(range(55, 67))


def infer_one(sim, z_hist, t, I, method: str, gate_params=None, seed: int = 0,
              k_max: int = K_MAX, run_challenger: bool = True,
              channel_state=None) -> dict:
    """Full blind inference for one (episode, timepoint, candidate)."""
    obs = observation_record(sim, z_hist, t)
    I = np.array(sorted(int(x) for x in I))
    rng = np.random.default_rng(seed)

    z_reps = replicate_window(sim, z_hist[t - W_WINDOW + 1], W_WINDOW - 1,
                              n_rep=R_REPLICATES, gate_params=gate_params)
    S = build_splits(z_reps, t)
    targets = pb.interior_targets(I, obs.positions, max_targets=MAX_TARGETS)

    # ---- directed, state-conditioned predictive influence: Ghat^pred_t -----
    t0 = time.time()
    infl = pb.stable_influence_pool(targets, I, obs.positions, S.tr_prev, S.tr_next,
                                    S.va_prev, S.va_next, n_boot=N_BOOT_STABILITY,
                                    shortlist_k=SHORTLIST_K, r_pool=R_POOL, rng=rng)
    t_infl = time.time() - t0

    greedy_pool = infl["pool"][:pb.POOL_CAP]
    full_pool_loss = pb.fit_eval(targets, I, greedy_pool, S.tr_prev, S.tr_next,
                                 S.va_prev, S.va_next, obs.positions)
    t0 = time.time()
    B_pred, trace, stop = pb.construct(targets, I, greedy_pool, S.tr_prev, S.tr_next,
                                       S.va_prev, S.va_next, full_pool_loss, k_max=k_max,
                                       positions=obs.positions)
    t_constr = time.time() - t0

    # ---- blind certification (separate from construction) -----------------
    cert = None
    if run_challenger:
        exterior = [j for j in range(sim.nn) if j not in set(I.tolist())]
        d = np.sqrt(((obs.positions[exterior][:, None, :] - obs.positions[I][None, :, :]) ** 2).sum(-1))
        near_ext = [j for j, dd in zip(exterior, d.min(axis=1)) if dd <= PROBE_NEAR_RADIUS]
        cert = certify(targets, I, B_pred, near_ext, S.tr_prev, S.tr_next,
                       S.va_prev, S.va_next, S.te_prev, S.te_next, S.te_traj, rng=rng,
                       positions=obs.positions)

    # ---- finite active probing (PRIMARY causal estimator) -----------------
    exterior = [j for j in range(sim.nn) if j not in set(I.tolist())]
    dd = np.sqrt(((obs.positions[exterior][:, None, :] - obs.positions[I][None, :, :]) ** 2).sum(-1)).min(axis=1)
    probe_candidates = [int(j) for j, x in zip(exterior, dd) if x <= PROBE_NEAR_RADIUS]
    probe = FiniteProbe(sim, n_rollouts=PROBE_ROLLOUTS, seed=seed + 7,
                        channel_state=channel_state)
    states = [z_hist[t]] * PROBE_REPEATS      # independent CRN draws at the REAL current state
    t0 = time.time()
    causal = probing.probe_sources(probe, I, probe_candidates, states, rng=rng)
    t_probe = time.time() - t0

    return dict(
        t=t, method=method, I=I.tolist(), I_size=len(I), targets=targets.tolist(),
        predictive=dict(pool=infl["pool"], score=infl["score"],
                        selection_frequency=infl["selection_frequency"],
                        directed_graph=infl["directed_graph"],
                        B_pred=B_pred, trace=trace, stop_reason=stop,
                        full_pool_loss=full_pool_loss),
        certification=cert,
        causal=dict(B_causal=causal["B_causal"],
                    C={int(k): dict(C_do=v["C_do"], ci_lo=v["ci_lo"], ci_hi=v["ci_hi"],
                                    n_samples=v["n_samples"]) for k, v in causal["C"].items()},
                    influence_matrix=probing.influence_matrix(causal, I),
                    probe_candidates=probe_candidates,
                    budget=probe.budget()),
        timing=dict(influence_s=t_infl, construct_s=t_constr, probe_s=t_probe),
    )


def _episodes(op, which):
    """Episode scope per mode. L3 ('gated') is a SECONDARY robustness condition
    (task brief section 5) and is deliberately run at reduced scope."""
    if which == "snapshot":
        return op["dev_seeds"][:4] + op["heldout_seeds"][:4]
    if which == "gated":
        return op["dev_seeds"][:3] + op["heldout_seeds"][:3]
    return op["dev_seeds"][:2]


def main(mode: str, shard: int = 0, n_shards: int = 1):
    screen = load_json(DATA_DIR / "episode_screen.json")
    op = screen["ops"]["OP1"]
    sim = make_simulator(op["nn"], op["beta"], op["s"])
    gate_params = GateParams(**load_json(DATA_DIR / "gate_choice.json")["chosen"]) \
        if mode == "gated" else None
    tag = mode
    suffix = "" if n_shards == 1 else f"__shard{shard}"

    out = dict(protocol=f"stage6_8 blind inference pipeline [{mode}]",
               operating_point={k: op[k] for k in ("nn", "beta", "s")},
               settings=dict(W_WINDOW=W_WINDOW, R_REPLICATES=R_REPLICATES, R_POOL=R_POOL,
                             SHORTLIST_K=SHORTLIST_K, N_BOOT_STABILITY=N_BOOT_STABILITY,
                             MAX_TARGETS=MAX_TARGETS, K_MAX=K_MAX,
                             PROBE_NEAR_RADIUS=PROBE_NEAR_RADIUS,
                             PROBE_ROLLOUTS=PROBE_ROLLOUTS, PROBE_REPEATS=PROBE_REPEATS),
               gate_params=(dict(p01=gate_params.p01, p10=gate_params.p10) if gate_params else None),
               dev_seeds=op["dev_seeds"], heldout_seeds=op["heldout_seeds"], runs=[])

    seeds = _episodes(op, mode)[shard::n_shards]
    for seed in seeds:
        res = run_episode(sim, seed, nt=max(SERIES_T) + 2, gate_params=gate_params,
                          record_oracle=(gate_params is not None))
        ts = [T_SNAPSHOT] if mode != "series" else SERIES_T
        prev_I = None
        for t in ts:
            obs = observation_record(sim, res.z_hist, t)
            ok_a, _ = cd.propose(obs)
            ok_s, _ = sp.propose(obs)
            if mode == "series":
                # follow the single largest-overlap continuation of one collective
                if prev_I is None:
                    picks = [(ok_a[len(ok_a) // 2], "affinity_louvain")] if ok_a else []
                else:
                    best = max(ok_a, key=lambda c: len(set(c.members.tolist()) & prev_I),
                               default=None)
                    picks = [(best, "affinity_louvain")] if best is not None else []
            elif mode == "gated":
                picks = [(c, "affinity_louvain") for c in ok_a[:1]]
            else:
                picks = [(c, "affinity_louvain") for c in ok_a[:2]]
                picks += [(c, "spectral_coherence") for c in ok_s[:1]]
            for cand, meth in picks:
                if cand is None:
                    continue
                r = infer_one(sim, res.z_hist, t, cand.members, meth,
                              gate_params=gate_params, seed=seed,
                              run_challenger=(mode != "series"),
                              channel_state=(res.gate_hist[t] if res.gate_hist is not None else None))
                r.update(seed=seed, candidate_size=cand.size, coherence=cand.coherence,
                         compactness=cand.compactness)
                out["runs"].append(r)
                if mode == "series":
                    prev_I = set(cand.members.tolist())
                print(f"seed {seed:<4} t={t:<3} {meth:<19} |I|={cand.size:<4} "
                      f"|Bpred|={len(r['predictive']['B_pred']):<3} ({r['predictive']['stop_reason']}) "
                      f"|Bcausal|={len(r['causal']['B_causal']):<3} "
                      f"suff={None if not r['certification'] else r['certification']['predictively_sufficient_rel_challenger_class']} "
                      f"[{sum(r['timing'].values()):.0f}s]", flush=True)
                dump_json(out, DATA_DIR / f"boundary_inference__{tag}{suffix}.json")
    dump_json(out, DATA_DIR / f"boundary_inference__{tag}{suffix}.json")
    print("wrote", DATA_DIR / f"boundary_inference__{tag}{suffix}.json")


def merge_shards(tag: str, n_shards: int):
    """Concatenate sharded runs into the single canonical file. Sharding is a
    pure parallelization of the seed loop -- shard k takes seeds[k::n_shards] --
    so the merged file is identical in content to an unsharded run."""
    base = None
    for k in range(n_shards):
        d = load_json(DATA_DIR / f"boundary_inference__{tag}__shard{k}.json")
        if base is None:
            base = d
        else:
            base["runs"].extend(d["runs"])
    base["runs"].sort(key=lambda r: (r["seed"], r["method"], r["t"]))
    base["n_shards_merged"] = n_shards
    dump_json(base, DATA_DIR / f"boundary_inference__{tag}.json")
    print(f"merged {n_shards} shards -> {len(base['runs'])} runs")


if __name__ == "__main__":
    _mode = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    if _mode == "merge":
        merge_shards(sys.argv[2], int(sys.argv[3]))
    else:
        main(_mode,
             int(sys.argv[2]) if len(sys.argv) > 2 else 0,
             int(sys.argv[3]) if len(sys.argv) > 3 else 1)
