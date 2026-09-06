"""
Part 12: exhaustive multi-actuator extension. All 31 nonempty subsets of {4,5,6,7,8},
organization-aware Riccati solver at each (q,T,lambda), Pareto analysis per cardinality.
"""
import sys, os, csv, time, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from riccati_solver import solve_organization_aware

DATADIR = os.path.join(os.path.dirname(__file__), "data")

NODES = [4, 5, 6, 7, 8]
ALL_SUBSETS = []
for r in range(1, len(NODES) + 1):
    for S in itertools.combinations(NODES, r):
        ALL_SUBSETS.append(S)
assert len(ALL_SUBSETS) == 31

LAMBDA_GRID = np.concatenate([[0.0], np.geomspace(1e-4, 1e6, 41)])
Q_LIST = [-1, 0, 1]
T_LIST = [0.1, 1, 3]

if __name__ == "__main__":
    print("=== Part 12: exhaustive 31-subset multi-actuator sweep ===")
    total = len(ALL_SUBSETS) * len(Q_LIST) * len(T_LIST) * len(LAMBDA_GRID)
    print(f"Grid: 31 subsets x q={Q_LIST} x T={T_LIST} x {len(LAMBDA_GRID)} lambda values = {total} solves")

    rows = []
    unreachable = 0
    t0 = time.time()
    for S in ALL_SUBSETS:
        for q in Q_LIST:
            for T in T_LIST:
                for lam in LAMBDA_GRID:
                    try:
                        res = solve_organization_aware(q, T, list(S), lam, n_eval=100)
                    except ValueError:
                        unreachable += 1
                        continue
                    rows.append(dict(S=str(S), size=len(S), q=q, T=T, lam=lam,
                                       E=res["E"], D=res["D"], y_T=res["y_T"]))
    elapsed = time.time() - t0
    print(f"Completed {len(rows)} solves in {elapsed:.1f}s ({unreachable} unreachable)")

    with open(os.path.join(DATADIR, "part12_multiactuator_sweep.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("Saved part12_multiactuator_sweep.csv")

    # Pareto frontier per cardinality, at representative (q,T)
    print("\nNondominated subsets per cardinality at q=0,T=1,lambda=0 (pure energy):")
    for size in range(1, 6):
        sub = [r for r in rows if r["size"] == size and r["q"] == 0.0 and r["T"] == 1.0 and r["lam"] == 0.0]
        sub_sorted = sorted(sub, key=lambda r: r["E"])
        if sub_sorted:
            print(f"  |S|={size}: best E={sub_sorted[0]['E']:.4f} via S={sub_sorted[0]['S']}")
