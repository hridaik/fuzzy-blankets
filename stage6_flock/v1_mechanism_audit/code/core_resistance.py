"""Part F: direct-core resistance curve. Mechanistic diagnostic only (forcing
INTERIOR birds is inadmissible for the actual task) -- characterizes the
intrinsic stability/threshold structure of the established flock.
"""
from __future__ import annotations

import numpy as np

from common import ROOT, AUDIT_DIR, load_canonical, dump_json, T_U, T_R, BASE_SEED_OFFSET, N_DEV, TW
from flock_sim.simulation import run_simulation
from flock_sim.interventions import make_pulse
from flock_sim.metrics import target_heading_fraction, coherence
from flock_sim.lattice import bird_to_rowcol

K_VALUES = [1, 2, 4, 8, 12, 16, 20]


def internal_degree(lattice, I0):
    """Predeclared selection rule: rank I0 members by their number of Moore
    neighbors that are ALSO in I0 (internal interaction degree), descending."""
    I0_set = set(I0.tolist())
    deg = []
    for i in I0.tolist():
        d = sum(1 for j in lattice.neighbor_ids[i].tolist() if j in I0_set)
        deg.append(d)
    order = np.argsort(-np.array(deg))
    return I0[order], np.array(deg)[order]


def evaluate(actuators, z_t0, I0, h_star, lattice, n_replicates=N_DEV):
    Hstar_end = np.zeros(n_replicates)
    Hstar_release = np.zeros(n_replicates)
    for r in range(n_replicates):
        seed = BASE_SEED_OFFSET + r
        interventions = make_pulse(actuators, h_star, t0=0, t_u=T_U) if len(actuators) else None
        res = run_simulation(nn=100, nt=T_U + T_R, seed=seed, init_z=z_t0,
                              interventions=interventions, lattice=lattice)
        Hstar_end[r] = target_heading_fraction(res.z_hist[T_U], I0, h_star)
        Hstar_release[r] = target_heading_fraction(res.z_hist[T_U + T_R], I0, h_star)
    return float(Hstar_end.mean()), float(Hstar_release.mean())


def main():
    c = load_canonical()
    lattice, I0, z_t0, h_star = c["lattice"], c["I0"], c["z_t0"], c["h_star"]
    ranked_by_degree, degrees = internal_degree(lattice, I0)
    print("I0 ranked by internal degree:", list(zip(ranked_by_degree.tolist(), degrees.tolist())))

    rows = []
    rng = np.random.default_rng(12345)
    for k in K_VALUES:
        deg_subset = ranked_by_degree[:k]
        mean_end_deg, mean_rel_deg = evaluate(deg_subset, z_t0, I0, h_star, lattice)

        # random subset, averaged over 5 random draws for a less selection-biased estimate
        rand_ends, rand_rels = [], []
        for _ in range(5):
            rand_subset = rng.choice(I0, size=k, replace=False)
            e, rl = evaluate(rand_subset, z_t0, I0, h_star, lattice, n_replicates=20)
            rand_ends.append(e)
            rand_rels.append(rl)

        rows.append(dict(
            k=k, actuators_by_degree=deg_subset.tolist(),
            mean_Hstar_end_by_degree=mean_end_deg, mean_Hstar_release_by_degree=mean_rel_deg,
            mean_Hstar_end_random=float(np.mean(rand_ends)), mean_Hstar_release_random=float(np.mean(rand_rels)),
            std_Hstar_end_random=float(np.std(rand_ends)),
        ))
        print(f"k={k:2d}: by-degree mean_Hstar_end={mean_end_deg:.3f} release={mean_rel_deg:.3f} | "
              f"random mean_Hstar_end={np.mean(rand_ends):.3f}+/-{np.std(rand_ends):.3f}")

    out = dict(K_VALUES=K_VALUES, n_replicates=N_DEV, rows=rows,
               interpretation_note=(
                   "Diagnostic only; forcing I0 members is inadmissible for the actual "
                   "external-only steering task. Used solely to characterize whether the "
                   "established core exhibits a sharp cascade threshold or a gradual/"
                   "sublinear response to internal forcing, which bears on whether sparse "
                   "EXTERIOR actuation is fighting an intrinsically bistable/absorbing "
                   "consensus."))
    dump_json(out, AUDIT_DIR / "data" / "core_resistance.json")


if __name__ == "__main__":
    main()
