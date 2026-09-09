"""L2 oracle characterization (task brief section 4).

EVALUATION-SIDE. Records the full time-dependent oracle FOV graph and the true
dynamic causal interface B_t^D for a fixed reference interior, and measures
|B_t^D|, |B_{t+1}^D triangle B_t^D|, interface lifetime and turnover, plus
global FOV edge churn. This is VALIDATION DATA ONLY: it runs before any
inference module is applied to real data, and no inference module can import
it.

Also produces the same statistics for L0 (all edges always live) as the
reference against which "the interface is now genuinely time-varying" is
judged, and for L3 once its gate parameters are chosen.
"""
from __future__ import annotations

import numpy as np

from common_68 import ModelParams, Lattice, dump_json, load_json, DATA_DIR, RHO, OMEGA, jaccard
from fov_dynamics import FovSimulator, GateParams
from oracle_68 import interface_series, edge_turnover

T_START, T_END = 40, 100          # measurement window (post burn-in)
REF_RADIUS = 2.5                  # radius of the fixed reference interior


def reference_interior(sim, center_bird: int, radius: float = REF_RADIUS) -> np.ndarray:
    """A fixed, geometry-defined disc of birds. Used ONLY as an oracle probe of
    how the true interface moves; it is not a detected candidate and is never
    handed to inference code as a starting interior."""
    P = sim.positions
    d = np.sqrt(((P - P[center_bird]) ** 2).sum(axis=1))
    return np.array(sorted(np.where(d <= radius)[0].tolist()), dtype=int)


def characterize(sim, seed: int, gate_params=None, label: str = "L2") -> dict:
    res = sim.run(nt=T_END + 1, seed=seed, gate_params=gate_params, record_oracle=True)
    L = int(round(sim.nn ** 0.5))
    center = (L // 2) * L + (L // 2)
    I = reference_interior(sim, center)
    I_series = {t: I for t in range(T_START, T_END + 1)}
    iface = interface_series(sim, res.active_mask_hist, I_series)
    churn = edge_turnover(res.active_mask_hist[T_START:T_END + 1])
    ts = iface["t"]
    tb = {}
    for a, b in zip(ts[:-1], ts[1:]):
        A, B = set(iface["B"][a]), set(iface["B"][b])
        tb[b] = len(A ^ B)
    return dict(
        label=label, seed=seed, interior=I.tolist(), interior_size=len(I),
        mean_B_size=iface["mean_size"], mean_symdiff=iface["mean_symdiff"],
        mean_B_turnover=iface["mean_turnover"], mean_node_lifetime=iface["mean_node_lifetime"],
        B_series={int(k): v for k, v in iface["B"].items()},
        size_series={int(k): v for k, v in iface["size"].items()},
        symdiff_series={int(k): v for k, v in iface["symdiff"].items()},
        edge_churn=churn,
        n_distinct_interfaces=len({tuple(v) for v in iface["B"].values()}),
        n_timepoints=len(ts),
    )


class _AlwaysLive(FovSimulator):
    """L0 reference: every geometric Moore edge is always live."""
    def visible_mask(self, z):
        return np.ones(self.n_edges, dtype=bool)


def main():
    screen = load_json(DATA_DIR / "episode_screen.json")
    op = screen["ops"]["OP1"]
    nn, beta, s = op["nn"], op["beta"], op["s"]
    seeds = (op["dev_seeds"] + op["heldout_seeds"])[:6]
    lattice = Lattice(nn=nn, nh=8)
    params = ModelParams(beta=beta, precB=s * RHO, precC=s * OMEGA)

    out = dict(protocol="stage6_8 oracle interface characterization",
               operating_point=dict(nn=nn, beta=beta, s=s, rho=s * RHO, omega=s * OMEGA),
               t_start=T_START, t_end=T_END, seeds=seeds, runs=[])

    sim_l2 = FovSimulator(params, lattice)
    sim_l0 = _AlwaysLive(params, lattice)
    for seed in seeds:
        for label, sim in (("L0_fixed_graph", sim_l0), ("L2_fov", sim_l2)):
            r = characterize(sim, seed, label=label)
            out["runs"].append(r)
            print(f"seed {seed:<4} {label:<16} |B|={r['mean_B_size']:6.2f} "
                  f"symdiff={r['mean_symdiff']:6.2f} turnover={r['mean_B_turnover']:.3f} "
                  f"node_life={r['mean_node_lifetime']:6.2f} "
                  f"edge_flip={r['edge_churn']['mean_edge_flip_fraction']:.4f} "
                  f"live={r['edge_churn']['mean_live_fraction']:.3f} "
                  f"distinct={r['n_distinct_interfaces']}/{r['n_timepoints']}", flush=True)
    dump_json(out, DATA_DIR / "oracle_interface.json")
    print("wrote", DATA_DIR / "oracle_interface.json")


if __name__ == "__main__":
    main()
