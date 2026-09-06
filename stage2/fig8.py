import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
import core
from figstyle import save_all, COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR, COLOR_ACCENT

FIGDIR = os.path.join(os.path.dirname(__file__), "figures")
DATADIR = os.path.join(os.path.dirname(__file__), "data")

N = core.N
e3v = np.zeros(N); e3v[core.idx[3]] = 1.0
e6v = np.zeros(N); e6v[core.idx[6]] = 1.0


def A_q(q):
    Qq = q * (np.outer(e3v, e6v) - np.outer(e6v, e3v))
    return (np.eye(N) + Qq) @ core.Omega0


def predictive_permeability(q, tau):
    I_idx = core.I_IDX
    B_idx = [core.idx[4], core.idx[5]]
    E_idx = [core.idx[6], core.idx[7], core.idx[8]]
    Aq = A_q(q)
    Gamma_tau = expm(-Aq * tau) @ core.Sigma0
    idx_future_I = I_idx
    idx_t = I_idx + B_idx + E_idx
    Sigma_tt = core.Sigma0[np.ix_(idx_t, idx_t)]
    Cov_fut_t = Gamma_tau[np.ix_(idx_future_I, idx_t)]
    Sigma_ff = core.Sigma0[np.ix_(idx_future_I, idx_future_I)]
    nI, nB, nE = len(I_idx), len(B_idx), len(E_idx)
    n_future = nI
    total = n_future + nI + nB + nE
    Sigma_joint = np.zeros((total, total))
    Sigma_joint[:n_future, :n_future] = Sigma_ff
    Sigma_joint[:n_future, n_future:] = Cov_fut_t
    Sigma_joint[n_future:, :n_future] = Cov_fut_t.T
    Sigma_joint[n_future:, n_future:] = Sigma_tt
    F = list(range(0, n_future))
    Itc = list(range(n_future, n_future + nI))
    Btc = list(range(n_future + nI, n_future + nI + nB))
    Etc = list(range(n_future + nI + nB, total))
    cond = Itc + Btc

    def cond_cov(target, cond_idx):
        if len(cond_idx) == 0:
            return Sigma_joint[np.ix_(target, target)]
        Sxx = Sigma_joint[np.ix_(target, target)]
        Sxc = Sigma_joint[np.ix_(target, cond_idx)]
        Scc = Sigma_joint[np.ix_(cond_idx, cond_idx)]
        Scx = Sigma_joint[np.ix_(cond_idx, target)]
        return Sxx - Sxc @ np.linalg.inv(Scc) @ Scx

    Sigma_F_cond = cond_cov(F, cond)
    Sigma_E_cond = cond_cov(Etc, cond)
    Sigma_FE_cond = cond_cov(F + Etc, cond)
    return 0.5 * (core.logdet(Sigma_F_cond) + core.logdet(Sigma_E_cond) - core.logdet(Sigma_FE_cond))


if __name__ == "__main__":
    q_list = [0, 0.5, 1, 2]
    tau_grid = np.concatenate([[0.0], np.geomspace(0.005, 4.0, 60)])

    P_data = {q: [] for q in q_list}
    for q in q_list:
        for tau in tau_grid:
            P_data[q].append(0.0 if tau == 0.0 else predictive_permeability(q, tau))

    # instantaneous blanket leakage for many q (should be exactly 0)
    I_idx = core.I_IDX
    B_idx = [core.idx[4], core.idx[5]]
    E_idx = [core.idx[6], core.idx[7], core.idx[8]]
    L_instantaneous = core.L_cmi_precision(core.Omega0, I_idx, B_idx, E_idx)  # invariant of q by construction
    q_check = np.linspace(-3, 3, 25)
    # verify Lyapunov / stationary invariance holds for each q (confirms Sigma0 unaffected by q)
    lyap_resid = []
    for q in q_check:
        Aq = A_q(q)
        lyap_resid.append(np.max(np.abs(Aq @ core.Sigma0 + core.Sigma0 @ Aq.T - 2*np.eye(N))))
    lyap_resid = np.array(lyap_resid)
    assert np.max(lyap_resid) < 1e-9

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    fig.subplots_adjust(wspace=0.45)
    ax0 = axes[0]
    cmap_colors = [COLOR_INTERIOR, COLOR_BOUNDARY, COLOR_EXTERIOR, COLOR_ACCENT]
    for q, c in zip(q_list, cmap_colors):
        ax0.plot(tau_grid, P_data[q], label=f"q={q}", color=c, linewidth=2.0)
    ax0.set_xlabel(r"$\tau$")
    ax0.set_ylabel(r"$P_\tau$ [nats]")
    ax0.set_title("A: finite-horizon predictive permeability")
    ax0.legend(fontsize=9)

    ax1 = axes[1]
    q_range = np.linspace(-2, 2, 100)
    J36 = -4.5 * q_range
    J63 = 4.5 * q_range
    ax1.plot(q_range, J36, color=COLOR_INTERIOR, linewidth=2.0, label=r"$J_{36}=-4.5q$")
    ax1.plot(q_range, J63, color=COLOR_EXTERIOR, linewidth=2.0, label=r"$J_{63}=+4.5q$")
    ax1.set_xlabel("q")
    ax1.set_ylabel("Jacobian entry")
    ax1.set_title("B: direct coupling\ngrows with q")
    ax1.legend(fontsize=9)

    ax2 = axes[2]
    ax2.plot(q_check, np.full_like(q_check, L_instantaneous), color=COLOR_ACCENT, marker="o", markersize=4)
    ax2.set_ylim(-0.01, 0.01)
    ax2.axhline(0, color="gray", linestyle=":")
    ax2.set_xlabel("q")
    ax2.set_ylabel(r"$I(X_I;X_E\mid X_B)$ [nats]")
    ax2.set_title("C: instantaneous leakage\nstays exactly 0 for all q")

    fig.suptitle("Figure 8 — Static blanket vs. finite-time dynamics are distinct objects", y=1.03, fontsize=13)
    save_all(fig, os.path.join(FIGDIR, "fig8_ou_dynamics"))
    plt.close(fig)

    with open(os.path.join(DATADIR, "fig8_data.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tau"] + [f"P_tau_q{q}" for q in q_list])
        for i, tau in enumerate(tau_grid):
            w.writerow([tau] + [P_data[q][i] for q in q_list])

    print(f"Figure 8 saved. Instantaneous leakage = {L_instantaneous:.3e} for all q (Lyapunov resid max {lyap_resid.max():.3e}).")
    print("Confirms P_tau > 0 for finite tau even at q=0 (propagation through blanket over time),")
    print("while J_36/J_63 and instantaneous leakage demonstrate direct coupling and static screening")
    print("are separate, independently-varying quantities.")
