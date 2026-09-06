"""
Part 12 (lambda=0 additivity checks): verify W_S = sum W_k, eta_S = sum eta_k,
E*_S = 1/eta_S for the Gramian-based Stage-3 formulas, as ground truth before the
full Riccati-based 31-subset sweep.
"""
import sys, os, itertools, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage3"))
import numpy as np
from scipy.linalg import solve_lyapunov
from steering_core import A_q, e_k, C_VEC, N

if __name__ == "__main__":
    print("=== Part 12 (lambda=0): multi-actuator Gramian additivity ===")
    q, T = 0.0, 1.0
    Aq = A_q(q)
    EAT = None
    from scipy.linalg import expm
    EAT = expm(-Aq * T)

    def W_single(k):
        ek = e_k(k)
        W_inf = solve_lyapunov(Aq, np.outer(ek, ek))
        return W_inf - EAT @ W_inf @ EAT.T

    nodes = [4, 5, 6, 7, 8]
    W_k = {k: W_single(k) for k in nodes}
    eta_k = {k: float(C_VEC @ W_k[k] @ C_VEC) for k in nodes}

    def W_subset_direct(S):
        Bmat = np.stack([e_k(k) for k in S], axis=1)
        M = Bmat @ Bmat.T
        W_inf = solve_lyapunov(Aq, M)
        return W_inf - EAT @ W_inf @ EAT.T

    rows = []
    max_disc = 0.0
    for r in range(1, 4):
        for S in itertools.combinations(nodes, r):
            W_sum = sum(W_k[k] for k in S)
            W_direct = W_subset_direct(S)
            disc = np.max(np.abs(W_sum - W_direct))
            max_disc = max(max_disc, disc)
            eta_sum = sum(eta_k[k] for k in S)
            eta_direct = float(C_VEC @ W_direct @ C_VEC)
            E_star = 1.0 / eta_sum
            rows.append(dict(S=str(S), eta_sum=eta_sum, eta_direct=eta_direct,
                               disc_eta=abs(eta_sum - eta_direct), disc_W=disc, E_star=E_star))
    print(f"Max |W_S - sum W_k| over all tested subsets (|S|<=3): {max_disc:.2e}")
    assert max_disc < 1e-9

    with open(os.path.join(os.path.dirname(__file__), "data", "part12a_additivity.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("Additivity verified exactly. Saved table.")
    for r in rows[:5]:
        print(" ", r)
