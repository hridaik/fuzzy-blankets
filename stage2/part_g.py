"""
Part G: null-test diagnostic (Gaussian conditional-independence likelihood-ratio statistic
vs asymptotic chi-square(pq) approximation). Diagnostic only -- not used for selection.
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from scipy import stats
import core
from part_b_c import sample_covariance, sample_multivariate_normal, L_plugin_batch, COV_DIVISOR

RNG_ROOT = 20260818 + 3

if __name__ == "__main__":
    print("=== Part G: LR statistic vs chi-square(pq) diagnostic ===")
    I_idx = core.I_IDX
    Bkey, B_idx = (4, 5), [core.idx[4], core.idx[5]]
    E_idx = [core.idx[nn] for nn in core.REST_NODES if nn not in Bkey]
    p, q, r = len(I_idx), len(E_idx), len(B_idx)
    dof = p * q
    print(f"Exact blanket case: I={{1,2,3}}, B={{4,5}}, E={{6,7,8}}; p={p}, q={q}, dof=pq={dof}")

    R = 2000
    n_list = [30, 50, 100, 200, 500, 1000]
    rng_master = np.random.default_rng(RNG_ROOT)
    rows = []
    for n in n_list:
        seed = int(rng_master.integers(0, 2**31 - 1))
        rng = np.random.default_rng(seed)
        # LR statistic: 2n * Lhat under H0 (exact blanket, true L_pop=0) is the standard
        # Gaussian conditional-independence LR test statistic (Wilks), asymptotically chi2(pq).
        stat_vals = []
        for rep in range(R):
            X = sample_multivariate_normal(n, core.Sigma0, rng)
            S = sample_covariance(X, COV_DIVISOR)
            Lhat = L_plugin_batch(S[None], I_idx, B_idx, E_idx)[0]
            if np.isnan(Lhat):
                continue
            stat_vals.append(2 * n * Lhat)
        stat_vals = np.array(stat_vals)
        emp_mean = stat_vals.mean()
        emp_var = stat_vals.var(ddof=1)
        theo_mean = dof
        theo_var = 2 * dof
        # KS test against chi2(dof)
        ks_stat, ks_p = stats.kstest(stat_vals, 'chi2', args=(dof,))
        # empirical vs theoretical rejection rate at alpha=0.05 (upper tail)
        crit = stats.chi2.ppf(0.95, dof)
        emp_reject_rate = np.mean(stat_vals > crit)
        rows.append(dict(n=n, dof=dof, R_eff=len(stat_vals), emp_mean=emp_mean, theo_mean=theo_mean,
                           emp_var=emp_var, theo_var=theo_var, ks_stat=ks_stat, ks_p=ks_p,
                           chi2_crit_95=crit, emp_reject_rate_alpha05=emp_reject_rate))
        print(f"n={n:<6} R_eff={len(stat_vals):<6} emp_mean={emp_mean:.3f} (theo {theo_mean})  "
              f"emp_var={emp_var:.3f} (theo {theo_var:.3f})  KS_stat={ks_stat:.4f} KS_p={ks_p:.4f}  "
              f"emp_reject@0.05={emp_reject_rate:.4f} (nominal 0.05)")

    outpath = os.path.join(os.path.dirname(__file__), "data", "part_g_null_diagnostic.csv")
    with open(outpath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved to {outpath}")
    print("\nInterpretation: at small n the chi-square approximation typically over-rejects (LR stat")
    print("skewed/inflated relative to chi2); it should improve monotonically (not necessarily strictly)")
    print("as n grows. This is a diagnostic only -- Part E's delta/bootstrap rule remains the selection method.")
