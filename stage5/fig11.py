"""Figure 11: Finite-data pathwise integrity classification accuracy vs. sample size.

At the primary delta=0.01 this dynamical system (tau_x=tau_z=1) never produces a
genuine pathwise violation for any ramp duration tested in Section 9 (max transient
leakage ~4e-5, see fig3) -- so there is no "truly violated" class to classify against
at delta=0.01. To get a meaningful two-class problem for this diagnostic we use a much
tighter delta_fig11=1e-5 (documented explicitly here, NOT used anywhere else in Stage 5)
that Section 9's own fine-duration sweep shows is exceeded by fast ramps (T_ramp<=0.25)
and respected by slow ramps (T_ramp>=4). This choice is purely to construct a
classification benchmark; it does not alter the delta=0.01 primary results elsewhere.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs
import integrity as I
import finite_data as fd
import rate_induced as ri

DELTA_FIG11 = 1e-5
T_VIOLATED = [0.1, 0.15, 0.2, 0.25]
T_INTACT = [4, 8]
N_PATHS_LIST = [50, 200, 1000]
N_REALIZATIONS = 40  # matches finite_data.py --scale full's n_outer, for consistency
N_CHECK = 20
N_BOOT = 500


def protocol_functions(T_ramp):
    res = ri.slow_ramp_run(T_ramp, n_eval=400)
    t = res["t"]
    y_arr, z_arr = res["y"], res["z"]
    y_of_t = lambda tt: float(np.interp(tt, t, y_arr))
    z_of_t = lambda tt: float(np.interp(tt, t, z_arr))
    return y_of_t, z_of_t, T_ramp


def truth_label(T_ramp, delta):
    res = ri.run_ramp(T_ramp, n_eval=200)
    return bool(res["L3"].max() > delta)


def classify_one_realization(y_of_t, z_of_t, T_ramp, n_paths, rng, delta):
    ens = fd.simulate_sde_ensemble(y_of_t, z_of_t, T_ramp, n_paths, n_steps=max(100, N_CHECK * 5), rng=rng)
    idx = np.linspace(0, len(ens["t"]) - 1, N_CHECK).astype(int)
    half = n_paths // 2
    if half < 8:
        return None  # too few samples to split meaningfully
    sel, val = np.arange(half), np.arange(half, n_paths)
    B_by_t = []
    X_val_by_t = []
    for i in idx:
        winners, _, _ = fd.select_boundary_from_sample(ens["X"][i][sel])
        B_by_t.append(winners[0])
        X_val_by_t.append(ens["X"][i][val])
    band = fd.trajectory_bootstrap_band(X_val_by_t, B_by_t, n_boot=N_BOOT, rng=rng, alpha=0.05)
    classified_violated = bool(np.any(band["U_band"] > delta))
    return classified_violated


if __name__ == "__main__":
    rows = []
    for T_ramp in T_VIOLATED + T_INTACT:
        truth = truth_label(T_ramp, DELTA_FIG11)
        y_of_t, z_of_t, _ = protocol_functions(T_ramp)
        for n_paths in N_PATHS_LIST:
            n_correct = 0
            n_valid = 0
            for r in range(N_REALIZATIONS):
                rng = np.random.default_rng(5000 + hash((T_ramp, n_paths, r)) % 100000)
                cv = classify_one_realization(y_of_t, z_of_t, T_ramp, n_paths, rng, DELTA_FIG11)
                if cv is None:
                    continue
                n_valid += 1
                if cv == truth:
                    n_correct += 1
            acc = n_correct / n_valid if n_valid else np.nan
            rows.append(dict(T_ramp=T_ramp, truth_violated=truth, n_paths=n_paths,
                              accuracy=acc, n_valid=n_valid))
            print(f"T_ramp={T_ramp:<6} truth_violated={truth}  n_paths={n_paths:<5} "
                  f"accuracy={acc:.2f} ({n_correct}/{n_valid})")

    # aggregate: false-failure rate (classified violated | truly intact),
    # false-preservation rate (classified intact | truly violated), by n_paths
    agg = {n: dict(fpr=[], fnr=[]) for n in N_PATHS_LIST}  # fpr: false "violated" alarms on intact truth
    for n_paths in N_PATHS_LIST:
        intact_rows = [r for r in rows if not r["truth_violated"] and r["n_paths"] == n_paths]
        viol_rows = [r for r in rows if r["truth_violated"] and r["n_paths"] == n_paths]
        agg[n_paths]["false_failure_rate"] = 1 - np.mean([r["accuracy"] for r in intact_rows])
        agg[n_paths]["false_preservation_rate"] = 1 - np.mean([r["accuracy"] for r in viol_rows])

    fig, ax = plt.subplots(1, 1, figsize=(7, 5))
    ffr = [agg[n]["false_failure_rate"] for n in N_PATHS_LIST]
    fpr = [agg[n]["false_preservation_rate"] for n in N_PATHS_LIST]
    ax.plot(N_PATHS_LIST, ffr, "-o", color=fs.COLOR_ACCENT,
            label="false-failure rate\n(intact truth called 'violated')")
    ax.plot(N_PATHS_LIST, fpr, "-o", color=fs.COLOR_INTERIOR,
            label="false-preservation rate\n(violated truth called 'intact')")
    ax.set_xscale("log")
    ax.set_xlabel("ensemble size (n_paths)")
    ax.set_ylabel("misclassification rate")
    ax.set_ylim(-0.05, 1.05)
    ax.set_title(f"Simultaneous-band pathwise classification error vs. sample size\n"
                 f"(delta_fig11={DELTA_FIG11:.0e}, {N_REALIZATIONS} realizations/cell, "
                 f"true classes: T_ramp in {T_VIOLATED} vs {T_INTACT})", fontsize=9.5)
    ax.legend(fontsize=8.5)
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig11_classification")
    fs.save_all(fig, outpath)
    plt.close(fig)

    import csv
    with open(os.path.join(os.path.dirname(__file__), "data", "fig11_classification.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("Saved", outpath)
