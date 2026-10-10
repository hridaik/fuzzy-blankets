"""Stage 6.10 Part H -- establish controllability BEFORE testing inference.

Uses the full-model control benchmark only. Scans just the two control-resource
variables needed to pose a reasonable task:

    actuator fraction of the current causal interface   f in FRACS
    control horizon                                     T in HORIZONS

and looks for a frozen operating task where the benchmark succeeds RELIABLY BUT
NOT TRIVIALLY -- clearly positive, not ~0%, not ~100% under tiny forcing.

Controller comparison must not run on episodes where full-information control
cannot steer the collective; this script decides which episodes those are.
"""
from __future__ import annotations

import sys
import time

import numpy as np

from common_610 import DATA_DIR, dump_json, load_json, rotate_cw, target_alignment
from episode_data import make_simulator, run_episode, observation_record
import candidate_detection as cd
import reference_truth as rt
import full_model_benchmark as fmb
from morphology import morphology
import closed_loop as cl
from closed_loop import detect, qualifying_start, MIN_SIZE, MAX_SIZE

T0 = 60
FRACS = (0.25, 0.5, 0.75)
HORIZONS = (12, 24)
REINFER_EVERY = 4          # must match run_closed_loop.REINFER_EVERY
THETA, Q_SUPPORT = 0.02, 0.5
SUCCESS_HI, SUCCESS_LO = 0.60, 0.10     # "reliably but not trivially"


def seed_episode(sim, seed, L):
    """A qualifying start: a moderate-size, clump-like, single-component
    candidate at T0. Uses morphology only -- no control outcome."""
    res = run_episode(sim, seed, nt=T0 + 2, record_oracle=False)
    ok, _ = cd.propose(observation_record(sim, res.z_hist, T0))
    I0 = qualifying_start(ok, L)
    if I0 is None:
        return None
    m = morphology(I0, L)
    z0 = res.z_hist[T0]
    h0 = int(np.bincount(z0[I0], minlength=4).argmax())
    return dict(res=res, I0=I0, h0=h0, h_star=rotate_cw(h0), q=m["q_clump"])


# The gate runs the SAME CODE as Part I (delegation below) but on a DIFFERENT
# random stream. Both halves matter and they fix different faults:
#
#   same code    -- the gate cannot drift from the comparison. Two defects of
#                   exactly that shape were found and superseded (a
#                   largest-candidate tracker, then pool/rollout/seed drift).
#   different    -- the stratum is chosen on one draw and every arm, the
#   stream          benchmark included, is measured on an independent one.
#                   Selecting and evaluating on the SAME draw would make the
#                   benchmark's success 1.0 within the stratum by construction,
#                   and every other arm would be compared against a reference
#                   sitting at its selected maximum. That biases the comparison
#                   toward "inference cannot match full model knowledge" for
#                   purely statistical reasons.
#
# `tests/test_gate_matches_part_i.py` pins the code-path equivalence by passing
# `gate_seed(s)` to Part I's loop, so it still asserts bit-for-bit agreement.
GATE_SEED_OFFSET = 900_000


def gate_seed(seed: int) -> int:
    """The control-phase random stream the gate uses, distinct from Part I's."""
    return int(seed) + GATE_SEED_OFFSET


def run_benchmark_episode(sim, res, I0, h_star, horizon, frac, seed, L):
    """The full-model benchmark, online, at a given resource setting.

    DELEGATES to `closed_loop.run_arm` with exactly the arguments Part I uses
    for its benchmark arm, so the gate and the comparison are the same code on
    the same episode with the same random streams. Earlier versions
    reimplemented the loop here and drifted from Part I in three ways at once
    (candidate pool, rollout count, CRN seed), which meant episodes were
    admitted on the strength of a benchmark run that Part I never reproduced.

    Because Part I runs its benchmark arm first, with `budget_schedule=None`,
    this call reproduces that arm bit-for-bit. A consequence worth stating
    plainly: the benchmark's success rate WITHIN the primary stratum is 1.0 by
    construction -- the stratum is defined by it -- so that number is a
    selection artefact and not a measurement. Its identity-validity rate is not,
    since validity plays no part in the selection.
    """
    k_act = max(1, int(round(frac * len(rt.structural_interface(
        sim, res.z_hist[T0], I0)))))
    r = cl.run_arm(sim, res.z_hist[:T0 + 1], "full_model_benchmark", gate_seed(seed), h_star,
                   horizon, k_act, I0, THETA, Q_SUPPORT, budget_schedule=None,
                   reinfer_every=REINFER_EVERY, I_init=I0,
                   # the gate does not read the exact-do reference, and computing
                   # it every step costs ~20s/episode. It does not enter the
                   # benchmark's own decisions, so omitting it here leaves the
                   # run identical to Part I's benchmark arm except for that
                   # unused record -- asserted in tests/test_gate_matches_part_i.py
                   record_reference=False)
    recs = []
    for rec in r["records"]:
        recs.append(dict(step=rec["step"], I_size=rec["I_size"], n_act=rec["n_act"],
                         B_size=rec["B_struct_size"], H=rec["H_current"],
                         H_I0=rec["H_I0"], q_clump=rec["q_clump"],
                         n_components=rec["n_components"]))
    return recs, None


def main(beta, s, seeds, tag="main", only_cell=None):
    sim = make_simulator(400, beta, s)
    L = 20
    out = dict(protocol="stage6_10 Part H -- controllability via the full-model benchmark",
               regime=dict(nn=400, beta=beta, s=s), t0=T0, fracs=list(FRACS),
               horizons=list(HORIZONS),
               bench=dict(delegates_to="closed_loop.run_arm",
                          reinfer_every=REINFER_EVERY, tau=cl.BENCH_TAU,
                          roll=cl.BENCH_ROLL, beam=cl.BENCH_BEAM),
               success_band=[SUCCESS_LO, SUCCESS_HI], episodes=[], cells={})
    eps = []
    for seed in seeds:
        e = seed_episode(sim, seed, L)
        if e is None:
            continue
        eps.append((seed, e))
        out["episodes"].append(dict(seed=seed, I0_size=len(e["I0"]), h0=e["h0"],
                                    h_star=e["h_star"], q_clump=e["q"]))
    print(f"qualifying start states: {len(eps)} of {len(seeds)} seeds", flush=True)

    for frac in FRACS:
        for horizon in HORIZONS:
            if only_cell is not None and only_cell != f"f{frac}_T{horizon}":
                continue
            finals, rows = [], []
            for seed, e in eps:
                t = time.time()
                recs, _ = run_benchmark_episode(sim, e["res"], e["I0"], e["h_star"],
                                                horizon, frac, seed, L)
                finals.append(recs[-1]["H"])
                rows.append(dict(seed=seed, final_H=recs[-1]["H"], final_H_I0=recs[-1]["H_I0"],
                                 mean_act=float(np.mean([r["n_act"] for r in recs])),
                                 mean_B=float(np.mean([r["B_size"] for r in recs])),
                                 final_size=recs[-1]["I_size"], final_q=recs[-1]["q_clump"],
                                 records=recs, elapsed_s=round(time.time() - t, 1)))
            key = f"f{frac}_T{horizon}"
            out["cells"][key] = dict(frac=frac, horizon=horizon, rows=rows,
                                     mean_final=float(np.mean(finals)),
                                     sd_final=float(np.std(finals)),
                                     frac_above_hi=float(np.mean([f >= SUCCESS_HI for f in finals])),
                                     frac_below_lo=float(np.mean([f <= SUCCESS_LO for f in finals])))
            c = out["cells"][key]
            print(f"frac={frac:<5} T={horizon:<3} meanH={c['mean_final']:.3f} "
                  f"sd={c['sd_final']:.3f} >=hi:{c['frac_above_hi']:.2f} "
                  f"<=lo:{c['frac_below_lo']:.2f} meanA={np.mean([r['mean_act'] for r in rows]):.1f}",
                  flush=True)
            dump_json(out, DATA_DIR / f"controllability__{tag}.json")
    dump_json(out, DATA_DIR / f"controllability__{tag}.json")
    print("wrote", DATA_DIR / f"controllability__{tag}.json")


def merge(tag="main"):
    """Merge per-cell shards into one controllability file."""
    out = None
    for frac in FRACS:
        for horizon in HORIZONS:
            key = f"f{frac}_T{horizon}"
            f = DATA_DIR / f"controllability__{tag}__{key}.json"
            if not f.exists():
                print("missing", key); continue
            d = load_json(f)
            if out is None:
                out = {k: v for k, v in d.items() if k != "cells"}
                out["cells"] = {}
            out["cells"].update(d["cells"])
    dump_json(out, DATA_DIR / f"controllability__{tag}.json")
    print(f"merged {len(out['cells'])} cells")
    for key, c in out["cells"].items():
        print(f"{key:<12} meanH={c['mean_final']:.3f} >=hi:{c['frac_above_hi']:.2f} "
              f"<=lo:{c['frac_below_lo']:.2f}")


if __name__ == "__main__":
    if sys.argv[1] == "merge":
        merge(sys.argv[2] if len(sys.argv) > 2 else "main")
    else:
        cell = sys.argv[1]
        main(0.4, 0.75, list(range(12)), tag=f"main__{cell}", only_cell=cell)
