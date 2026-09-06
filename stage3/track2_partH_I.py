import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from steering_core import A_q, e_k, C_VEC, h_k, eta_k_lyapunov, N

if __name__ == "__main__":
    print("=== Part 2H: short-horizon analytic checks at q=0 ===")
    Aq0 = A_q(0.0)

    def deriv_coeffs(k, order=3):
        """c^T (-A)^m e_k for m=0..order, i.e. Taylor coefficients of h_k(t) = c^T e^{-At} e_k."""
        ek = e_k(k)
        coeffs = []
        v = ek.copy()
        for m in range(order + 1):
            coeffs.append(float(C_VEC @ v))
            v = -Aq0 @ v
        return coeffs  # [h(0), h'(0), h''(0)/1!... actually these are c^T(-A)^m e_k = m! * (coeff of t^m)]

    print("\nInternal nodes 1,2,3 (expect h(0)=1/3):")
    for k in [1, 2, 3]:
        c = deriv_coeffs(k, 0)
        print(f"  k={k}: h_k(0) = {c[0]:.10f}  (expected 1/3 = {1/3:.10f})")
        assert abs(c[0] - 1/3) < 1e-9

    print("\nBlanket node 4 (expect h'(0)=1):")
    c4 = deriv_coeffs(4, 1)
    print(f"  h_4(0)={c4[0]:.3e} (expect 0)  h_4'(0)={c4[1]:.10f} (expect 1)")
    assert abs(c4[0]) < 1e-9 and abs(c4[1] - 1.0) < 1e-9

    print("\nBlanket node 5 (expect h'(0)=1/2):")
    c5 = deriv_coeffs(5, 1)
    print(f"  h_5(0)={c5[0]:.3e} (expect 0)  h_5'(0)={c5[1]:.10f} (expect 0.5)")
    assert abs(c5[0]) < 1e-9 and abs(c5[1] - 0.5) < 1e-9

    print("\nExterior nodes 6,7,8 (expect h(0)=h'(0)=0, h''(0)=5/4):")
    for k in [6, 7, 8]:
        c = deriv_coeffs(k, 2)
        print(f"  k={k}: h(0)={c[0]:.3e}  h'(0)={c[1]:.3e}  h''(0)={c[2]:.10f} (expect 1.25)")
        assert abs(c[0]) < 1e-9 and abs(c[1]) < 1e-9 and abs(c[2] - 1.25) < 1e-9

    # small-T log-log slope checks (careful range selection to avoid higher-order contamination)
    print("\nSmall-T log-log slope verification (eta_k(T) ~ T^p):")

    def loglog_slope(T_vals, eta_vals):
        lx = np.log(T_vals); ly = np.log(eta_vals)
        A = np.vstack([lx, np.ones_like(lx)]).T
        slope, intercept = np.linalg.lstsq(A, ly, rcond=None)[0]
        return slope

    checks = [
        ("internal k=1", 1, 1.0, [1e-4, 2e-4, 4e-4, 8e-4]),
        ("blanket k=4", 4, 3.0, [1e-3, 2e-3, 4e-3, 8e-3]),
        ("blanket k=5", 5, 3.0, [1e-3, 2e-3, 4e-3, 8e-3]),
        ("exterior k=6", 6, 5.0, [1e-3, 2e-3, 4e-3, 8e-3]),
    ]
    rows_h = []
    for label, k, expected_slope, T_probe in checks:
        etas = [eta_k_lyapunov(T, 0.0, k)[0] for T in T_probe]
        slope = loglog_slope(np.array(T_probe), np.array(etas))
        print(f"  {label}: fitted slope={slope:.4f}  expected={expected_slope}  "
              f"(T probe range {T_probe[0]:.0e}-{T_probe[-1]:.0e})")
        rows_h.append(dict(label=label, k=k, expected_slope=expected_slope, fitted_slope=slope))
        assert abs(slope - expected_slope) < 0.05, f"slope mismatch for {label}: {slope} vs {expected_slope}"

    # analytic E*_k(T) leading-order prefactors
    print("\nLeading-order E*_k(T) prefactor checks (E* = 1/eta at Y*=1):")
    T_small = 1e-3
    exp_E = {1: 9 / T_small, 4: 3 / T_small**3, 5: 12 / T_small**3, 6: 64 / (5 * T_small**5)}
    for k, exp in exp_E.items():
        eta, _, _ = eta_k_lyapunov(T_small, 0.0, k)
        E_star = 1.0 / eta
        rel_err = abs(E_star - exp) / exp
        print(f"  k={k}: E*({T_small:.0e}) = {E_star:.4e}  leading-order predicted = {exp:.4e}  rel.err={rel_err:.4f}")

    with open(os.path.join(os.path.dirname(__file__), "data", "part2h_slope_checks.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_h[0].keys()))
        w.writeheader(); w.writerows(rows_h)
    print("\nAll Part 2H short-horizon checks passed.")

    # -------------------------------------------------------------------
    print("\n=== Part 2I: nonequilibrium short-time coefficients (general q) ===")

    def hprime0(q, k):
        Aq = A_q(q)
        ek = e_k(k)
        return float(C_VEC @ (-Aq) @ ek)

    q_list = [-2, -1, -0.5, 0.5, 1, 2]
    rows_i = []
    for q in q_list:
        hp4 = hprime0(q, 4); exp4 = 1 + q / 3
        hp5 = hprime0(q, 5); exp5 = 0.5 + q / 6
        hp6 = hprime0(q, 6); exp6 = -1.5 * q
        hp7 = hprime0(q, 7); hp8 = hprime0(q, 8); exp78 = q / 3
        print(f"  q={q:<5} h4'(0)={hp4:.6f}(exp {exp4:.6f})  h5'(0)={hp5:.6f}(exp {exp5:.6f})  "
              f"h6'(0)={hp6:.6f}(exp {exp6:.6f})  h7'(0)={hp7:.6f} h8'(0)={hp8:.6f}(exp {exp78:.6f})")
        for got, exp in [(hp4, exp4), (hp5, exp5), (hp6, exp6), (hp7, exp78), (hp8, exp78)]:
            assert abs(got - exp) < 1e-9
        rows_i.append(dict(q=q, hprime4=hp4, hprime5=hp5, hprime6=hp6, hprime7=hp7, hprime8=hp8))

    print("\nEta_6(T) ~ [h6'(0)]^2/3 * T^3 = (1.5q)^2/3 T^3 = (3/4) q^2 T^3 check, "
          "and E*_6(T) ~ 4/(3 q^2 T^3):")
    for q in [1.0, -1.0, 2.0]:
        T_small = 1e-3
        eta6, _, _ = eta_k_lyapunov(T_small, q, 6)
        pred = (1.5 * q) ** 2 / 3 * T_small**3
        print(f"  q={q}: eta_6({T_small:.0e}) = {eta6:.6e}  predicted = {pred:.6e}  "
              f"rel.err={abs(eta6-pred)/pred:.4f}")

    # analytic crossover between node 6 and node 4 from short-horizon coefficients
    print("\nAnalytic crossover q* where eta_6(T)=eta_4(T) at leading order (T-independent ratio):")
    print("  eta_4 ~ (1+q/3)^2/3 T^3 ;  eta_6 ~ (1.5q)^2/3 T^3")
    print("  crossover: (1+q/3)^2 = (1.5q)^2  =>  1+q/3 = +-1.5q")
    # solve exactly with sympy-free algebra:
    # case +: 1 + q/3 = 1.5q -> 1 = 1.5q - q/3 = (9q-2q)/6=7q/6 -> q=6/7
    # case -: 1 + q/3 = -1.5q -> 1 = -1.5q - q/3 = -(11q)/6 -> q = -6/11
    q_plus = 6 / 7
    q_minus = -6 / 11
    print(f"  q* = 6/7 = {q_plus:.6f}   and   q* = -6/11 = {q_minus:.6f}")

    def eta4_lead(q, T): return (1 + q/3)**2 / 3 * T**3
    def eta6_lead(q, T): return (1.5*q)**2 / 3 * T**3
    for q in [q_plus, q_minus]:
        r = eta6_lead(q, 1.0) / eta4_lead(q, 1.0)
        print(f"    check at q={q:.6f}: eta6_lead/eta4_lead = {r:.6f} (expect 1.0)")
        assert abs(r - 1.0) < 1e-9

    with open(os.path.join(os.path.dirname(__file__), "data", "part2i_hprime0.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_i[0].keys()))
        w.writeheader(); w.writerows(rows_i)
    print("\nAll Part 2I identities and crossover values verified exactly (analytic, before finite-T check).")
