"""Stage 6.10 Parts K + L -- release, and the single clarity trajectory.

Part K: control is switched OFF at the end of a successful episode. Does the
lineage hold the new heading on its own, and does it stay a coherent clump? A
collective that snaps back the instant the actuators stop was pushed, not
steered, and the two outcomes are reported separately rather than folded into
the control result.

Part L: ONE trajectory is exported for the demo, chosen by a declared rule from
episodes that were already prequalified and held out. It is an illustration.
It is never used to support an aggregate claim, and the rule is recorded here
so that "the clearest example" cannot quietly become "the best example".
"""
from __future__ import annotations

import sys

import numpy as np

from common_610 import DATA_DIR, dump_json, load_json
from episode_data import make_simulator
from closed_loop import release
from identity_scoring import lineage_statistics, identity_valid

RELEASE_STEPS = 16


def main(tag="main"):
    d = load_json(DATA_DIR / f"closed_loop__{tag}.json")
    reg = d["regime"]
    sim = make_simulator(reg["nn"], reg["beta"], reg["s"])
    L = int(round(reg["nn"] ** 0.5))
    env = d["validity_envelope"]
    out = dict(protocol="stage6_10 Parts K+L -- release and clarity trajectory",
               source=f"closed_loop__{tag}.json", release_steps=RELEASE_STEPS,
               episodes=[])

    for ep in d["episodes"]:
        row = dict(seed=ep["seed"], h_star=ep["h_star"], arms={})
        for arm, r in ep["arms"].items():
            if not r["score"]["success"]:
                continue                      # release only what actually worked
            recs = release(sim, np.array(r["final_z"]), ep["seed"], ep["h_star"],
                           np.array(r["final_I"]), RELEASE_STEPS, L)
            H = [x["H_current"] for x in recs]
            row["arms"][arm] = dict(
                H_at_release=r["final_H_current"], H_trace=H,
                H_final=H[-1], retention=float(H[-1] / max(1e-9, r["final_H_current"])),
                q_final=recs[-1]["q_clump"], comp_final=recs[-1]["n_components"],
                size_final=recs[-1]["I_size"], records=recs)
            print(f"seed {ep['seed']:<4} {arm:<22} H {r['final_H_current']:.2f} "
                  f"-> {H[-1]:.2f} after {RELEASE_STEPS} free steps "
                  f"(retention {row['arms'][arm]['retention']:.2f})", flush=True)
        if row["arms"]:
            out["episodes"].append(row)
    dump_json(out, DATA_DIR / f"release__{tag}.json")

    # ---------------------------------------------------------- Part L ----
    # Declared selection rule, fixed before looking at the candidates:
    #   among episodes where the METHOD arm (adaptive_causal) scored a
    #   conjunctive success, take the one whose final H is the MEDIAN of that
    #   set. Median, not maximum: the clearest example must be typical of the
    #   successes, not the best of them.
    cands = [(e["arms"]["adaptive_causal"]["final_H_current"], e["seed"])
             for e in d["episodes"]
             if e["arms"]["adaptive_causal"]["score"]["success"]]
    if cands:
        cands.sort()
        pick = cands[len(cands) // 2]
        out["clarity_trajectory"] = dict(
            seed=pick[1], final_H=pick[0], arm="adaptive_causal",
            rule="median final H among adaptive_causal conjunctive successes",
            n_eligible=len(cands),
            caveat="Illustration only. Not used for any aggregate claim.")
        print(f"\nclarity trajectory: seed {pick[1]} (median of {len(cands)} successes, "
              f"H={pick[0]:.3f})")
    else:
        out["clarity_trajectory"] = dict(
            seed=None, rule="median final H among adaptive_causal conjunctive successes",
            n_eligible=0,
            caveat="No episode qualified. No clarity trajectory is exported; "
                   "an unsuccessful episode is not substituted.")
        print("\nno qualifying clarity trajectory -- none exported")
    dump_json(out, DATA_DIR / f"release__{tag}.json")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
