"""Part G: parameter-regime ambiguity audit. Two explicitly named regimes:
  - code_default:       beta=1, precB(rho)=15, precC(omega)=3  (what actually produced protocol_v1)
  - manuscript_all_ones: beta=1, precB(rho)=1,  precC(omega)=1  (what the paper's text claims)
No tuning in search of a "nicer" result -- both regimes are run once, predeclared,
and reported side by side. See METHODS_AUDIT.md section 13 discrepancy #1 for the
source of this ambiguity.
"""
from __future__ import annotations

import numpy as np

from common import ROOT, AUDIT_DIR, load_canonical, dump_json, T_U, T_R, BASE_SEED_OFFSET, N_DEV
from flock_sim.model import ModelParams
from flock_sim.simulation import run_simulation
from flock_sim.interventions import make_pulse
from flock_sim.metrics import target_heading_fraction, coherence, polarization
from analysis.baseline_characterization import find_qualifying_t0

REGIMES = {
    "code_default": ModelParams(beta=1.0, precB=15.0, precC=3.0),
    "manuscript_all_ones": ModelParams(beta=1.0, precB=1.0, precC=1.0),
}
N_BASELINE_SEEDS = 50
N_SENSITIVITY_REPS = 20


def from_scratch_baseline(params, n_seeds):
    n_qualify = 0
    phi_at_30 = []
    for seed in range(n_seeds):
        res = run_simulation(nn=100, nt=60, seed=seed, params=params)
        phi_at_30.append(polarization(res.z_hist[30]))
        q = find_qualifying_t0(res.z_hist)
        if q is not None:
            n_qualify += 1
    return dict(n_seeds=n_seeds, qualification_rate=n_qualify / n_seeds,
                mean_phi_at_t30=float(np.mean(phi_at_30)))


def ceteris_paribus_on_canonical(params, z_t0, I0, h_star, lattice, B_D0, non_core):
    # uncontrolled
    Hstar_uncontrolled = np.zeros(N_SENSITIVITY_REPS)
    for r in range(N_SENSITIVITY_REPS):
        res = run_simulation(nn=100, nt=T_U, seed=BASE_SEED_OFFSET + r, init_z=z_t0,
                              params=params, lattice=lattice)
        Hstar_uncontrolled[r] = target_heading_fraction(res.z_hist[T_U], I0, h_star)

    def arm(actuators):
        Hstar_end = np.zeros(N_SENSITIVITY_REPS)
        for r in range(N_SENSITIVITY_REPS):
            interventions = make_pulse(actuators, h_star, t0=0, t_u=T_U) if len(actuators) else None
            res = run_simulation(nn=100, nt=T_U, seed=BASE_SEED_OFFSET + r, init_z=z_t0,
                                  interventions=interventions, params=params, lattice=lattice)
            Hstar_end[r] = target_heading_fraction(res.z_hist[T_U], I0, h_star)
        return float(Hstar_end.mean()), float((Hstar_end >= 0.8).mean())

    bd0_mean, bd0_p = arm(B_D0)
    allnc_mean, allnc_p = arm(non_core)

    # resistance curve (by-degree only, for speed)
    from core_resistance import internal_degree
    ranked, _ = internal_degree(lattice, I0)
    resistance = {}
    for k in (1, 4, 12, 20):
        m, p = arm(ranked[:k])
        resistance[k] = dict(mean_Hstar_end=m, p_success=p)

    return dict(
        mean_Hstar_uncontrolled=float(Hstar_uncontrolled.mean()),
        B_D0_mean_Hstar_end=bd0_mean, B_D0_p_success=bd0_p,
        all_non_core_mean_Hstar_end=allnc_mean, all_non_core_p_success=allnc_p,
        resistance_by_degree=resistance,
    )


def main():
    c = load_canonical()
    lattice, I0, z_t0, h_star = c["lattice"], c["I0"], c["z_t0"], c["h_star"]
    import json
    ds = json.load(open(AUDIT_DIR / "data" / "dynamical_shell.json"))
    B_D0 = np.array(ds["B_D0"])
    non_core = np.setdiff1d(np.arange(100), I0)

    out = {}
    for name, params in REGIMES.items():
        print(f"=== regime: {name} (beta={params.beta}, precB={params.precB}, precC={params.precC}) ===")
        base = from_scratch_baseline(params, N_BASELINE_SEEDS)
        print("  from-scratch baseline:", base)
        cp = ceteris_paribus_on_canonical(params, z_t0, I0, h_star, lattice, B_D0, non_core)
        print("  ceteris-paribus-on-canonical-IC:", cp)
        out[name] = dict(params=dict(beta=params.beta, precB=params.precB, precC=params.precC),
                          from_scratch_baseline=base, ceteris_paribus_on_canonical=cp)

    dump_json(out, AUDIT_DIR / "data" / "parameter_sensitivity.json")

    # qualitative-difference flag (not a claim about which is "correct")
    q_default = out["code_default"]["from_scratch_baseline"]["qualification_rate"]
    q_manuscript = out["manuscript_all_ones"]["from_scratch_baseline"]["qualification_rate"]
    bd_default = out["code_default"]["ceteris_paribus_on_canonical"]["B_D0_p_success"]
    bd_manuscript = out["manuscript_all_ones"]["ceteris_paribus_on_canonical"]["B_D0_p_success"]
    print(f"\nQualification rate: code_default={q_default:.2f} manuscript_all_ones={q_manuscript:.2f}")
    print(f"B_D0 control p_success: code_default={bd_default:.2f} manuscript_all_ones={bd_manuscript:.2f}")


if __name__ == "__main__":
    main()
