import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from scipy.integrate import solve_ivp, simpson
import core
from steering_core import A_q, e_k, C_VEC, h_k, eta_k_lyapunov, N

if __name__ == "__main__":
    print("=== Part 2G: minimum-energy steering to Y(T)=Y* ===")
    Ystar = 1.0
    cases = [(0.0, 4, 1.0), (0.0, 6, 1.0), (1.0, 4, 1.0), (1.0, 6, 1.0), (0.0, 4, 3.0), (1.0, 6, 3.0)]

    rows = []
    for q, k, T in cases:
        eta, _, _ = eta_k_lyapunov(T, q, k)
        if eta < 1e-12:
            print(f"  q={q} k={k} T={T}: eta_k tiny ({eta:.3e}) -- reporting condition, not dividing blindly.")
            rows.append(dict(q=q, k=k, T=T, eta=eta, E_star=np.nan, Y_end_check=np.nan,
                               energy_integral_check=np.nan, status="eta_near_zero"))
            continue
        E_star = Ystar**2 / eta

        Aq = A_q(q)
        ek = e_k(k)

        def u_star(s):
            # u_k*(s) = (Y*/eta) h_k(T-s; q)
            hval = (C_VEC @ np_expm_neg(Aq, T - s) @ ek)
            return (Ystar / eta) * hval

        from scipy.linalg import expm as _expm
        def np_expm_neg(Aq_, t):
            return _expm(-Aq_ * t)

        def mdot(t, m):
            return -Aq @ m + ek * u_star(t)

        sol = solve_ivp(mdot, [0, T], np.zeros(N), max_step=T / 2000, rtol=1e-10, atol=1e-12)
        Y_end = C_VEC @ sol.y[:, -1]

        # energy via independent quadrature (Simpson) of u*(t)^2, not reusing eta expression
        t_grid = np.linspace(0, T, 4000)
        u_vals = np.array([u_star(s) for s in t_grid])
        energy_check = simpson(u_vals**2, x=t_grid)

        rows.append(dict(q=q, k=k, T=T, eta=eta, E_star=E_star, Y_end_check=Y_end,
                           energy_integral_check=energy_check, status="ok"))
        print(f"  q={q:<4} k={k} T={T:<4} eta_k={eta:.6e}  E*={E_star:.6f}  "
              f"Y(T) achieved={Y_end:.8f} (target 1.0)  energy(quad)={energy_check:.6f} (should = E*)")
        assert abs(Y_end - Ystar) < 1e-4, f"failed to reach target: {Y_end}"
        assert abs(energy_check - E_star) / E_star < 1e-3, f"energy mismatch: {energy_check} vs {E_star}"

    with open(os.path.join(os.path.dirname(__file__), "data", "part2g_min_energy_steering.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("\nAll representative minimum-energy control cases verified: Y(T)=1 achieved, energy matches E*.")
