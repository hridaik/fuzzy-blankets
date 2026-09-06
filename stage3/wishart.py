"""
Part 1A: direct Wishart-level sampling of the sample covariance/scatter matrix,
replacing raw (n x d) Gaussian data regeneration. Validated against raw-data MC below.

Convention: for X_1..X_n iid N(mu,Sigma), the centered scatter matrix
    S_c = sum_i (X_i - Xbar)(X_i - Xbar)^T ~ Wishart_d(Sigma, nu=n-1).
The "sample covariance" used throughout Stage 2 divides S_c by n (COV_DIVISOR="n");
CMI itself is invariant to this choice (see part_b_c.py). Bootstrap replicates of
size n drawn from a fitted Gaussian are, at the level of their covariance, exactly
another draw from Wishart_d(Sigma_fit, n-1)/divisor -- so both the OUTER (data) and
INNER (bootstrap) sampling levels in Stage-2's nested coverage study can be replaced
by direct Wishart draws, with cost independent of n. This is the speedup that makes
Part 1B's high-precision coverage study tractable in-session.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage2"))
import numpy as np
import core
from part_b_c import sample_covariance, sample_multivariate_normal, L_plugin_batch, beta_pqr, COV_DIVISOR

DIVISOR = COV_DIVISOR  # "n", inherited from Stage 2; kept explicit here too


def sample_wishart_scatter_batch(Sigma, nu, M, rng):
    """Batched draw of M scatter matrices ~ Wishart_d(Sigma, nu), via Bartlett decomposition.
    Returns array (M, d, d). Cost is independent of any sample size n -- only nu, d, M matter."""
    d = Sigma.shape[0]
    L = np.linalg.cholesky(Sigma)
    A = np.zeros((M, d, d))
    for i in range(d):
        # diagonal: chi-distributed, sqrt of chi2(nu - i) for 0-indexed row i
        dof = nu - i
        A[:, i, i] = np.sqrt(rng.chisquare(dof, size=M))
    il = np.tril_indices(d, k=-1)
    if len(il[0]):
        A[:, il[0], il[1]] = rng.standard_normal((M, len(il[0])))
    LA = L[None, :, :] @ A
    W = LA @ LA.transpose(0, 2, 1)
    return W


def sample_covariance_wishart_batch(Sigma, n, M, rng, divisor=DIVISOR):
    """Batched sample-covariance draws consistent with Stage-2's convention: scatter
    matrix ~ Wishart_d(Sigma, n-1), divided by n (or n-1) per `divisor`."""
    nu = n - 1
    W = sample_wishart_scatter_batch(Sigma, nu, M, rng)
    d = n if divisor == "n" else nu
    return W / d


if __name__ == "__main__":
    print("=== Part 1A: Wishart-level sampling validation against raw-data Monte Carlo ===")
    I_idx = core.I_IDX
    candidates = {(): [], (4,): [core.idx[4]], (4, 5): [core.idx[4], core.idx[5]]}
    n_list = [50, 200]
    R = 3000  # larger than Stage-2's R=500 since we're specifically checking agreement here
    M_boot_check = 500

    rows = []
    rng_master = np.random.default_rng(2026081901)
    for Bkey, B_idx in candidates.items():
        E_idx = [core.idx[nn] for nn in core.REST_NODES if nn not in Bkey]
        p, q, r = len(I_idx), len(E_idx), len(B_idx)
        L_pop = core.L_cmi_cov_joint(core.Sigma0, I_idx, B_idx, E_idx)
        for n in n_list:
            beta = beta_pqr(p, q, r, n)

            # raw-data Monte Carlo
            seed1 = int(rng_master.integers(0, 2**31 - 1))
            rng1 = np.random.default_rng(seed1)
            L_hat_raw = []
            for rep in range(R):
                X = sample_multivariate_normal(n, core.Sigma0, rng1)
                S = sample_covariance(X, DIVISOR)
                Lhat = L_plugin_batch(S[None], I_idx, B_idx, E_idx)[0]
                if not np.isnan(Lhat):
                    L_hat_raw.append(Lhat)
            L_hat_raw = np.array(L_hat_raw)

            # Wishart-level Monte Carlo
            seed2 = int(rng_master.integers(0, 2**31 - 1))
            rng2 = np.random.default_rng(seed2)
            Sb = sample_covariance_wishart_batch(core.Sigma0, n, R, rng2)
            L_hat_wish = L_plugin_batch(Sb, I_idx, B_idx, E_idx)
            L_hat_wish = L_hat_wish[~np.isnan(L_hat_wish)]

            # bootstrap upper bound comparison on ONE fitted dataset from each stream
            def one_bootstrap_U95(L_hat_source_first, rng_local):
                S_fit = None
                return None
            # build a single fitted covariance from a fresh raw-data draw, then compare
            # bootstrap U_0.95 computed via raw-data resampling vs Wishart resampling
            seed3 = int(rng_master.integers(0, 2**31 - 1))
            rng3 = np.random.default_rng(seed3)
            X_fit = sample_multivariate_normal(n, core.Sigma0, rng3)
            S_fit = sample_covariance(X_fit, DIVISOR)
            L_fit = core.L_cmi_cov_joint(S_fit, I_idx, B_idx, E_idx)
            L_obs_tilde = L_plugin_batch(S_fit[None], I_idx, B_idx, E_idx)[0] - beta

            # raw-data bootstrap
            Lchol_fit = np.linalg.cholesky(S_fit)
            Zb = rng3.standard_normal((M_boot_check, n, 8))
            Xb = Zb @ Lchol_fit.T
            Xb_c = Xb - Xb.mean(axis=1, keepdims=True)
            div = n if DIVISOR == "n" else n - 1
            Sb_raw = np.matmul(Xb_c.transpose(0, 2, 1), Xb_c) / div
            Lb_raw = L_plugin_batch(Sb_raw, I_idx, B_idx, E_idx) - beta
            e_raw = Lb_raw[~np.isnan(Lb_raw)] - L_fit
            U95_raw = L_obs_tilde - np.quantile(e_raw, 0.05)

            # Wishart bootstrap (same S_fit, same nu convention)
            Sb_wish = sample_covariance_wishart_batch(S_fit, n, M_boot_check, rng3)
            Lb_wish = L_plugin_batch(Sb_wish, I_idx, B_idx, E_idx) - beta
            e_wish = Lb_wish[~np.isnan(Lb_wish)] - L_fit
            U95_wish = L_obs_tilde - np.quantile(e_wish, 0.05)

            row = dict(B=str(Bkey), n=n, L_pop=L_pop, beta=beta,
                       mean_raw_Lhat=L_hat_raw.mean(), mean_wish_Lhat=L_hat_wish.mean(),
                       mean_raw_Ltilde=(L_hat_raw - beta).mean(), mean_wish_Ltilde=(L_hat_wish - beta).mean(),
                       var_raw=L_hat_raw.var(ddof=1), var_wish=L_hat_wish.var(ddof=1),
                       q05_raw=np.quantile(L_hat_raw - beta, 0.05), q05_wish=np.quantile(L_hat_wish - beta, 0.05),
                       q95_raw=np.quantile(L_hat_raw - beta, 0.95), q95_wish=np.quantile(L_hat_wish - beta, 0.95),
                       U95_raw_bootstrap=U95_raw, U95_wish_bootstrap=U95_wish,
                       R=R, M_boot_check=M_boot_check)
            rows.append(row)
            print(f"B={str(Bkey):<8} n={n:<5} mean(Lhat) raw={L_hat_raw.mean():.6f} wish={L_hat_wish.mean():.6f}  "
                  f"var raw={L_hat_raw.var(ddof=1):.7f} wish={L_hat_wish.var(ddof=1):.7f}  "
                  f"U95(boot) raw={U95_raw:.5f} wish={U95_wish:.5f}")

    import csv
    outpath = os.path.join(os.path.dirname(__file__), "data", "part1a_wishart_validation.csv")
    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nSaved to {outpath}")

    print("\nAgreement check (mean/var/quantiles should match within MC noise, "
          f"MC SE on mean ~ sd/sqrt(R={R})):")
    max_mean_diff = max(abs(r["mean_raw_Ltilde"] - r["mean_wish_Ltilde"]) for r in rows)
    max_var_reldiff = max(abs(r["var_raw"] - r["var_wish"]) / r["var_raw"] for r in rows)
    print(f"  max |mean_raw - mean_wish| (bias-corrected) = {max_mean_diff:.5f}")
    print(f"  max relative |var_raw - var_wish| = {max_var_reldiff:.4f}")
