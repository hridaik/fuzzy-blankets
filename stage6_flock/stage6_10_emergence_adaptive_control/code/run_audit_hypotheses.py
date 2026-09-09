"""Stage 6.10 Part A, phase 2 -- the six hypotheses, tested SEPARATELY.

Reads `data/audit_trace.json` (the instrumented replay) and adds the targeted
measurements each hypothesis needs. Every comparison between actions uses
COMMON RANDOM NUMBERS: at a given state the baseline and all candidate actuator
sets are evaluated against the same pre-drawn uniforms.

H1 the full-information arm simply spends more actuators
H2 it includes many weak causal channels
H3 KL influence is not aligned with target-directed influence
H4 additive multicover misses synergy / antagonism
H5 one-step influence does not predict horizon-T effect
H6 the episode-level ordering is mostly noise
"""
from __future__ import annotations

import itertools

import numpy as np

from common_610 import DATA_DIR, S68_DATA, dump_json, load_json
from episode_data import make_simulator, run_episode, observation_record
import candidate_detection as cd
import adaptive_control as ac
import reference_truth as rt

HEURISTIC = "adaptive_oracle"      # frozen arm name; the Full-info causal heuristic
INFERRED = "adaptive_causal"
SAMPLE_STEPS = [0, 6, 12, 18, 24]  # declared subsample for the expensive tests
N_ROLL = 128
TAUS = (2, 4, 8)
N_PAIRS = 24


def spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan")
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    ra = ra - ra.mean(); rb = rb - rb.mean()
    d = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / d) if d else float("nan")


def main():
    tr = load_json(DATA_DIR / "audit_trace.json")
    sim = make_simulator(tr["operating_point"]["nn"], tr["operating_point"]["beta"],
                         tr["operating_point"]["s"])
    out = dict(protocol="stage6_10 Part A -- six hypotheses",
               source="data/audit_trace.json", n_roll=N_ROLL, taus=list(TAUS),
               sample_steps=SAMPLE_STEPS,
               naming=dict(adaptive_oracle="Full-info causal heuristic"))

    # ---------------------------------------------------------------- H1 ----
    per_arm = {}
    for arm in tr["arms"]:
        na = [s["n_act"] for ep in tr["episodes"] for s in ep["arms"][arm]["steps"]]
        fin = [ep["arms"][arm]["final_target_fraction"] for ep in tr["episodes"]]
        per_arm[arm] = dict(mean_actuators=float(np.mean(na)), sd_actuators=float(np.std(na)),
                            mean_final=float(np.mean(fin)), sd_final=float(np.std(fin)),
                            n_episodes=len(fin))
    out["H1_actuator_spend"] = dict(
        per_arm=per_arm,
        statement=("Compares actuator spend and outcome per arm. A fixed-K re-run is "
                   "reported separately by run_fixed_k.py; this table alone cannot settle H1."))

    # ---------------------------------------------------------------- H2 ----
    h2 = {}
    for arm in (HEURISTIC, INFERRED):
        kl = [v for ep in tr["episodes"] for s in ep["arms"][arm]["steps"]
              for v in s["kl_per_actuator"].values()]
        kl = np.array(kl, float)
        if len(kl):
            h2[arm] = dict(n=len(kl), median=float(np.median(kl)),
                           q10=float(np.quantile(kl, .10)), q90=float(np.quantile(kl, .90)),
                           frac_below_1e3=float(np.mean(kl < 1e-3)),
                           frac_below_1e2=float(np.mean(kl < 1e-2)))
    out["H2_weak_channels"] = dict(per_arm=h2,
        statement="Distribution of per-actuator KL influence WITHIN each arm's selected set.")

    # -------------------------------------------------------- H3/H4/H5 ------
    rows35, pairs, hor = [], [], []
    for ep in tr["episodes"]:
        seed, h_star = ep["seed"], ep["h_star"]
        steps = ep["arms"][HEURISTIC]["steps"]
        res = run_episode(sim, seed, nt=tr["t0"] + 2, record_oracle=False)
        z_prefix = res.z_hist[:tr["t0"] + 1]
        for k in SAMPLE_STEPS:
            if k >= len(steps):
                continue
            st = steps[k]
            I = np.array(st["I"])
            # the state the controller saw at this step, recovered from the trace
            zt = np.array(res.z_hist[tr["t0"]]) if k == 0 else None
            if zt is None:
                continue                      # only step 0 states are exactly recoverable here
            cands = [int(j) for j in st["B_do"]]
            if len(cands) < 4:
                continue
            seed_crn = 900000 + 31 * seed
            kl = [rt.do_influence(sim, zt, I, j, agg="sum")[0] for j in cands]
            auth = {}
            for tau in TAUS:
                base = rt.rollout_alignment(sim, zt, I, h_star, tau, [], seed_crn, N_ROLL)
                auth[tau] = [rt.rollout_alignment(sim, zt, I, h_star, tau, [j], seed_crn, N_ROLL) - base
                             for j in cands]
            rows35.append(dict(seed=seed, step=k, n_cands=len(cands),
                               kl=kl, authority={str(t): auth[t] for t in TAUS},
                               rho_kl_auth={str(t): spearman(kl, auth[t]) for t in TAUS}))
            hor.append(dict(seed=seed, step=k,
                            rho_tau2_tau4=spearman(auth[2], auth[4]),
                            rho_tau2_tau8=spearman(auth[2], auth[8]),
                            rho_kl_tau8=spearman(kl, auth[8])))
            # H4: synergy on sampled pairs from the top-authority sources
            order = np.argsort(-np.array(auth[TAUS[0]]))
            top = [cands[i] for i in order[:8]]
            base2 = rt.rollout_alignment(sim, zt, I, h_star, TAUS[0], [], seed_crn, N_ROLL)
            for (j, kk) in list(itertools.combinations(top, 2))[:N_PAIRS]:
                ajk = rt.rollout_alignment(sim, zt, I, h_star, TAUS[0], [j, kk], seed_crn, N_ROLL) - base2
                aj = auth[TAUS[0]][cands.index(j)]
                ak = auth[TAUS[0]][cands.index(kk)]
                pairs.append(dict(seed=seed, step=k, j=j, k=kk, A_jk=ajk, A_j=aj, A_k=ak,
                                  S_jk=float(ajk - aj - ak)))
            print(f"  seed {seed} step {k}: rho(KL, A_tau2) = "
                  f"{rows35[-1]['rho_kl_auth'][str(TAUS[0])]:.3f}", flush=True)

    rhos = [r["rho_kl_auth"][str(TAUS[0])] for r in rows35 if r["rho_kl_auth"][str(TAUS[0])] == r["rho_kl_auth"][str(TAUS[0])]]
    out["H3_kl_vs_authority"] = dict(
        per_state=rows35,
        mean_rho_kl_authority=float(np.mean(rhos)) if rhos else float("nan"),
        n_states=len(rows35),
        statement="Spearman rank correlation between task-agnostic KL influence and "
                  "target-directed authority, per state, over the exact causal interface.")
    S = np.array([p["S_jk"] for p in pairs], float)
    A1 = np.array([abs(p["A_j"]) + abs(p["A_k"]) for p in pairs], float)
    out["H4_synergy"] = dict(
        n_pairs=len(pairs),
        mean_abs_S=float(np.mean(np.abs(S))) if len(S) else float("nan"),
        median_abs_S=float(np.median(np.abs(S))) if len(S) else float("nan"),
        frac_S_gt_half_of_parts=float(np.mean(np.abs(S) > 0.5 * A1)) if len(S) else float("nan"),
        frac_negative=float(np.mean(S < 0)) if len(S) else float("nan"),
        pairs=pairs[:200],
        statement="S_jk = A_{jk} - A_j - A_k. Nonzero means an additive/multicover "
                  "ranking cannot be exactly right.")
    out["H5_horizon"] = dict(
        per_state=hor,
        mean_rho_tau2_tau4=float(np.nanmean([h["rho_tau2_tau4"] for h in hor])) if hor else float("nan"),
        mean_rho_tau2_tau8=float(np.nanmean([h["rho_tau2_tau8"] for h in hor])) if hor else float("nan"),
        mean_rho_kl_tau8=float(np.nanmean([h["rho_kl_tau8"] for h in hor])) if hor else float("nan"),
        statement="Does short-horizon authority rank actuators the same way as the "
                  "horizon the controller is actually judged on?")

    # ---------------------------------------------------------------- H6 ----
    diffs = []
    for ep in tr["episodes"]:
        a = ep["arms"][INFERRED]["final_target_fraction"]
        b = ep["arms"][HEURISTIC]["final_target_fraction"]
        diffs.append(dict(seed=ep["seed"], adaptive_causal=a, full_info_heuristic=b, diff=a - b))
    d = np.array([x["diff"] for x in diffs], float)
    n = len(d)
    se = float(np.std(d, ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
    rng = np.random.default_rng(0)
    boot = np.array([rng.choice(d, n, replace=True).mean() for _ in range(20000)])
    out["H6_ordering_noise"] = dict(
        per_episode=diffs, n=n, mean_diff=float(d.mean()), sd_diff=float(d.std(ddof=1)),
        se_diff=se, t_stat=float(d.mean() / se) if se and se == se else float("nan"),
        boot_ci=[float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
        frac_episodes_inferred_better=float(np.mean(d > 0)),
        statement="Paired per-episode difference (adaptive sampled-causal minus "
                  "full-info causal heuristic) on identical starting conditions.")

    dump_json(out, DATA_DIR / "audit_hypotheses.json")
    print("\nwrote", DATA_DIR / "audit_hypotheses.json")
    print(f"H3 mean rho(KL, authority) = {out['H3_kl_vs_authority']['mean_rho_kl_authority']:.3f}")
    print(f"H4 mean |S_jk| = {out['H4_synergy']['mean_abs_S']:.4f} over {out['H4_synergy']['n_pairs']} pairs")
    print(f"H6 mean paired diff = {out['H6_ordering_noise']['mean_diff']:.3f} "
          f"CI {out['H6_ordering_noise']['boot_ci']}")


if __name__ == "__main__":
    main()
