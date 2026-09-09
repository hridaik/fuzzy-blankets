"""Stage 6.10 Parts E + J -- the uncontrolled reference pass.

One pass over UNCONTROLLED episodes at the frozen operating regime, producing
the two reference objects that later parts are scored against:

  Part E  the thingness landscape -- (C, G, L, D) for every detected candidate,
          which is what percentile ranks are taken against, plus the frozen
          "clear clump stratum" thresholds.
  Part J  the identity validity envelope -- what tracked lineages do on their
          own over the control horizon.

No actuator is forced anywhere in this file, no arm is run, and no target
heading exists here. This is a hard requirement: thresholds must be frozen on
uncontrolled data, so control success is not computable in this module.
"""
from __future__ import annotations

import sys
import time

import numpy as np

from common_610 import DATA_DIR, dump_json
from episode_data import (make_simulator, run_episode, observation_record,
                          replicate_window, build_splits)
import candidate_detection as cd
import reference_truth as rt
from morphology import morphology
from thingness import (coherence, integration_and_leakage, exterior_contrast,
                       add_percentile_ranks, SIZE_TOL)
from identity_scoring import lineage_statistics, build_envelope, calibrate_envelope
from closed_loop import detect, qualifying_start, MIN_SIZE, MAX_SIZE

T0 = 60
HORIZON = 24                  # >= any Part H control horizon
ENV_HORIZONS = (12, 24)       # envelope is built at the horizon it will score
WINDOW = 12                   # heading window for C
N_REP = 120                   # replicate rollouts from z[T0] for G and L
REP_STEPS = 6                 # steps per replicate
RING = 1                      # exterior ring thickness (cardinal dilation)
CLUMP_STRATUM_Q = 0.90        # frozen here, on uncontrolled data only


def exterior_ring(I, L, k=RING):
    inside = set(int(x) for x in I)
    ring = set()
    frontier = set(inside)
    for _ in range(k):
        nxt = set()
        for a in frontier:
            ar, ac = a % L, a // L
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = ar + dr, ac + dc
                if 0 <= nr < L and 0 <= nc < L:
                    b = nc * L + nr
                    if b not in inside and b not in ring:
                        nxt.add(b)
        ring |= nxt
        frontier = nxt
    return sorted(ring)


def main(beta, s, seeds, tag="main"):
    nn, L = 400, 20
    sim = make_simulator(nn, beta, s)
    out = dict(protocol="stage6_10 Parts E+J -- uncontrolled reference",
               regime=dict(nn=nn, beta=beta, s=s), t0=T0, horizon=HORIZON,
               window=WINDOW, ring=RING, clump_stratum_q=CLUMP_STRATUM_Q,
               controlled=False, candidates=[], lineages=[])

    for seed in seeds:
        t = time.time()
        res = run_episode(sim, seed, nt=T0 + HORIZON + 2, record_oracle=False)
        zh = res.z_hist
        ok, _ = cd.propose(observation_record(sim, zh[:T0 + 1], T0))
        # G and L are held-out quantities: fit on train replicates from z[T0],
        # score on the disjoint test replicates.
        reps = replicate_window(sim, zh[T0], REP_STEPS, n_rep=N_REP,
                                seed_offset=900_000 + 1000 * seed)
        sp = build_splits(reps, T0)

        # ---- Part E: the whole landscape, snakes included --------------
        for ci, c in enumerate(ok):
            I = np.array(sorted(int(x) for x in c.members))
            if not (MIN_SIZE <= len(I) <= MAX_SIZE):
                continue
            m = morphology(I, L)
            B = [int(x) for x in rt.structural_interface(sim, zh[T0], I)]
            ring = exterior_ring(I, L)
            G, Lk = integration_and_leakage(sp.tr_prev, sp.tr_next,
                                            sp.te_prev, sp.te_next,
                                            I, B, ring, seed=seed,
                                            positions=sim.positions)
            out["candidates"].append(dict(
                seed=seed, cand=ci, size=len(I),
                C=coherence(zh[T0 - WINDOW:T0 + 1], I), G=G, L=Lk,
                D=exterior_contrast(zh[T0], I, ring),
                q_clump=m["q_clump"], n_components=m["n_components"],
                aspect_ratio=m["aspect_ratio"], bbox_fill=m["bbox_fill"],
                B_size=len(B)))

        # ---- Part J: what an untouched lineage does over the horizon ---
        # The start state is chosen by the SAME qualifying rule as the
        # controlled episodes (moderate size, single component, most clump-like)
        # so the envelope is calibrated on comparable lineages.
        I_t = qualifying_start(ok, L)
        if I_t is None:
            print(f"seed {seed:<4} no qualifying start; skipped", flush=True)
            continue
        I_seq, z_seq = [], []
        for step in range(HORIZON + 1):
            cur = T0 + step
            if step:
                I_t, _ = detect(sim, zh, cur, I_t)
            I_seq.append(I_t.copy()); z_seq.append(zh[cur])
        # The envelope must be built at the SAME horizon it will score: a
        # 24-step drift bound is far too loose for a 12-step episode.
        row = dict(seed=seed, by_horizon={})
        for hz in ENV_HORIZONS:
            n = min(hz + 1, len(I_seq))
            row["by_horizon"][str(hz)] = lineage_statistics(I_seq[:n], z_seq[:n], L)
        st = row["by_horizon"][str(HORIZON)]
        out["lineages"].append(row)
        print(f"seed {seed:<4} cands={len(ok):<3} |I0|={st['initial_size']:<3} "
              f"minJ={st['min_step_jaccard']:.2f} J0={st['final_jaccard_to_I0']:.2f} "
              f"sz={st['final_size_ratio']:.2f} Q={st['final_q_clump']:.2f} "
              f"comp={st['max_n_components']} [{time.time()-t:.0f}s]", flush=True)
        dump_json(out, DATA_DIR / f"uncontrolled_reference__{tag}.json")

    # Calibration / validation split of the uncontrolled lineages. The split is
    # by seed order, fixed, and made before any envelope is built.
    rows = out["lineages"]
    half = len(rows) // 2
    out["envelope_split"] = dict(calibration=[r["seed"] for r in rows[:half]],
                                 validation=[r["seed"] for r in rows[half:]])
    out["validity_envelope_by_horizon"] = {}
    for hz in ENV_HORIZONS:
        cal = [r["by_horizon"][str(hz)] for r in rows[:half]]
        val = [r["by_horizon"][str(hz)] for r in rows[half:]]
        out["validity_envelope_by_horizon"][str(hz)] = calibrate_envelope(cal, val)
    out["validity_envelope"] = out["validity_envelope_by_horizon"][str(HORIZON)]
    add_percentile_ranks(out["candidates"])
    out["percentile_rank_spec"] = dict(
        size_tolerance=SIZE_TOL,
        comparable="same cardinal component count, area within +-25%",
        axes=["C", "G", "L", "D"])
    qs = [c["q_clump"] for c in out["candidates"]]
    out["clump_stratum_threshold"] = float(np.quantile(qs, CLUMP_STRATUM_Q)) if qs else float("nan")
    out["n_in_clump_stratum"] = int(sum(q >= out["clump_stratum_threshold"] for q in qs))
    dump_json(out, DATA_DIR / f"uncontrolled_reference__{tag}.json")

    for hz in ENV_HORIZONS:
        e = out["validity_envelope_by_horizon"][str(hz)]
        c = e["calibration"]
        print(f"\nVALIDITY ENVELOPE, horizon {hz}  (per-axis q={c['chosen_q']}%, "
              f"joint pass on held-out uncontrolled lineages "
              f"{c['achieved_joint_pass']:.2f}, target {c['target_joint_pass']:.2f}"
              f"{'' if c['met_target'] else '  -- TARGET NOT MET'})")
        for k, v in e["lower"].items():
            print(f"  {k:<24} >= {v:.3f}")
        for k, v in e["upper"].items():
            print(f"  {k:<24} <= {v:.3f}")
        print("  grid: " + "  ".join(f"q{r['q']}->{r['joint_pass_rate']:.2f}"
                                     for r in c["grid_trace"]))
    print(f"\nthingness landscape: {len(out['candidates'])} candidates "
          f"(snakes retained; clump stratum Q >= {out['clump_stratum_threshold']:.3f}, "
          f"n={out['n_in_clump_stratum']})")


if __name__ == "__main__":
    main(0.4, 0.75, list(range(200, 260)), sys.argv[1] if len(sys.argv) > 1 else "main")
