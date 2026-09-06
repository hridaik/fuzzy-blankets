import sys, os, csv, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage2"))
import numpy as np
import core
from part_b_c import L_plugin_batch, beta_pqr
from wishart import sample_covariance_wishart_batch

RNG_ROOT = 2026081903

if __name__ == "__main__":
    print("=== Part 1E: certification margin M_delta(B) = delta - L_pop(B) ===")
    I_idx = core.I_IDX

    def cand(Bkey):
        B_idx = [core.idx[nn] for nn in Bkey]
        E_idx = [core.idx[nn] for nn in core.REST_NODES if nn not in Bkey]
        return B_idx, E_idx

    candidates = [(), (4,), (5,), (4, 5), (4, 6), (4, 5, 6)]
    n_list = [200, 1000, 5000]
    delta_grid = [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25]
    R_outer = 2000
    M_boot = 500
    alpha = 0.05

    rows = []
    rng_master = np.random.default_rng(RNG_ROOT)
    t0all = time.time()
    for Bkey in candidates:
        B_idx, E_idx = cand(Bkey)
        p, q, r = len(I_idx), len(E_idx), len(B_idx)
        L_pop = core.L_cmi_cov_joint(core.Sigma0, I_idx, B_idx, E_idx)
        for n in n_list:
            beta_val = beta_pqr(p, q, r, n)
            seed = int(rng_master.integers(0, 2**31 - 1))
            rng = np.random.default_rng(seed)
            U_vals = []
            t0 = time.time()
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
                e_b = (Lb_raw[valid] - beta_val) - L_fit
                U95 = L_obs_tilde - np.quantile(e_b, alpha)
                U_vals.append(U95)
            U_vals = np.array(U_vals)
            elapsed = time.time() - t0
            for delta in delta_grid:
                cert_prob = np.mean(U_vals <= delta) if len(U_vals) else np.nan
                margin = delta - L_pop
                rows.append(dict(B=str(Bkey), n=n, L_pop=L_pop, delta=delta, margin=margin,
                                   cert_prob=cert_prob, n_eff=len(U_vals)))
            print(f"B={str(Bkey):<10} n={n:<6} L_pop={L_pop:.5f} ({elapsed:.1f}s, n_eff={len(U_vals)})")

    print(f"\nTotal wall time: {time.time()-t0all:.1f}s")
    outpath = os.path.join(os.path.dirname(__file__), "data", "track1_partE_margin.csv")
    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"Saved to {outpath}")

    print("\nIllustrating: small positive margin -> hard to certify even with substantial data.")
    for Bkey in [(4, 5)]:
        sub = [r for r in rows if r["B"] == str(Bkey) and r["n"] == 1000]
        for r in sorted(sub, key=lambda r: r["margin"])[:6]:
            print(f"  B={r['B']} n={r['n']} delta={r['delta']:.3f} margin={r['margin']:.4f} "
                  f"cert_prob={r['cert_prob']:.3f}")
