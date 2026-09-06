import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from steering_core import eta_k_lyapunov, eta_k_quadrature, h_k

if __name__ == "__main__":
    print("=== Part 2F: finite-horizon controllability Gramian cross-verification ===")
    q_list = [-1, 0, 1]
    T_list = [0.1, 0.5, 1.0, 3.0]
    rows = []
    max_disc_lyap_quad = 0.0
    max_disc_eta_hsq = 0.0
    for q in q_list:
        for T in T_list:
            for k in range(1, 9):
                eta_lyap, W_T, W_inf = eta_k_lyapunov(T, q, k)
                eta_quad = eta_k_quadrature(T, q, k, n_grid=4000)
                disc = abs(eta_lyap - eta_quad)
                max_disc_lyap_quad = max(max_disc_lyap_quad, disc)

                # independent check: eta_k(T) = int_0^T h_k(t)^2 dt, via direct trapezoid on h_k
                t_grid = np.linspace(0, T, 3000)
                hk = h_k(t_grid, q, k)
                eta_from_hsq = np.trapezoid(hk**2, t_grid)
                disc2 = abs(eta_lyap - eta_from_hsq)
                max_disc_eta_hsq = max(max_disc_eta_hsq, disc2)

                rows.append(dict(q=q, T=T, k=k, eta_lyapunov=eta_lyap, eta_quadrature=eta_quad,
                                   eta_from_h_squared=eta_from_hsq,
                                   disc_lyap_vs_quad=disc, disc_lyap_vs_hsq=disc2))
    print(f"Max |eta_lyapunov - eta_quadrature(Simpson)| over all (q,T,k) = {max_disc_lyap_quad:.3e}")
    print(f"Max |eta_lyapunov - integral(h_k^2)(trapezoid)|              = {max_disc_eta_hsq:.3e}")
    assert max_disc_lyap_quad < 1e-6
    assert max_disc_eta_hsq < 1e-5

    with open(os.path.join(os.path.dirname(__file__), "data", "part2f_gramian_crosscheck.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("Saved Gramian cross-verification table. All three independent computation routes agree.")
