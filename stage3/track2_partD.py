import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import core
from steering_core import h_k

if __name__ == "__main__":
    print("=== Part 2D: impulse response h_k(t;q) ===")
    q_list = [-2, -1, -0.5, 0, 0.5, 1, 2]
    t_grid = np.concatenate([np.linspace(0, 0.5, 200), np.linspace(0.5, 6, 300)[1:]])

    print("Symmetry check: Q_q couples only nodes 3 and 6, so full {1,2,3}/{6,7,8} permutation")
    print("symmetry is expected ONLY at q=0. For q!=0, node 3 is singled out within {1,2,3} and")
    print("node 6 is singled out within {6,7,8}; the residual pairs {1,2} and {7,8} should stay symmetric.")
    for q in [0, 1]:
        h1 = h_k(t_grid, q, 1); h2 = h_k(t_grid, q, 2); h3 = h_k(t_grid, q, 3)
        h6 = h_k(t_grid, q, 6); h7 = h_k(t_grid, q, 7); h8 = h_k(t_grid, q, 8)
        d12 = np.max(np.abs(h1 - h2)); d13 = np.max(np.abs(h1 - h3))
        d78 = np.max(np.abs(h7 - h8)); d67 = np.max(np.abs(h6 - h7))
        print(f"  q={q}: max|h1-h2|={d12:.3e}  max|h1-h3|={d13:.3e}  max|h7-h8|={d78:.3e}  max|h6-h7|={d67:.3e}")
        if q == 0:
            assert max(d12, d13, d78, d67) < 1e-9, "expected exact full symmetry at q=0"
        else:
            assert d12 < 1e-9 and d78 < 1e-9, "expected {1,2} and {7,8} to remain symmetric even at q!=0"
            assert d13 > 1e-6 and d67 > 1e-6, "expected node 3 and node 6 to break symmetry at q!=0"
    print("Confirmed: {1,2} and {7,8} stay exactly symmetric for all q; node 3 and node 6 (the pair")
    print("directly coupled by Q_q) are the only nodes whose impulse response is q-dependent asymmetrically.")

    data = {"t": t_grid}
    rows_summary = []
    for q in q_list:
        for k in range(1, 9):
            hk = h_k(t_grid, q, k)
            data[f"h_{k}_q{q}"] = hk
            group = "interior" if k in (1, 2, 3) else ("blanket" if k in (4, 5) else "exterior")
            rows_summary.append(dict(q=q, k=k, group=group, h_at_t0=hk[0], h_max_abs=np.max(np.abs(hk)),
                                       t_of_max_abs=t_grid[np.argmax(np.abs(hk))]))
    np.savez(os.path.join(os.path.dirname(__file__), "data", "part2d_impulse_response.npz"), **data)
    with open(os.path.join(os.path.dirname(__file__), "data", "part2d_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_summary[0].keys()))
        w.writeheader(); w.writerows(rows_summary)
    print(f"\nSaved impulse-response grid ({len(t_grid)} time points x {len(q_list)} q values x 8 nodes) and summary.")
