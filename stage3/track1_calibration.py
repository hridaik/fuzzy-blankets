"""
Track 1, Parts 1B-1E: high-precision coverage reassessment (Wishart-accelerated),
oracle diagnostic, alternative-method comparison, and certification margin analysis.
"""
import sys, os, csv, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage2"))
import numpy as np
from scipy import stats
import core
from part_b_c import L_plugin_batch, beta_pqr
from wishart import sample_covariance_wishart_batch

RNG_ROOT = 2026081902


def wilson_ci(k, n, conf=0.95):
    """Wilson score interval for a binomial proportion (better small/edge-case behavior than normal approx)."""
    if n == 0:
        return (np.nan, np.nan)
    z = stats.norm.ppf(1 - (1 - conf) / 2)
    phat = k / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    half = (z * np.sqrt(phat * (1 - phat) / n + z**2 / (4 * n**2))) / denom
    return (center - half, center + half)


def bootstrap_U_all_methods(S_fit, L_fit, L_obs_tilde, Lb_tilde_raw_batch, alpha=0.05):
    """Given one fitted covariance and its bootstrap replicate CMI values (already bias-corrected,
    NaNs removed), return the one-sided upper bound U_{1-alpha} under three methods:
      basic       -- Stage-2's error-inversion bootstrap (default/deployable method)
      percentile  -- plain percentile bootstrap on Ltilde_b itself
      bc          -- bias-corrected percentile (no acceleration term)
    """
    Lb = Lb_tilde_raw_batch
    e_b = Lb - L_fit
    U_basic = L_obs_tilde - np.quantile(e_b, alpha)

    U_percentile = np.quantile(Lb, 1 - alpha)

    # bias-corrected percentile (BC, no acceleration): z0 from proportion of Lb <= L_obs_tilde
    prop = np.mean(Lb <= L_obs_tilde)
    prop = np.clip(prop, 1e-4, 1 - 1e-4)
    z0 = stats.norm.ppf(prop)
    z_alpha = stats.norm.ppf(1 - alpha)
    alpha_adj = stats.norm.cdf(2 * z0 + z_alpha)
    alpha_adj = np.clip(alpha_adj, 1e-4, 1 - 1e-4)
    U_bc = np.quantile(Lb, alpha_adj)

    return dict(basic=U_basic, percentile=U_percentile, bc=U_bc)


if __name__ == "__main__":
    I_idx = core.I_IDX

    def cand(Bkey):
        B_idx = [core.idx[nn] for nn in Bkey]
        E_idx = [core.idx[nn] for nn in core.REST_NODES if nn not in Bkey]
        return B_idx, E_idx

    cells = [
        ((), 1000), ((), 5000),
        ((4,), 200), ((4,), 1000), ((4,), 5000),
        ((4, 5), 200), ((4, 5), 1000),
    ]

    R_outer = 5000
    M_boot = 1000
    M_oracle = 20000
    alpha = 0.05

    print("=== Track 1, Parts 1B/1C/1D: high-precision coverage + oracle diagnostic ===")
    print(f"Settings: R_outer={R_outer}, M_boot={M_boot}, M_oracle={M_oracle}, alpha={alpha} "
          f"(all via Wishart-level sampling, validated in Part 1A).")

    rows = []
    rng_master = np.random.default_rng(RNG_ROOT)
    t_start_all = time.time()
    for Bkey, n in cells:
        B_idx, E_idx = cand(Bkey)
        p, q, r = len(I_idx), len(E_idx), len(B_idx)
        L_pop = core.L_cmi_cov_joint(core.Sigma0, I_idx, B_idx, E_idx)
        beta_val = beta_pqr(p, q, r, n)

        seed = int(rng_master.integers(0, 2**31 - 1))
        rng = np.random.default_rng(seed)

        # oracle reference distribution: Ltilde - L_pop under TRUE Sigma0, at this n
        S_oracle = sample_covariance_wishart_batch(core.Sigma0, n, M_oracle, rng)
        L_oracle_tilde = L_plugin_batch(S_oracle, I_idx, B_idx, E_idx) - beta_val
        L_oracle_tilde = L_oracle_tilde[~np.isnan(L_oracle_tilde)]
        oracle_err = L_oracle_tilde - L_pop
        oracle_q_alpha = np.quantile(oracle_err, alpha)

        t0 = time.time()
        covered = {"basic": 0, "percentile": 0, "bc": 0, "oracle": 0}
        widths_basic = []
        n_eff = 0
        for rep in range(R_outer):
            S_fit = sample_covariance_wishart_batch(core.Sigma0, n, 1, rng)[0]
            try:
                L_fit = core.L_cmi_cov_joint(S_fit, I_idx, B_idx, E_idx)
            except np.linalg.LinAlgError:
                continue
            L_obs_raw = L_plugin_batch(S_fit[None], I_idx, B_idx, E_idx)[0]
            if np.isnan(L_obs_raw):
                continue
            L_obs_tilde = L_obs_raw - beta_val

            Sb = sample_covariance_wishart_batch(S_fit, n, M_boot, rng)
            Lb_raw = L_plugin_batch(Sb, I_idx, B_idx, E_idx)
            valid = ~np.isnan(Lb_raw)
            if valid.sum() < 20:
                continue
            Lb_tilde = Lb_raw[valid] - beta_val

            n_eff += 1
            U = bootstrap_U_all_methods(S_fit, L_fit, L_obs_tilde, Lb_tilde, alpha=alpha)
            U_oracle = L_obs_tilde - oracle_q_alpha

            if L_pop <= U["basic"]:
                covered["basic"] += 1
            if L_pop <= U["percentile"]:
                covered["percentile"] += 1
            if L_pop <= U["bc"]:
                covered["bc"] += 1
            if L_pop <= U_oracle:
                covered["oracle"] += 1
            widths_basic.append(U["basic"])

        elapsed = time.time() - t0
        row = dict(B=str(Bkey), n=n, p=p, q=q, r=r, L_pop=L_pop, beta=beta_val, R_outer=R_outer,
                   n_eff=n_eff, M_boot=M_boot, elapsed_sec=elapsed)
        for method in ["basic", "percentile", "bc", "oracle"]:
            k = covered[method]
            cov = k / n_eff if n_eff else np.nan
            lo, hi = wilson_ci(k, n_eff)
            row[f"coverage_{method}"] = cov
            row[f"coverage_{method}_wilson_lo"] = lo
            row[f"coverage_{method}_wilson_hi"] = hi
        rows.append(row)
        print(f"B={str(Bkey):<10} n={n:<6} L_pop={L_pop:.5f}  n_eff={n_eff}  ({elapsed:.1f}s)  "
              f"basic={row['coverage_basic']:.4f} [{row['coverage_basic_wilson_lo']:.4f},{row['coverage_basic_wilson_hi']:.4f}]  "
              f"percentile={row['coverage_percentile']:.4f}  bc={row['coverage_bc']:.4f}  "
              f"oracle={row['coverage_oracle']:.4f} [{row['coverage_oracle_wilson_lo']:.4f},{row['coverage_oracle_wilson_hi']:.4f}]")

    print(f"\nTotal wall time: {time.time()-t_start_all:.1f}s")

    outpath = os.path.join(os.path.dirname(__file__), "data", "track1_highprec_coverage.csv")
    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Saved to {outpath}")

    # -------------------------------------------------------------------
    # Part 1D verdict: does any alternative method broadly dominate 'basic'?
    # -------------------------------------------------------------------
    print("\n=== Part 1D: method comparison verdict ===")
    for method in ["basic", "percentile", "bc"]:
        devs = [abs(r[f"coverage_{method}"] - 0.95) for r in rows]
        print(f"  {method:<12} mean |coverage - 0.95| across cells = {np.mean(devs):.4f}, max = {np.max(devs):.4f}")
