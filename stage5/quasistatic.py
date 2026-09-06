"""
Stage 5, Section 8: quasi-static (instantaneous-equilibrium/oracle) boundary handoff.
Also runs a slow prescribed z-ramp with the fast Gaussian subsystem evolving, for
comparison against the pure oracle Sigma*(z) curve (used again in Section 9).
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import core5
import integrity as I
import dynamics as dyn

DELTA_PRIMARY = 0.01


def oracle_curve(z_grid, delta=DELTA_PRIMARY):
    rows = []
    for z in z_grid:
        Om = core5.Omega_of_z(z)
        L1, w1 = I.Lambda_K(Om, 1)
        L2, w2 = I.Lambda_K(Om, 2)
        L3, w3 = I.Lambda_K(Om, 3)
        Kd, achievers = I.K_delta(Om, delta)
        rows.append(dict(z=z, Lambda1=L1, B1=w1, Lambda2=L2, B2=w2, Lambda3=L3, B3=w3,
                          Kdelta=Kd, Bdelta=achievers))
    return rows


def smoothstep(u):
    u = np.clip(u, 0.0, 1.0)
    return 3 * u**2 - 2 * u**3


def slow_ramp_run(T_ramp, n_eval=600):
    """z is FORCED to follow a smoothstep ramp from -1 to +1 (open loop, u_z chosen so that the
    forced z(t) is realized exactly regardless of the y-z coupling); y is left to its own
    dynamics with u_y=0. Used to show near-equilibrium tracking when T_ramp is slow."""
    z_of_t = lambda t: -1.0 + 2.0 * smoothstep(t / T_ramp)
    zdot_of_t = lambda t: 2.0 / T_ramp * _smoothstep_deriv(t / T_ramp)

    def u_z_fn(t, state):
        y, z, m, Sigma = dyn.unpack(state)
        return dyn.TAU_Z * zdot_of_t(t) - (y - z)

    def u_y_fn(t, state):
        return 0.0

    y0 = -1.0
    z0 = -1.0
    v0 = np.array(core5.Omega_of_z(z0))
    from reference import v_of_z
    m0 = v_of_z(z0) * y0
    Sigma0 = np.linalg.inv(core5.Omega_of_z(z0))
    res = dyn.integrate(y0, z0, m0, Sigma0, T_ramp, u_y_fn=u_y_fn, u_z_fn=u_z_fn, n_eval=n_eval)
    return res


def _smoothstep_deriv(u):
    u = np.clip(u, 0.0, 1.0)
    return 6 * u - 6 * u**2


if __name__ == "__main__":
    log = []
    def p(s=""):
        print(s); log.append(s)

    p("=== Stage 5, Section 8: quasi-static boundary handoff (oracle Sigma*(z)) ===")
    z_grid = np.linspace(-1, 1, 81)
    rows = oracle_curve(z_grid)

    p(f"{'z':>7} {'L1':>10} {'B1':>14} {'L2':>10} {'B2':>16} {'L3':>10} {'B3':>10} {'K_0.01':>7} {'B_delta':>16}")
    for r in rows[::4]:
        p(f"{r['z']:7.3f} {r['Lambda1']:10.6f} {str(r['B1']):>14} {r['Lambda2']:10.6f} "
          f"{str(r['B2']):>16} {r['Lambda3']:10.6f} {str(r['B3']):>10} {str(r['Kdelta']):>7} {str(r['Bdelta']):>16}")

    # confirm qualitative 2->3->2 transition, without forcing it
    z_endA = rows[0]
    z_mid = rows[len(rows) // 2]
    z_endB = rows[-1]
    p(f"\nz=-1: Kdelta(0.01)={z_endA['Kdelta']}, achievers={z_endA['Bdelta']}  (expect 2, [(4,5)])")
    p(f"z=0 : Kdelta(0.01)={z_mid['Kdelta']}, achievers={z_mid['Bdelta']}  (expect 3, [(4,5,6)])")
    p(f"z=+1: Kdelta(0.01)={z_endB['Kdelta']}, achievers={z_endB['Bdelta']}  (expect 2, [(5,6)])")
    transition_confirmed = (z_endA["Kdelta"] == 2 and (4, 5) in z_endA["Bdelta"] and
                             z_mid["Kdelta"] == 3 and (4, 5, 6) in z_mid["Bdelta"] and
                             z_endB["Kdelta"] == 2 and (5, 6) in z_endB["Bdelta"])
    p(f"Qualitative {{4,5}} -> {{4,5,6}} -> {{5,6}} transition confirmed on this grid: {transition_confirmed}")
    if not transition_confirmed:
        p("NOTE: transition pattern not confirmed as stated -- see full table for ties/alternatives.")

    # export csv
    outcsv = os.path.join(os.path.dirname(__file__), "data", "part8_quasistatic.csv")
    with open(outcsv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["z", "Lambda1", "B1", "Lambda2", "B2", "Lambda3", "B3", "Kdelta_0.01", "Bdelta_0.01"])
        for r in rows:
            w.writerow([r["z"], r["Lambda1"], r["B1"], r["Lambda2"], r["B2"], r["Lambda3"], r["B3"],
                        r["Kdelta"], r["Bdelta"]])
    p(f"\nSaved quasi-static table to {outcsv}")

    p("\n--- Demonstration: slow forced-z ramp (T_ramp=8) fast-subsystem tracking oracle ---")
    res = slow_ramp_run(T_ramp=8.0)
    max_dev = 0.0
    for i, t in enumerate(res["t"]):
        z = res["z"][i]
        Om_z = core5.Omega_of_z(z)
        Sigma_oracle = np.linalg.inv(Om_z)
        dev = np.max(np.abs(res["Sigma"][i] - Sigma_oracle))
        max_dev = max(max_dev, dev)
    p(f"max|Sigma(t) - Sigma*(z(t))| over slow ramp (T_ramp=8) = {max_dev:.4e} (should be small: near-adiabatic)")

    np.savez(os.path.join(os.path.dirname(__file__), "data", "part8_quasistatic.npz"),
             z_grid=z_grid, L1=np.array([r["Lambda1"] for r in rows]),
             L2=np.array([r["Lambda2"] for r in rows]), L3=np.array([r["Lambda3"] for r in rows]),
             Kdelta=np.array([r["Kdelta"] for r in rows], dtype=float))
    with open(os.path.join(os.path.dirname(__file__), "data", "part8_log.txt"), "w") as f:
        f.write("\n".join(log))
    p("\nSection 8 complete.")
