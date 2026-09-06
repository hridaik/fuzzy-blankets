"""Figure 12 (final-patch Part 3): pathwise constraint activation.
Only generated if stress_test.py found an activated case (see data/stress_test_decision.json).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
import figstyle as fs

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

if __name__ == "__main__":
    with open(os.path.join(DATA_DIR, "stress_test_decision.json")) as f:
        decision = json.load(f)["case"]
    if decision is None:
        print("No activated case was found by stress_test.py (neither the tau_z sweep nor the "
              "stringent unit-test thresholds activated the pathwise constraint) -- per the spec, "
              "Figure 12 is NOT generated in this situation. Nothing to do.")
        sys.exit(0)

    with open(os.path.join(DATA_DIR, "stress_test_results.json")) as f:
        results = json.load(f)

    kind, tau_z, delta_used = decision
    if kind == "3a":
        entry = results[f"3a_compare_tauz{tau_z}"]
        A, C = entry["A"], entry["C"]
        is_unit_test = False
        title_case = f"tau_z={tau_z} (physically interpretable interface-timescale stress test)"
    else:
        entry = results["3b_unit"][str(delta_used)]
        A = entry["A"]
        C = entry.get("C") or entry.get("C_T4")
        is_unit_test = True
        title_case = f"delta_unit={delta_used:.0e} (stringent unit-test threshold)"

    if not (isinstance(C, dict) and C.get("ok")):
        print(f"Activated case found (kind={kind}) but formulation C was reported INFEASIBLE by the "
              f"multi-start optimizer -- this itself demonstrates the constraint is active/respected "
              f"(outcome 2 in the spec's acceptable-outcomes list). No trajectory to plot for C; "
              f"generating Panel A (Lambda_3 comparison) only, with a text note.")
        C = None

    fig = plt.figure(figsize=(13, 9.5))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    tA = np.array(A["t"]); L3A = np.array(A["L3"])
    ax_a.plot(tA, L3A, color=fs.COLOR_EXTERIOR, lw=2, label="A: task-only")
    if C is not None:
        tC = np.array(C["t"]); L3C = np.array(C["L3"])
        ax_a.plot(tC, L3C, color=fs.COLOR_ACCENT, lw=2, label="C: pathwise-integrity")
    delta_line = delta_used if is_unit_test else 0.01
    ax_a.axhline(delta_line, color="gray", ls=":", lw=1.2, label=f"delta={delta_line:.0e}")
    ax_a.set_xlabel("t"); ax_a.set_ylabel(r"$\Lambda_3(t)$")
    ax_a.set_title("Panel A: pathwise leakage, task-only vs. pathwise-integrity")
    ax_a.legend(fontsize=8)

    yA, zA, YA = np.array(A["y"]), np.array(A["z"]), np.array(A["Y"])
    ax_b.plot(tA, yA, color=fs.COLOR_INTERIOR, label="y (A)")
    ax_b.plot(tA, zA, color=fs.COLOR_BOUNDARY, label="z (A)")
    ax_b.plot(tA, YA, color=fs.COLOR_EXTERIOR, label="Y=c^Tm (A)")
    if C is not None:
        ax_b.plot(tC, np.array(C["y"]), color=fs.COLOR_INTERIOR, ls="--", label="y (C)")
        ax_b.plot(tC, np.array(C["z"]), color=fs.COLOR_BOUNDARY, ls="--", label="z (C)")
        ax_b.plot(tC, np.array(C["Y"]), color=fs.COLOR_EXTERIOR, ls="--", label="Y (C)")
    ax_b.set_xlabel("t"); ax_b.set_title("Panel B: state trajectories (solid=A, dashed=C)")
    ax_b.legend(fontsize=7, ncol=2)

    knots_t_A = np.linspace(0, A.get("T", 2.0) if "T" in A else 2.0, len(A["uy"]))
    ax_c.step(np.linspace(0, tA[-1], len(A["uy"])), A["uy"], where="post", color=fs.COLOR_INTERIOR,
              label=f"u_y (A), E={A['E_total']:.2f}")
    if A["uz"] is not None:
        ax_c.step(np.linspace(0, tA[-1], len(A["uz"])), A["uz"], where="post", color=fs.COLOR_BOUNDARY,
                  label="u_z (A)")
    if C is not None:
        ax_c.step(np.linspace(0, tC[-1], len(C["uy"])), C["uy"], where="post", color=fs.COLOR_INTERIOR,
                  ls="--", label=f"u_y (C), E={C['E_total']:.2f}")
        if C["uz"] is not None:
            ax_c.step(np.linspace(0, tC[-1], len(C["uz"])), C["uz"], where="post", color=fs.COLOR_BOUNDARY,
                      ls="--", label="u_z (C)")
    ax_c.set_xlabel("t"); ax_c.set_title("Panel C: controls (energies annotated)")
    ax_c.legend(fontsize=7)

    DorgA = np.array(A["Dorg"])
    ax_d.plot(tA, DorgA, color=fs.COLOR_EXTERIOR, lw=2, label=f"A, AUC={A['A_org_ctrl']:.4f}")
    if C is not None:
        DorgC = np.array(C["Dorg"])
        ax_d.plot(tC, DorgC, color=fs.COLOR_ACCENT, lw=2, label=f"C, AUC={C['A_org_ctrl']:.4f}")
    ax_d.set_xlabel("t"); ax_d.set_ylabel(r"$D_{\rm org}(t)$")
    ax_d.set_title("Panel D: organizational departure")
    ax_d.legend(fontsize=8)

    if is_unit_test:
        supertitle = ("Constraint-activation unit test using a deliberately stringent tolerance; "
                       "this is NOT the primary Stage-5 biological/identity threshold.")
    else:
        supertitle = (f"Pathwise constraint activation via interface-timescale stress test "
                       f"({title_case}); primary delta=0.01 threshold, physically interpretable "
                       f"tau_z, NOT a unit-test artifact.")
    fig.suptitle(supertitle, fontsize=11, y=1.01)
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), "figures", "fig12_constraint_activation")
    fs.save_all(fig, outpath)
    plt.close(fig)
    print("Saved", outpath)
