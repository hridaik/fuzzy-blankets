"""
Part 10: compare Stage-3 (lambda=0) energy ranking with organization-aware rankings at nonzero lambda.
Part 11: terminal-distortion diagnostic (does minimizing D produce large D_T or D_max near T?).
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np

DATADIR = os.path.join(os.path.dirname(__file__), "data")
EXTERNAL_NODES = [4, 5, 6, 7, 8]

if __name__ == "__main__":
    rows = []
    with open(os.path.join(DATADIR, "part9_single_actuator_sweep.csv")) as f:
        for r in csv.DictReader(f):
            rows.append({k: (float(v) if k not in ("k",) else int(float(v))) for k, v in r.items()})

    print("=== Part 10: ranking comparison across lambda ===")
    q_list = sorted(set(r["q"] for r in rows))
    T_list = sorted(set(r["T"] for r in rows))
    lam_list = sorted(set(r["lam"] for r in rows))

    ranking_rows = []
    for q in q_list:
        for T in T_list:
            for lam in lam_list:
                cell = {r["k"]: r for r in rows if r["q"] == q and r["T"] == T and r["lam"] == lam
                        and r["k"] in EXTERNAL_NODES}
                if len(cell) < len(EXTERNAL_NODES):
                    continue
                # rank by weighted objective J_lambda = E + lambda * 2D  (since D already has the 1/2,
                # and the optimization objective per the spec is 1/2 int[u'u + lambda m'Qperp m] =
                # (1/2)E + lambda*D  when E is defined as int u'u -- so weighted cost = E/2 + lambda*D... )
                # We report both the pure-E ranking (lambda=0 equivalent) and the actual J_lambda ranking.
                best_E = min(cell, key=lambda k: cell[k]["E"])
                best_D = min(cell, key=lambda k: cell[k]["D"])
                best_J = min(cell, key=lambda k: 0.5 * cell[k]["E"] + lam * cell[k]["D"])
                ranking_rows.append(dict(q=q, T=T, lam=lam, best_E_node=best_E, best_D_node=best_D,
                                           best_J_node=best_J,
                                           E_rank=",".join(str(k) for k in sorted(cell, key=lambda k: cell[k]["E"])),
                                           J_rank=",".join(str(k) for k in sorted(cell, key=lambda k: 0.5*cell[k]["E"]+lam*cell[k]["D"]))))

    with open(os.path.join(DATADIR, "part10_ranking_comparison.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ranking_rows[0].keys()))
        w.writeheader(); w.writerows(ranking_rows)

    # Report: does best_J_node change from best_E_node (lambda=0 winner) as lambda grows?
    print("Fraction of (q,T,lambda) cells where organization-aware winner differs from pure-energy winner:")
    for q in q_list:
        for T in T_list:
            sub = [r for r in ranking_rows if r["q"] == q and r["T"] == T]
            sub_sorted = sorted(sub, key=lambda r: r["lam"])
            base_winner = sub_sorted[0]["best_E_node"]  # lambda=0 (or smallest lambda) winner
            n_changed = sum(1 for r in sub_sorted if r["best_J_node"] != base_winner)
            switch_lams = [r["lam"] for r in sub_sorted if r["best_J_node"] != base_winner]
            if n_changed > 0:
                first_switch = min(switch_lams)
                print(f"  q={q:<5} T={T:<4} lambda=0 winner={base_winner}  switches at {n_changed}/{len(sub_sorted)} "
                      f"lambda values, first switch at lambda={first_switch:.4g}, new winner(s)={sorted(set(r['best_J_node'] for r in sub_sorted if r['lam']==first_switch))}")
            else:
                print(f"  q={q:<5} T={T:<4} lambda=0 winner={base_winner}  NEVER switches across tested lambda")

    # specific comparison: nodes 4, 5, 6
    print("\nSpecific node 4 vs 5 vs 6 comparison at q=1, T=1 across lambda:")
    sub = sorted([r for r in ranking_rows if r["q"] == 1.0 and r["T"] == 1.0], key=lambda r: r["lam"])
    for r in sub[::5]:
        print(f"  lambda={r['lam']:<10.4g} best_E={r['best_E_node']}  best_J={r['best_J_node']}  full E-rank={r['E_rank']}")

    print("\n=== Part 11: terminal-distortion diagnostic ===")
    diag_rows = []
    for r in rows:
        if r["k"] not in EXTERNAL_NODES:
            continue
        ratio_DT = r["D_T"] / r["D_max"] if r["D_max"] > 0 else np.nan
        diag_rows.append(dict(k=r["k"], q=r["q"], T=r["T"], lam=r["lam"], D=r["D"], D_T=r["D_T"],
                                D_max=r["D_max"], ratio_DT_over_Dmax=ratio_DT))
    # flag cases where D_T is close to D_max (terminal distortion dominates) at moderate/high lambda
    flagged = [r for r in diag_rows if r["lam"] > 1.0 and r["ratio_DT_over_Dmax"] > 0.8]
    print(f"Cases with lambda>1 and D_T/D_max > 0.8 (terminal distortion dominates the path max): {len(flagged)} / {len(diag_rows)}")
    for r in flagged[:10]:
        print(" ", r)
    with open(os.path.join(DATADIR, "part11_terminal_distortion.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(diag_rows[0].keys()))
        w.writeheader(); w.writerows(diag_rows)
    print("Saved terminal-distortion diagnostic table.")
    if flagged:
        print("\nFLAG: some high-lambda solutions concentrate distortion near the terminal time.")
        print("Per instructions, this is REPORTED as a finding, not addressed with a new terminal penalty.")
    else:
        print("\nNo systematic terminal-distortion concentration found at the tested lambda values.")
