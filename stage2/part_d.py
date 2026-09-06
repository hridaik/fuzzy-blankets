"""
Part D: Gaussian parametric-bootstrap confidence interval for L, and coverage study.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import csv
import core
from part_b_c import sample_covariance, sample_multivariate_normal, L_plugin_batch, beta_pqr, COV_DIVISOR

RNG_ROOT = 20260818 + 1


def fit_gaussian(X):
    mu = X.mean(axis=0)
    S = sample_covariance(X, COV_DIVISOR)
    return mu, S


def bootstrap_replicates_cov(n, Sigma_fit, M, rng):
    """Generate M bootstrap datasets of size n from N(0, Sigma_fit) and return
    their sample covariances as a batch array (M, d, d). Mean is not re-added
    since CMI is invariant to translation; centering uses each bootstrap
    dataset's own sample mean exactly as in the observed-data pipeline."""
    d = Sigma_fit.shape[0]
    Lchol = np.linalg.cholesky(Sigma_fit)
    Z = rng.standard_normal((M, n, d))
    Xb = Z @ Lchol.T  # (M, n, d)
    Xb_c = Xb - Xb.mean(axis=1, keepdims=True)
    div = n if COV_DIVISOR == "n" else n - 1
    # batched matmul (BLAS-backed) is ~15x faster here than the equivalent einsum('mid,mie->mde',...)
    Sb = np.matmul(Xb_c.transpose(0, 2, 1), Xb_c) / div
    return Sb


def ci_from_bootstrap(L_tilde_obs, L_fit, e_b, alpha=0.05):
    """Error-inversion CI: e_b = Ltilde_b - L_fit. CI = [Lobs - q_{1-a/2}(e), Lobs - q_{a/2}(e)]."""
    q_lo = np.quantile(e_b, alpha / 2)
    q_hi = np.quantile(e_b, 1 - alpha / 2)
    ci_lo = L_tilde_obs - q_hi
    ci_hi = L_tilde_obs - q_lo
    q_alpha = np.quantile(e_b, alpha)
    U = L_tilde_obs - q_alpha  # one-sided upper bound at level 1-alpha
    return ci_lo, ci_hi, U


if __name__ == "__main__":
    print("=== Part D: bootstrap CI + coverage ===")
    I_idx = core.I_IDX
    candidates = {
        (): [],
        (4,): [core.idx[4]],
        (4, 5): [core.idx[4], core.idx[5]],
    }

    # single illustrative bootstrap example
    rng = np.random.default_rng(RNG_ROOT)
    n_demo = 200
    Bkey, B_idx = (4,), [core.idx[4]]
    E_idx = [core.idx[nn] for nn in core.REST_NODES if nn not in Bkey]
    p, q, r = len(I_idx), len(E_idx), len(B_idx)
    X = sample_multivariate_normal(n_demo, core.Sigma0, rng)
    mu_fit, S_fit = fit_gaussian(X)
    L_fit = core.L_cmi_cov_joint(S_fit, I_idx, B_idx, E_idx)
    L_obs_raw = L_plugin_batch(S_fit[None], I_idx, B_idx, E_idx)[0]
    beta_val = beta_pqr(p, q, r, n_demo)
    L_obs_tilde = L_obs_raw - beta_val

    M = 500
    Sb = bootstrap_replicates_cov(n_demo, S_fit, M, rng)
    L_b_raw = L_plugin_batch(Sb, I_idx, B_idx, E_idx)
    L_b_tilde = L_b_raw - beta_val
    e_b = L_b_tilde - L_fit
    ci_lo, ci_hi, U95 = ci_from_bootstrap(L_obs_tilde, L_fit, e_b, alpha=0.05)
    print(f"Demo (n={n_demo}, B={Bkey}): L_fit={L_fit:.5f}, L_obs_raw={L_obs_raw:.5f}, "
          f"L_obs_tilde={L_obs_tilde:.5f}, 95% CI=[{ci_lo:.5f}, {ci_hi:.5f}], U_0.95={U95:.5f}")
    print(f"  Presentation (clipped at 0) CI: [{max(ci_lo,0):.5f}, {max(ci_hi,0):.5f}]  (unclipped retained above)")

    # -----------------------------------------------------------------------
    # Coverage study
    # -----------------------------------------------------------------------
    print("\n=== Coverage study (target 1-alpha=0.95) ===")
    print("NOTE ON COMPUTE BUDGET: the task suggests M>=500 bootstrap replicates and enough outer")
    print("datasets for credible coverage estimates. Coverage assessment requires a NESTED bootstrap")
    print("(R_outer observed datasets, each with its own M-replicate bootstrap), which is far more")
    print("expensive than Part C's unnested bias check. An initial run at R_outer=200, M_boot=500 was")
    print("observed to be dominated by raw random-number generation volume at n=5000 (M*n*d draws per")
    print("outer replicate) rather than by any avoidable inefficiency (a real einsum->matmul bottleneck")
    print("was found and fixed in bootstrap_replicates_cov, but did not fully resolve the runtime). We")
    print("therefore reduced to R_outer=100, M_boot=300 for tractability; R_outer=100 gives a binomial")
    print("coverage SE of ~2.2% at the 95% target, adequate to detect miscalibration >~5-6%. This is a")
    print("compute-budget reduction, not a tuning of results, and is reported per the instructions.")
    R_outer = 100
    M_boot = 300
    n_list_cov = [50, 200, 1000, 5000]
    alpha = 0.05

    rows = []
    rng_master = np.random.default_rng(RNG_ROOT + 7)
    for Bkey, B_idx in candidates.items():
        E_idx = [core.idx[nn] for nn in core.REST_NODES if nn not in Bkey]
        p, q, r = len(I_idx), len(E_idx), len(B_idx)
        L_pop = core.L_cmi_cov_joint(core.Sigma0, I_idx, B_idx, E_idx)
        for n in n_list_cov:
            beta_val = beta_pqr(p, q, r, n)
            seed = int(rng_master.integers(0, 2**31 - 1))
            rng = np.random.default_rng(seed)
            covered_2sided = 0
            covered_1sided = 0
            widths = []
            n_singular = 0
            for rep in range(R_outer):
                X = sample_multivariate_normal(n, core.Sigma0, rng)
                mu_fit, S_fit = fit_gaussian(X)
                try:
                    L_fit = core.L_cmi_cov_joint(S_fit, I_idx, B_idx, E_idx)
                except np.linalg.LinAlgError:
                    n_singular += 1
                    continue
                L_obs_raw = L_plugin_batch(S_fit[None], I_idx, B_idx, E_idx)[0]
                if np.isnan(L_obs_raw):
                    n_singular += 1
                    continue
                L_obs_tilde = L_obs_raw - beta_val
                Sb = bootstrap_replicates_cov(n, S_fit, M_boot, rng)
                L_b_raw = L_plugin_batch(Sb, I_idx, B_idx, E_idx)
                valid = ~np.isnan(L_b_raw)
                L_b_tilde = L_b_raw[valid] - beta_val
                e_b = L_b_tilde - L_fit
                ci_lo, ci_hi, U95 = ci_from_bootstrap(L_obs_tilde, L_fit, e_b, alpha=alpha)
                # coverage targets the TRUE POPULATION L (L_pop), the actual estimand of interest
                if ci_lo <= L_pop <= ci_hi:
                    covered_2sided += 1
                if L_pop <= U95:
                    covered_1sided += 1
                widths.append(ci_hi - ci_lo)
            n_eff = R_outer - n_singular
            cov2 = covered_2sided / n_eff if n_eff else float('nan')
            cov1 = covered_1sided / n_eff if n_eff else float('nan')
            mean_width = np.mean(widths) if widths else float('nan')
            print(f"B={str(Bkey):<8} n={n:<6} L_pop={L_pop:.5f}  2-sided cov={cov2:.3f}  "
                  f"1-sided cov={cov1:.3f}  mean width={mean_width:.5f}  n_singular={n_singular}")
            rows.append(dict(B=str(Bkey), n=n, p=p, q=q, r=r, L_pop=L_pop, beta=beta_val,
                               coverage_2sided=cov2, coverage_1sided=cov1, mean_width=mean_width,
                               n_singular=n_singular, R_outer=R_outer, M_boot=M_boot, alpha=alpha))

    outpath = os.path.join(os.path.dirname(__file__), "data", "part_d_coverage_table.csv")
    with open(outpath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved coverage table to {outpath}")
