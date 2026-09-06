"""
Part B: explicit Gaussian plug-in CMI estimator (batched over many datasets/candidates).
Part C: exact Gaussian finite-sample bias c_d(nu), beta_pqr(n), and Monte Carlo verification.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from scipy.special import digamma
import core

RNG_ROOT = 20260818  # date-derived root seed, fixed for reproducibility, stated explicitly
COV_DIVISOR = "n"  # explicit choice: sample covariance uses divisor n (MLE), not n-1.
# The task states CMI itself is invariant to this choice (log|c*S| terms cancel in
# every one of the four covariance blocks appearing in L, since the same scalar c
# multiplies matrices of dimensions (p+r),(q+r),(r),(p+q+r) and
# c^{p+r}*c^{q+r} / (c^r * c^{p+q+r}) = c^{(p+r)+(q+r)-r-(p+q+r)} = c^0 = 1).
# The Wishart degrees of freedom nu = n-1 used in Part C assume the mean was estimated,
# regardless of which divisor convention is used for the covariance itself.


def sample_covariance(X, divisor="n"):
    n = X.shape[0]
    Xc = X - X.mean(axis=0, keepdims=True)
    d = n if divisor == "n" else n - 1
    return (Xc.T @ Xc) / d


def batched_slogdet_or_nan(M):
    """M: (..., d, d). Returns logdet, or nan (elementwise over batch) if not PD."""
    if M.shape[-1] == 0:
        return np.zeros(M.shape[:-2])
    sign, ld = np.linalg.slogdet(M)
    ld = np.where(sign > 0, ld, np.nan)
    return ld


def L_plugin_batch(S_batch, I_idx, B_idx, E_idx):
    """Batched Gaussian plug-in CMI, per the boxed Part-B formula, using joint
    covariance sub-blocks (no matrix inversion needed). S_batch: (..., 8, 8)."""
    IB = I_idx + B_idx
    EB = E_idx + B_idx
    IEB = I_idx + E_idx + B_idx

    def sub(idxs):
        return S_batch[..., idxs, :][..., :, idxs]

    ld_IB = batched_slogdet_or_nan(sub(IB))
    ld_EB = batched_slogdet_or_nan(sub(EB))
    ld_B = batched_slogdet_or_nan(sub(B_idx)) if len(B_idx) else np.zeros(S_batch.shape[:-2])
    ld_IEB = batched_slogdet_or_nan(sub(IEB))
    return 0.5 * (ld_IB + ld_EB - ld_B - ld_IEB)


# ---------------------------------------------------------------------------
# Part C: exact bias c_d(nu), beta_pqr(n)
# ---------------------------------------------------------------------------
def c_d(d, nu):
    if d == 0:
        return 0.0
    j = np.arange(1, d + 1)
    return np.sum(digamma((nu + 1 - j) / 2.0)) + d * np.log(2.0) - d * np.log(nu)


def beta_pqr(p, q, r, n):
    nu = n - 1
    return 0.5 * (c_d(p + r, nu) + c_d(q + r, nu) - c_d(r, nu) - c_d(p + q + r, nu))


def sample_multivariate_normal(n, Sigma, rng):
    Lchol = np.linalg.cholesky(Sigma)
    Z = rng.standard_normal((n, Sigma.shape[0]))
    return Z @ Lchol.T


if __name__ == "__main__":
    print("=== Part B/C ===")
    print(f"Covariance divisor convention: {COV_DIVISOR} (CMI value is invariant to this choice; "
          f"see comment in source). Wishart dof used in bias formula: nu = n-1.")

    # sanity: population CMI reproduced via batched formula on Sigma0 itself (n=inf limit, no bias)
    S0_batch = core.Sigma0[None, :, :]
    L0 = L_plugin_batch(S0_batch, core.I_IDX, [], [core.idx[n] for n in core.REST_NODES])[0]
    print(f"Sanity: batched plug-in formula at population Sigma0 (B=empty) = {L0:.11f} "
          f"vs core.L_cmi_cov_joint = {core.L_cmi_cov_joint(core.Sigma0, core.I_IDX, [], [core.idx[n] for n in core.REST_NODES]):.11f}")

    # -----------------------------------------------------------------------
    # Verify beta_pqr(n) ~ pq/(2(n-1)) + O(n^-2) for a representative (p,q,r)
    # -----------------------------------------------------------------------
    print("\nLarge-n check: beta_pqr(n) vs leading order pq/(2(n-1))")
    p, q, r = 3, 3, 2  # matches I={1,2,3}, E={6,7,8}, B={4,5}
    print(f"{'n':<10}{'beta_exact':<16}{'leading pq/2(n-1)':<20}{'residual':<14}{'residual*n^2':<14}")
    for n in [10, 30, 100, 300, 1000, 3000, 10000, 30000]:
        b = beta_pqr(p, q, r, n)
        leading = p * q / (2 * (n - 1))
        resid = b - leading
        print(f"{n:<10}{b:<16.8e}{leading:<20.8e}{resid:<14.3e}{resid*n**2:<14.4f}")
    print("residual*n^2 should stabilize (not -> 0 and not -> infinity) if residual is truly O(n^-2).")

    np.save(os.path.join(os.path.dirname(__file__), "data", "beta_check_placeholder.npy"), np.array([0]))

    # -----------------------------------------------------------------------
    # Monte Carlo bias verification: population L, analytic beta, empirical bias
    # -----------------------------------------------------------------------
    print("\n=== Monte Carlo bias check (Sigma0, I={1,2,3}) ===")
    R = 500  # independent datasets per (B, n), as suggested minimum
    n_list = [30, 50, 100, 200, 500, 1000, 5000]
    candidates = {
        (): [],
        (4,): [core.idx[4]],
        (4, 5): [core.idx[4], core.idx[5]],
    }
    I_idx = core.I_IDX
    all_rows = []
    print(f"{'B':<8}{'n':<7}{'p,q,r':<10}{'L_pop':<12}{'beta':<12}{'mean(Lhat-L)':<14}{'mean(Ltil-L)':<14}{'std(Ltil)':<12}{'RMSE(Ltil)':<12}{'n_singular':<10}")
    rng_master = np.random.default_rng(RNG_ROOT)
    for Bkey, B_idx in candidates.items():
        E_idx = [core.idx[nn] for nn in core.REST_NODES if nn not in Bkey]
        p, q, r = len(I_idx), len(E_idx), len(B_idx)
        L_pop = core.L_cmi_cov_joint(core.Sigma0, I_idx, B_idx, E_idx)
        for n in n_list:
            beta = beta_pqr(p, q, r, n)
            seed = rng_master.integers(0, 2**31 - 1)
            rng = np.random.default_rng(seed)
            L_hat_vals = []
            n_singular = 0
            for rep in range(R):
                X = sample_multivariate_normal(n, core.Sigma0, rng)
                S = sample_covariance(X, COV_DIVISOR)
                Lhat = L_plugin_batch(S[None], I_idx, B_idx, E_idx)[0]
                if np.isnan(Lhat):
                    n_singular += 1
                    continue
                L_hat_vals.append(Lhat)
            L_hat_vals = np.array(L_hat_vals)
            L_tilde_vals = L_hat_vals - beta
            mean_raw_bias = L_hat_vals.mean() - L_pop
            mean_corr_bias = L_tilde_vals.mean() - L_pop
            std_corr = L_tilde_vals.std(ddof=1)
            rmse_corr = np.sqrt(np.mean((L_tilde_vals - L_pop) ** 2))
            print(f"{str(Bkey):<8}{n:<7}{f'{p},{q},{r}':<10}{L_pop:<12.6f}{beta:<12.6f}{mean_raw_bias:<14.6f}{mean_corr_bias:<14.6f}{std_corr:<12.6f}{rmse_corr:<12.6f}{n_singular:<10}")
            all_rows.append(dict(B=str(Bkey), n=n, p=p, q=q, r=r, L_pop=L_pop, beta=beta,
                                   mean_raw_bias=mean_raw_bias, mean_corr_bias=mean_corr_bias,
                                   std_corr=std_corr, rmse_corr=rmse_corr, n_singular=n_singular, R=R))

    import csv
    outpath = os.path.join(os.path.dirname(__file__), "data", "part_c_bias_table.csv")
    with open(outpath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nSaved bias table to {outpath}")
