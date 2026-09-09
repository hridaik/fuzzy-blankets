"""ORACLE REVEAL (task brief sections 17-18).

Run ONLY after `run_boundary_pipeline.py` has written its results to disk.
Reads that frozen file and never modifies it. Adds, in this order:

  1. `B_t^{causal, exact}` from the exact black-box counterfactual propagator
     -- still without exposing topology to anything;
  2. the true FOV graph and `B_t^D`.

Three quantities are reported SEPARATELY and never collapsed into one number
(task brief section 17):

  estimation error due to finite probing : Bhat^{causal,sampled} vs B^{causal,exact}
  identifiability                        : B^{causal,exact}         vs B^D
  structural agreement                   : Bhat^{causal,sampled}    vs B^D

Nothing here is ever used to retune an estimator, threshold, shortlist size or
stopping rule -- every one of those was frozen in PROTOCOL_6_8.md before this
script existed.
"""
from __future__ import annotations

import sys

import numpy as np

from common_68 import dump_json, load_json, DATA_DIR
from episode_data import make_simulator, run_episode
from fov_dynamics import GateParams
from intervention_api_68 import ExactPropagator
from oracle_68 import compare_sets, turnover_similarity, temporal_lag

TAU_EXACT = 1e-9        # an exact effect above this counts as a live causal channel
SERIES_T_MAX = 200


def exact_causal_set(sim, z_t, I, candidates, channel_state=None) -> tuple[list, dict]:
    ep = ExactPropagator(sim, channel_state=channel_state)
    vals = {}
    for j in candidates:
        j = int(j)
        others = [h for h in range(4) if h != int(z_t[j])]
        vals[j] = float(np.mean([ep.exact(I, j, zp, z_t)["D_do_joint"] for zp in others]))
    return sorted([j for j, v in vals.items() if v > TAU_EXACT]), vals


def main(tag: str):
    frozen = load_json(DATA_DIR / f"boundary_inference__{tag}.json")
    op = frozen["operating_point"]
    sim = make_simulator(op["nn"], op["beta"], op["s"])
    gp = GateParams(**frozen["gate_params"]) if frozen.get("gate_params") else None

    ep_cache = {}
    out = dict(protocol=f"stage6_8 oracle reveal [{tag}]",
               source=f"boundary_inference__{tag}.json",
               operating_point=op, tau_exact=TAU_EXACT, runs=[])

    by_seed = {}
    for r in frozen["runs"]:
        by_seed.setdefault(r["seed"], []).append(r)

    for seed, runs in by_seed.items():
        nt = max(r["t"] for r in runs) + 2
        res = run_episode(sim, seed, nt=nt, gate_params=gp, record_oracle=True)
        edges_live = res.active_mask_hist
        prev = {}
        for r in sorted(runs, key=lambda x: (x["method"], x["t"])):
            t, I = r["t"], np.array(sorted(r["I"]))
            z_t = res.z_hist[t]
            BD = sim.oracle_B_D(edges_live[t], I).tolist()
            cands = r["causal"]["probe_candidates"]
            B_exact, exact_vals = exact_causal_set(
                sim, z_t, I, cands,
                channel_state=(res.gate_hist[t] if res.gate_hist is not None else None))
            B_samp = r["causal"]["B_causal"]
            B_pred = r["predictive"]["B_pred"]

            rec = dict(
                seed=seed, t=t, method=r["method"], I_size=r["I_size"],
                B_D=BD, B_causal_exact=B_exact, B_causal_sampled=B_samp, B_pred=B_pred,
                exact_effect=exact_vals,
                # (1) estimation error due to finite probing
                estimation_error=compare_sets(B_samp, B_exact),
                # (2) identifiability: can an exact intervention even see B^D?
                identifiability=compare_sets(B_exact, BD),
                # (3) structural agreement of the finite estimator with the truth
                structural_agreement=compare_sets(B_samp, BD),
                # predictive interface vs the same truth
                predictive_vs_BD=compare_sets(B_pred, BD),
                predictive_vs_causal_exact=compare_sets(B_pred, B_exact),
                n_probe_candidates=len(cands),
                probe_budget=r["causal"]["budget"],
            )
            key = (seed, r["method"])
            if key in prev and prev[key]["t"] == t - 1:
                p = prev[key]
                rec["T_B_causal"] = turnover_similarity(B_samp, p["B_causal_sampled"],
                                                        BD, p["B_D"])
                rec["T_B_pred"] = turnover_similarity(B_pred, p["B_pred"], BD, p["B_D"])
                rec["BD_changed"] = int(len(set(BD) ^ set(p["B_D"])))
                rec["B_causal_changed"] = int(len(set(B_samp) ^ set(p["B_causal_sampled"])))
                rec["B_pred_changed"] = int(len(set(B_pred) ^ set(p["B_pred"])))
            prev[key] = rec
            out["runs"].append(rec)
            print(f"seed {seed:<4} t={t:<3} {r['method']:<19} |B_D|={len(BD):<3} "
                  f"|exact|={len(B_exact):<3} |sampled|={len(B_samp):<3} |pred|={len(B_pred):<3} "
                  f"| est J={rec['estimation_error']['jaccard']:.2f} "
                  f"ident J={rec['identifiability']['jaccard']:.2f} "
                  f"struct J={rec['structural_agreement']['jaccard']:.2f} "
                  f"pred J={rec['predictive_vs_BD']['jaccard']:.2f}", flush=True)

    # temporal lag, per (seed, method) series
    lags = []
    for (seed, meth) in {(r["seed"], r["method"]) for r in out["runs"]}:
        rs = sorted([r for r in out["runs"] if r["seed"] == seed and r["method"] == meth],
                    key=lambda x: x["t"])
        if len(rs) < 4:
            continue
        BD = {r["t"]: r["B_D"] for r in rs}
        lags.append(dict(seed=seed, method=meth,
                         causal=temporal_lag({r["t"]: r["B_causal_sampled"] for r in rs}, BD),
                         predictive=temporal_lag({r["t"]: r["B_pred"] for r in rs}, BD)))
    out["temporal_lag"] = lags
    dump_json(out, DATA_DIR / f"oracle_reveal__{tag}.json")
    print("wrote", DATA_DIR / f"oracle_reveal__{tag}.json")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "snapshot")
