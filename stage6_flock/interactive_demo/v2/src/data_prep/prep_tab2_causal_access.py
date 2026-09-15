"""Build interactive_demo/v2/data/tab2_causal_access.json.

Sources:
  stage6_10_emergence_adaptive_control/data/audit_trace.json
      -- episodes[2] (seed 17): interior I0, and the frozen adaptive_oracle
         arm's step-0 candidate pool B_do (the exterior sources actually
         do()-tested), plus the regime (nn, beta, s) needed to rebuild the
         exact simulator.
  stage6_10_emergence_adaptive_control/data/audit_hypotheses.json
      -- H3_kl_vs_authority.per_state[2]: for the SAME (seed, step), the exact
         one-step causal KL ("kl", from reference_truth.do_influence, agg=sum)
         and the signed finite-horizon target authority A_j^{h*,tau} for
         tau in {2,4,8} (reference_truth.task_authority), for every candidate
         in B_do, in the same order. Episode 2 (seed 17) was chosen over the
         default episode 0 (seed 15) after comparing all 8 audited states --
         see "Seed selection" below.
  interactive_demo/data/stage6_10_bundle.json
      -- lattice.positions/neighbors for the L=20 regime (positions/neighbors
         are a deterministic function of the lattice size only, so valid for
         any episode at this regime).

Deterministic replay (per the brief's rule: only when a display quantity was
not persisted, and only after verifying it against a stored endpoint):
  The full 400-bird heading vector z_t0 was never persisted (run_audit_
  hypotheses.py computed it in memory and discarded it after use). We
  replay it exactly the way that script did -- run_episode(sim, seed,
  nt=t0+2), z_hist[t0] -- using the SAME simulator/seed/regime. This is
  verified two ways before use: (1) calling reference_truth.do_influence
  with this replayed z_t0 for every stored candidate reproduces the frozen
  per-candidate "kl" values in audit_hypotheses.json to within 2e-15 (see
  explore_tab2_states.py, run separately); (2) do_influence's own "per"
  return value (a per-interior-bird KL breakdown) sums to exactly the
  already-frozen "kl" total for that candidate by construction -- we are not
  computing a new quantity, only unpacking a return value that was computed
  once already and partially discarded.

Seed selection: run explore_tab2_states.py (not part of the build) to see
the comparison across all 8 audited states. Episode 0 (seed 15, the
originally-used state) has authority values that round to ~0 at 3 decimals
for all but 2 candidates, and its replayed heading vector is uniform
(2 distinct headings, 399 vs 1) -- an unrepresentative, visually flat
example. Episode 2 (seed 17) has a materially larger and better-separated
authority spread (max 0.0081 at tau=2, up to 0.032 at tau=8, INCLUDING
negative values down to -0.0044 at tau=8 -- real examples of an exterior
source that actively hurts the target), a compact single-component interior
(Q_clump=0.91), and a genuinely mixed replayed heading vector (281 vs 119
birds across 2 headings) rather than a degenerate one.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[2] / "data" / "tab2_causal_access.json"

sys.path.insert(0, str(ROOT / "stage6_10_emergence_adaptive_control/code"))
sys.path.insert(0, str(ROOT / "stage6_8_dynamic_interactions/code"))
from episode_data import make_simulator, run_episode  # noqa: E402
import reference_truth as rt  # noqa: E402
import numpy as np  # noqa: E402

EPISODE_IDX = 2  # seed 17 -- see "Seed selection" above

trace = json.load(open(ROOT / "stage6_10_emergence_adaptive_control/data/audit_trace.json"))
hyp = json.load(open(ROOT / "stage6_10_emergence_adaptive_control/data/audit_hypotheses.json"))
bundle10 = json.load(open(ROOT / "interactive_demo/data/stage6_10_bundle.json"))

ep = trace["episodes"][EPISODE_IDX]
step0 = ep["arms"]["adaptive_oracle"]["steps"][0]
state = hyp["H3_kl_vs_authority"]["per_state"][EPISODE_IDX]
assert state["seed"] == ep["seed"] and state["step"] == step0["step"]

t0 = trace["t0"]
sim = make_simulator(trace["operating_point"]["nn"], trace["operating_point"]["beta"], trace["operating_point"]["s"])
res = run_episode(sim, ep["seed"], nt=t0 + 2, record_oracle=False)
zt = np.array(res.z_hist[t0])

cand_ids = [int(j) for j in step0["B_do"]]
assert len(cand_ids) == state["n_cands"] == len(state["kl"]) == len(state["authority"]["2"])

I0 = np.array(ep["I0"])
candidates = []
max_err = 0.0
for i, j in enumerate(cand_ids):
    total, per = rt.do_influence(sim, zt, I0, j, agg="sum")
    max_err = max(max_err, abs(total - state["kl"][i]))
    top_per_bird = sorted(per.items(), key=lambda kv: -abs(kv[1]))[:10]
    candidates.append({
        "id": j,
        "causal_effect": state["kl"][i],
        "authority": {tau: state["authority"][tau][i] for tau in ("2", "4", "8")},
        "per_interior_bird": [{"bird": b, "kl": v} for b, v in top_per_bird],
    })
assert max_err < 1e-9, f"replay mismatch: {max_err}"

out = {
    "provenance": {
        "episode_source": f"stage6_10_emergence_adaptive_control/data/audit_trace.json, episodes[{EPISODE_IDX}] (seed {ep['seed']}, {ep['split']} split)",
        "metric_source": f"stage6_10_emergence_adaptive_control/data/audit_hypotheses.json, H3_kl_vs_authority.per_state[{EPISODE_IDX}]",
        "lattice_source": "interactive_demo/data/stage6_10_bundle.json (same L=20 regime: nn=400, beta=1.0, s=1.0; positions/neighbors are seed-independent)",
        "replay_note": (
            "The full 400-bird heading vector at t0 was not persisted by the audit "
            "pipeline; it is replayed deterministically here (run_episode, same seed "
            "and regime) exactly as run_audit_hypotheses.py did in memory. Verified "
            "by reproducing every stored per-candidate KL value to within 1e-9 "
            "before use (see explore_tab2_states.py)."
        ),
        "seed_selection_note": (
            "Episode 2 (seed 17) was chosen over the default episode 0 (seed 15) "
            "for a materially clearer example: episode 0's authority values round "
            "to ~0 for nearly every candidate and its heading vector is almost "
            "uniform. See prep_tab2_causal_access.py module docstring for the "
            "full comparison across all 8 audited states."
        ),
        "formulas": {
            "causal_effect": "C^do_{j->I}: exact ONE-STEP interventional KL of the interior's next-heading marginals under do(z_j=z'), summed over I and averaged over alternate z' (reference_truth.do_influence, agg=sum). This already IS an interventional quantity, not a passive correlation. It is a single-timestep (t -> t+1) quantity.",
            "target_authority": "A_j^{h*,tau} = E[H*_{t+tau} | do(u_j=h*)] - E[H*_{t+tau} | baseline], common random numbers, n_roll=96 (reference_truth.task_authority). Multi-step: tau in {2,4,8}.",
        },
        "tau_note": "tau=1 exterior authority is structurally exactly 0 in this model (an exterior actuator's forced action cannot reach the interior in one step) -- tau=2 is the minimum informative horizon and is used as the default toggle. Causal effect (KL) above is a separate, single-step (tau=1) quantity by construction -- it measures immediate influence, not target alignment at any horizon.",
        "auth_tau_default": 2,
        "rho_kl_authority_this_state": state["rho_kl_auth"]["2"],
        "rho_kl_authority_pooled_8_states": hyp["H3_kl_vs_authority"]["mean_rho_kl_authority"],
        "scope_note": "2-way toggle (causal effect / target authority): see VISUALIZATION_NOTES.md for why a third, purely-observational 'predictive relevance' axis was not added for this exact candidate set.",
    },
    "seed": ep["seed"],
    "h_star": ep["h_star"],
    "step": step0["step"],
    "t0": t0,
    "lattice": bundle10["lattice"],
    "interior": ep["I0"],
    "headings": zt.tolist(),
    "candidates": candidates,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out))
print("wrote", OUT, OUT.stat().st_size, "bytes")
