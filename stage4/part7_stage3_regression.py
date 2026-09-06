"""
Part 7: at lambda=0, Stage-4's Riccati solution must reproduce Stage-3's verified
minimum-energy control exactly (within numerical tolerance). Regression test.
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage3"))
import numpy as np
from steering_core import eta_k_lyapunov
from riccati_solver import solve_organization_aware

if __name__ == "__main__":
    print("=== Part 7: Stage-3 recovery at lambda=0 ===")
    cases = [(0.0, 4, 1.0), (0.0, 6, 1.0), (1.0, 4, 1.0), (1.0, 6, 1.0), (0.0, 4, 3.0), (1.0, 6, 3.0),
             (-1.0, 5, 0.5), (2.0, 4, 2.0)]
    rows = []
    max_rel_E_err = 0.0
    for q, k, T in cases:
        eta, _, _ = eta_k_lyapunov(T, q, k)
        E_star_stage3 = 1.0 / eta

        res = solve_organization_aware(q, T, [k], lam=0.0)
        rel_err = abs(res["E"] - E_star_stage3) / E_star_stage3
        max_rel_E_err = max(max_rel_E_err, rel_err)
        print(f"q={q:<5} k={k} T={T:<4} E_stage3={E_star_stage3:.6f}  E_stage4(lam=0)={res['E']:.6f}  "
              f"rel.err={rel_err:.2e}  y(T)={res['y_T']:.8f}")
        rows.append(dict(q=q, k=k, T=T, E_stage3=E_star_stage3, E_stage4=res["E"], rel_err=rel_err,
                           y_T=res["y_T"]))
        assert rel_err < 1e-3, f"REGRESSION FAILURE: Stage-4 lambda=0 does not match Stage-3 for q={q},k={k},T={T}"
        assert abs(res["y_T"] - 1.0) < 1e-5

    print(f"\nMax relative energy error across all regression cases: {max_rel_E_err:.2e}")
    with open(os.path.join(os.path.dirname(__file__), "data", "part7_stage3_regression.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("PASSED: Stage-4 lambda=0 solution reproduces Stage-3 minimum-energy control.")
