"""Figure 10: Finite-data recovery -- oracle vs. estimated Lambda_3(t), K_delta(t), inferred B_t,
for n=50,200,1000, at the same z-checkpoints used in Section 17 (recomputed here directly at
each n so all three sample sizes appear on one figure)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import core5
import integrity as I
import finite_data as fd
from reference import v_of_z

Z_CHECKPOINTS = [-1.0, -0.5, 0.0, 0.5, 1.0]
N_LIST = [50, 200, 1000]
N_REPS = 100  # matches finite_data.py --scale full's R, for consistency

if __name__ == "__main__":
    rng = np.random.default_rng(31337)
    oracle_L3 = []
    for z in Z_CHECKPOINTS:
        Om = core5.Omega_of_z(z)
        Sigma_z = np.linalg.inv(Om)
        L3, _ = I.Lambda_K(Sigma_z, 3, from_precision=False)
        oracle_L3.append(L3)
    oracle_L3 = np.array(oracle_L3)

    results = {n: dict(L3_mean=[], L3_lo=[], L3_hi=[], Kdelta_mode=[]) for n in N_LIST}
    for n in N_LIST:
        for z in Z_CHECKPOINTS:
            Om = core5.Omega_of_z(z)
            Sigma_z = np.linalg.inv(Om)
            mu_z = v_of_z(z) * 0.0
            Lchol = np.linalg.cholesky(Sigma_z)
            L_vals, Kd_vals = [], []
            for rep in range(N_REPS):
                X = mu_z[None, :] + rng.standard_normal((n, core5.N)) @ Lchol.T
                half = n // 2
                X_sel, X_val = X[:half], X[half:]
                winners, Lmin_sel, _ = fd.select_boundary_from_sample(X_sel)
                B_star = winners[0]
                L_val = fd.validate_boundary(X_val, B_star)
                if not np.isnan(L_val):
                    L_vals.append(L_val)
                    Kd_vals.append(len(B_star) if L_val <= 0.01 else 4)
            L_vals = np.array(L_vals)
            results[n]["L3_mean"].append(np.mean(L_vals))
            results[n]["L3_lo"].append(np.percentile(L_vals, 16))
            results[n]["L3_hi"].append(np.percentile(L_vals, 84))
            results[n]["Kdelta_mode"].append(np.median(Kd_vals))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8))
    z_arr = np.array(Z_CHECKPOINTS)
    ax1.plot(z_arr, oracle_L3, "k--", lw=2, label="oracle", zorder=5)
    colors = [fs.COLOR_INTERIOR, fs.COLOR_BOUNDARY, fs.COLOR_ACCENT]
    for n, c in zip(N_LIST, colors):
        r = results[n]
        ax1.plot(z_arr, r["L3_mean"], "-o", color=c, label=f"n={n}", ms=4)
        ax1.fill_between(z_arr, r["L3_lo"], r["L3_hi"], color=c, alpha=0.18)
    ax1.axhline(0.01, color="gray", ls=":", lw=1)
    ax1.set_xlabel("z"); ax1.set_ylabel(r"$\Lambda_3$ (validation estimate, nats)")
    ax1.set_title(r"Estimated $\Lambda_3(z)$ vs. oracle, by sample size")
    ax1.legend(fontsize=8.5)

    for n, c in zip(N_LIST, colors):
        ax2.plot(z_arr, results[n]["Kdelta_mode"], "-o", color=c, label=f"n={n}", ms=4)
    ax2.set_xlabel("z"); ax2.set_ylabel(r"median inferred $K_\delta$")
    ax2.set_title(r"Inferred $K_\delta(z)$ ($\delta=0.01$) vs. sample size (median of "
                  f"{N_REPS} reps; shaded band in left panel is 16-84th pctile)")
    ax2.legend(fontsize=8.5)
    ax2.set_yticks([1, 2, 3, 4])

    fig.suptitle("What survives when the oracle covariance is replaced by finite stochastic data "
                 f"(selection/validation split, {N_REPS} reps per (n,z))", fontsize=10.5, y=1.03)
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig10_finite_data_recovery")
    fs.save_all(fig, outpath)
    plt.close(fig)
    print("Saved", outpath)
