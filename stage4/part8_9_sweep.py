"""
Part 8: Pareto monotonicity audit (E nondecreasing, D nonincreasing with lambda).
Part 9: single-actuator E-D analysis over q,T,lambda grid, with representative full trajectories.
"""
import sys, os, csv, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stage3"))
import numpy as np
import core
from steering_core import C_VEC, N
from organization_core import Q_perp, v_vec
from riccati_solver import solve_organization_aware

DATADIR = os.path.join(os.path.dirname(__file__), "data")

LAMBDA_GRID = np.concatenate([[0.0], np.geomspace(1e-4, 1e6, 41)])
ACTUATORS = [1, 4, 5, 6, 7, 8]  # 1 kept as internal reference only, not "externally accessible"
Q_LIST = [-2, -1, 0, 1, 2]
T_LIST = [0.1, 1, 3]

MONOTONICITY_TOL = 1e-4  # relative tolerance for Pareto monotonicity audit

if __name__ == "__main__":
    print("=== Part 8/9: single-actuator organization-aware sweep ===")
    print(f"Grid: actuators={ACTUATORS}, q={Q_LIST}, T={T_LIST}, lambda grid size={len(LAMBDA_GRID)}")
    total = len(ACTUATORS) * len(Q_LIST) * len(T_LIST) * len(LAMBDA_GRID)
    print(f"Total solves: {total}")

    rows = []
    reversal_log = []
    unreachable_log = []
    t0 = time.time()
    for k in ACTUATORS:
        for q in Q_LIST:
            for T in T_LIST:
                prev_E, prev_D = None, None
                cell_rows = []
                for lam in LAMBDA_GRID:
                    try:
                        res = solve_organization_aware(q, T, [k], lam, n_eval=200)
                    except ValueError as e:
                        unreachable_log.append(dict(k=k, q=q, T=T, lam=lam, error=str(e)))
                        continue
                    r_T = res["m"][:, -1] - v_vec  # residual r(T) = m(T) - v (since y(T)=1)
                    row = dict(k=k, q=q, T=T, lam=lam, E=res["E"], D=res["D"], Dbar=res["Dbar"],
                               D_T=res["D_T"], D_max=res["D_max"], y_T=res["y_T"],
                               resid_norm=np.linalg.norm(r_T))
                    for i, n in enumerate(range(1, 9)):
                        row[f"m_T_{n}"] = res["m"][i, -1]
                    cell_rows.append(row)

                    if prev_E is not None:
                        # monotonicity audit: E should be nondecreasing, D nonincreasing, as lambda increases
                        if res["E"] < prev_E * (1 - MONOTONICITY_TOL) - 1e-9:
                            reversal_log.append(dict(k=k, q=q, T=T, lam_prev="...", lam=lam,
                                                       kind="E_decreased", prev_E=prev_E, E=res["E"]))
                        if res["D"] > prev_D * (1 + MONOTONICITY_TOL) + 1e-9:
                            reversal_log.append(dict(k=k, q=q, T=T, lam=lam, kind="D_increased",
                                                       prev_D=prev_D, D=res["D"]))
                    prev_E, prev_D = res["E"], res["D"]
                rows.extend(cell_rows)
    elapsed = time.time() - t0
    print(f"\nCompleted {len(rows)} solves in {elapsed:.1f}s ({len(unreachable_log)} unreachable/skipped)")
    print(f"Monotonicity reversals flagged (tol={MONOTONICITY_TOL}): {len(reversal_log)}")
    for r in reversal_log[:20]:
        print("  REVERSAL:", r)

    with open(os.path.join(DATADIR, "part9_single_actuator_sweep.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"Saved sweep table ({len(rows)} rows) to part9_single_actuator_sweep.csv")

    if reversal_log:
        with open(os.path.join(DATADIR, "part8_monotonicity_reversals.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=sorted(set(k for r in reversal_log for k in r)))
            w.writeheader(); w.writerows(reversal_log)
        print("Saved reversal log.")
    else:
        print("No monotonicity reversals found beyond tolerance.")

    if unreachable_log:
        with open(os.path.join(DATADIR, "part9_unreachable_log.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(unreachable_log[0].keys()))
            w.writeheader(); w.writerows(unreachable_log)
        print(f"Saved {len(unreachable_log)} unreachable-target entries.")
