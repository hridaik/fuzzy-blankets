"""Part H: statistical/predictive screening validation.

H1 (structural, derived from source -- see README.md): because
`active_inference.compute_G` for bird i sums independent per-neighbor
contributions over EXACTLY `lattice.neighbor_ids[i]` (no other channel touches
G, the policy posterior, or the sampled next heading for i), and because the
per-bird action/next-state RNG draws are conditionally independent across
birds given the full current state (each row of `sample_categorical_rows`
consumes its own independent uniform draw), the model's computational graph
implies EXACTLY:

    X_{I0,t+1} _||_ X_{E^D_0,t} | X_{I0,t}, X_{B^D_0,t}

i.e. a genuine structural one-step Markov/screening property with B = B^D_0
(by construction: B^D_0 contains every neighbor of every bird in I0, so
conditioning on X_{I0,t} union X_{B^D_0,t} already pins down every input any
compute_G(i in I0) can read). This is verified empirically below (H2) as a
sanity check (excess log-loss ~ 0), not as the primary evidence for the claim
-- the primary evidence is the code inspection itself, cited in README.md.

H2 (empirical, approximate): does B^F_0 (2 birds) screen X_{I0,t+1} as well as
B^D_0 (12 birds)? We compare per-bird one-step-ahead predictive log-loss under
three conditioning sets:
  - M_full: exact predictive distribution from active_inference given the
    FULL realized z_t (gold standard -- for this model this is provably
    identical to conditioning on just bird i's own neighbors).
  - M_BD:   conditioning on X_{I0,t} union X_{B^D_0,t} only. Because B^D_0
            contains every neighbor of every I0 bird, this is architecturally
            IDENTICAL to M_full (verified by assertion below, not assumed).
  - M_BF:   conditioning on X_{I0,t} union X_{B^F_0,t} only; any neighbor of
            an I0 bird that lies OUTSIDE I0 union B^F_0 is unknown and is
            marginalized by Monte-Carlo draws from its empirical marginal
            heading distribution at that timestep (a mean-field / factorized
            approximation across unknown neighbors -- NOT exact CMI, since
            compute_G's softmax nonlinearity means E[softmax(G)] != softmax(E[G]);
            explicitly flagged as approximate, per the task brief's guidance
            to avoid an intractable full joint CMI estimate).
"""
from __future__ import annotations

import json
import numpy as np

from common import ROOT, AUDIT_DIR, load_canonical, dump_json, T_U, TW
from flock_sim.active_inference import build_model, compute_G, policy_posterior
from flock_sim.simulation import run_simulation
from flock_sim.model import ModelParams

N_TRAJ = 40
SAMPLE_TIMES = list(range(0, T_U, 2))   # every other step, 0..18
N_MC = 24
EPS = 1e-12


def main():
    c = load_canonical()
    lattice, I0, z_t0, h_star = c["lattice"], c["I0"], c["z_t0"], c["h_star"]
    ds = json.load(open(AUDIT_DIR / "data" / "dynamical_shell.json"))
    B_D0 = np.array(ds["B_D0"])
    B_F0 = np.array(ds["B_F0"])
    params = ModelParams()
    pm = build_model(params)
    rng = np.random.default_rng(777)

    # Structural check: every neighbor of every I0 bird must lie in I0 union B_D0.
    I0_and_BD = set(I0.tolist()) | set(B_D0.tolist())
    for i in I0.tolist():
        nbrs = set(lattice.neighbor_ids[i].tolist())
        assert nbrs.issubset(I0_and_BD), f"bird {i} has a neighbor outside I0 union B_D0"
    print("Structural check PASSED: every I0 bird's full neighbor set is contained in I0 union B_D0.")

    # Generate an uncontrolled ensemble from the canonical IC.
    trajs = [run_simulation(nn=100, nt=T_U, seed=900_000 + r, init_z=z_t0, lattice=lattice, params=params)
             for r in range(N_TRAJ)]
    z_hists = np.stack([tr.z_hist for tr in trajs])  # (N_TRAJ, T_U+1, 100)

    # Pooled empirical marginal heading distribution per timestep (for MC fill-in).
    marginals = {}
    for t in SAMPLE_TIMES:
        zt = z_hists[:, t, :]  # (N_TRAJ, 100)
        counts = np.array([np.bincount(zt[:, b], minlength=4) for b in range(100)])  # (100,4)
        marginals[t] = (counts.sum(axis=0) + 1.0) / (counts.sum() + 4.0)  # pooled across all birds, Laplace-smoothed

    unknown_mask_BF = np.ones(100, dtype=bool)
    unknown_mask_BF[np.concatenate([I0, B_F0])] = False
    unknown_ids_BF = np.where(unknown_mask_BF)[0]

    logloss_full, logloss_BD, logloss_BF = [], [], []
    n_bd_exact_matches = 0
    n_total = 0

    for t in SAMPLE_TIMES:
        for r in range(N_TRAJ):
            z_now = z_hists[r, t, :].copy()
            z_next = z_hists[r, t + 1, :]

            G_full = compute_G(pm, lattice, z_now)
            ut_full = policy_posterior(pm, G_full)
            p_full = ut_full @ pm.Bu.T  # (100, nu): p_full[i, h] = P(z_new[i]=h | z_now)

            # M_BD: identical computation restricted conceptually to I0+B_D0, but since
            # every I0 neighbor already lives in I0+B_D0, filling in E with ANYTHING
            # cannot change compute_G's result for I0 birds (they never read E at all).
            # We verify this by actually zeroing/perturbing E and recomputing.
            z_perturbed = z_now.copy()
            other = np.setdiff1d(np.arange(100), np.concatenate([I0, B_D0]))
            z_perturbed[other] = (z_perturbed[other] + 1) % 4  # deliberately corrupt E
            G_bd = compute_G(pm, lattice, z_perturbed)
            ut_bd = policy_posterior(pm, G_bd)
            p_bd = ut_bd @ pm.Bu.T

            for i in I0.tolist():
                if np.allclose(p_bd[i], p_full[i]):
                    n_bd_exact_matches += 1
                n_total += 1
                logloss_full.append(-np.log(p_full[i, z_next[i]] + EPS))
                logloss_BD.append(-np.log(p_bd[i, z_next[i]] + EPS))

            # M_BF: Monte Carlo marginalize the unknown (non I0, non B_F0) birds.
            p_bf_accum = np.zeros((100, 4))
            for _ in range(N_MC):
                z_mc = z_now.copy()
                z_mc[unknown_ids_BF] = rng.choice(4, size=len(unknown_ids_BF), p=marginals[t])
                G_mc = compute_G(pm, lattice, z_mc)
                ut_mc = policy_posterior(pm, G_mc)
                p_bf_accum += ut_mc @ pm.Bu.T
            p_bf = p_bf_accum / N_MC
            for i in I0.tolist():
                logloss_BF.append(-np.log(p_bf[i, z_next[i]] + EPS))

    logloss_full = np.array(logloss_full)
    logloss_BD = np.array(logloss_BD)
    logloss_BF = np.array(logloss_BF)

    out = dict(
        n_samples=n_total, n_traj=N_TRAJ, sample_times=SAMPLE_TIMES, n_mc=N_MC,
        structural_check_neighbors_subset_I0_union_BD0=True,
        frac_BD_predictions_exactly_matching_full=n_bd_exact_matches / n_total,
        mean_logloss_full=float(logloss_full.mean()),
        mean_logloss_BD=float(logloss_BD.mean()),
        mean_logloss_BF=float(logloss_BF.mean()),
        excess_logloss_BD_minus_full=float(logloss_BD.mean() - logloss_full.mean()),
        excess_logloss_BF_minus_full=float(logloss_BF.mean() - logloss_full.mean()),
        interpretation=(
            "excess_logloss_BD_minus_full should be exactly 0 (up to floating point) "
            "because B^D_0 provably contains every input to every I0 bird's update. "
            "excess_logloss_BF_minus_full > 0 indicates the Fiedler boundary omits "
            "real predictive information about I0's next state that the true "
            "dynamical shell captures completely."
        ),
    )
    dump_json(out, AUDIT_DIR / "data" / "predictive_screening.json")
    print(f"n_samples={n_total}  frac B^D exact match={out['frac_BD_predictions_exactly_matching_full']:.4f}")
    print(f"mean logloss: full={out['mean_logloss_full']:.4f}  BD={out['mean_logloss_BD']:.4f}  "
          f"BF={out['mean_logloss_BF']:.4f}")
    print(f"excess logloss (BD - full) = {out['excess_logloss_BD_minus_full']:.5f}  "
          f"(should be ~0)")
    print(f"excess logloss (BF - full) = {out['excess_logloss_BF_minus_full']:.5f}  "
          f"(should be > 0 if Fiedler boundary under-screens)")


if __name__ == "__main__":
    main()
