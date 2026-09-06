import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import core
from steering_core import eta_k_lyapunov

if __name__ == "__main__":
    print("=== Part 2K: statistical boundary strength vs. control authority (exploratory) ===")
    I_idx = core.I_IDX
    rest_nodes = core.REST_NODES
    L_empty = core.L_cmi_cov_joint(core.Sigma0, I_idx, [], [core.idx[n] for n in rest_nodes])
    delta_k = {}
    for k in rest_nodes:
        B_idx = [core.idx[k]]
        E_idx = [core.idx[n] for n in rest_nodes if n != k]
        L_k = core.L_cmi_cov_joint(core.Sigma0, I_idx, B_idx, E_idx)
        delta_k[k] = L_empty - L_k
        print(f"  Delta_{k}(empty) = L(empty) - L({{{k}}}) = {delta_k[k]:.6f}")

    q_list = [0.0, 1.0]
    T_list = [0.1, 1.0]
    rows = []
    for k in rest_nodes:
        for q in q_list:
            for T in T_list:
                eta, _, _ = eta_k_lyapunov(T, q, k)
                E_star = 1.0 / eta if eta > 0 else np.nan
                rows.append(dict(k=k, delta_k_static=delta_k[k], q=q, T=T, eta=eta, E_star=E_star))

    with open(os.path.join(os.path.dirname(__file__), "data", "part2k_comparison.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    print("\nExploratory note (n=5 non-internal nodes -- NOT a basis for correlation statistics):")
    print("Statistical Delta_k ranking (largest to smallest):", sorted(delta_k, key=lambda k: -delta_k[k]))
    for q in q_list:
        for T in T_list:
            eta_ranking = sorted(rest_nodes, key=lambda k: -eta_k_lyapunov(T, q, k)[0])
            print(f"  q={q}, T={T}: control-authority ranking (eta, largest to smallest) = {eta_ranking}")
    print("\nThe question is qualitative: does a statistically important boundary node (e.g. node 4)")
    print("remain a good actuator as q varies? Answer emerges visually in Steering Figure 8, not via")
    print("a correlation coefficient computed on 5 points.")
