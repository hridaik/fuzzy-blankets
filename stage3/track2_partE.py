import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from steering_core import g_k

if __name__ == "__main__":
    print("=== Part 2E: static gain g_k(q) ===")
    g0 = {k: g_k(0.0, k) for k in range(1, 9)}
    expected0 = {1: 211/1065, 2: 211/1065, 3: 211/1065, 4: 8/71, 5: 7/71,
                 6: 23/355, 7: 23/355, 8: 23/355}
    print("q=0 exact-fraction check:")
    for k in range(1, 9):
        diff = abs(g0[k] - expected0[k])
        print(f"  g_{k}(0) = {g0[k]:.10f}  expected {expected0[k]:.10f}  diff={diff:.2e}")
        assert diff < 1e-9

    print("\nq-invariance check for k in {1,2,4,5,7,8}:")
    q_list = [-2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2]
    rows = []
    for q in q_list:
        gk = {k: g_k(q, k) for k in range(1, 9)}
        for k in [1, 2, 4, 5, 7, 8]:
            diff = abs(gk[k] - g0[k])
            assert diff < 1e-9, f"g_{k}({q}) should equal g_{k}(0), diff={diff}"
        g3_analytic = (g0[3] + q * g0[6]) / (1 + q**2)
        g6_analytic = (-q * g0[3] + g0[6]) / (1 + q**2)
        d3 = abs(gk[3] - g3_analytic)
        d6 = abs(gk[6] - g6_analytic)
        print(f"  q={q:<5} g3={gk[3]:.8f} (analytic {g3_analytic:.8f}, diff {d3:.2e})  "
              f"g6={gk[6]:.8f} (analytic {g6_analytic:.8f}, diff {d6:.2e})")
        assert d3 < 1e-9 and d6 < 1e-9
        rows.append(dict(q=q, **{f"g{k}": gk[k] for k in range(1, 9)},
                          g3_analytic=g3_analytic, g6_analytic=g6_analytic))

    print("\nSpot checks:")
    g1 = {k: g_k(1.0, k) for k in range(1, 9)}
    gm1 = {k: g_k(-1.0, k) for k in range(1, 9)}
    checks = [("g3(1)", g1[3], 28/213), ("g6(1)", g1[6], -1/15),
              ("g3(-1)", gm1[3], 1/15), ("g6(-1)", gm1[6], 28/213)]
    for label, got, exp in checks:
        print(f"  {label} = {got:.10f}  expected {exp:.10f}  diff={abs(got-exp):.2e}")
        assert abs(got - exp) < 1e-9

    q_dense = np.linspace(-2, 2, 161)
    dense_rows = []
    for q in q_dense:
        gk = {k: g_k(q, k) for k in range(1, 9)}
        dense_rows.append(dict(q=q, **{f"g{k}": gk[k] for k in range(1, 9)}))

    with open(os.path.join(os.path.dirname(__file__), "data", "part2e_static_gain.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(dense_rows[0].keys()))
        w.writeheader(); w.writerows(dense_rows)
    print(f"\nAll Part 2E identities verified exactly. Saved dense g_k(q) grid ({len(q_dense)} points).")
