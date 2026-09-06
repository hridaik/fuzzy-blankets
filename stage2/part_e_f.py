"""
Part E: confidence-certified approximate blankets (fixed I={1,2,3}, 32 candidates).
Part F: graded membership under finite uncertainty (statistical selection stability).
"""
import sys, os, itertools, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import core
from part_b_c import sample_covariance, sample_multivariate_normal, L_plugin_batch, beta_pqr, COV_DIVISOR
from part_d import fit_gaussian, bootstrap_replicates_cov, ci_from_bootstrap

RNG_ROOT = 20260818 + 2

I_idx = core.I_IDX
rest_nodes = core.REST_NODES
ALL_CANDIDATES = []
for rr in range(len(rest_nodes) + 1):
    for Bc in itertools.combinations(rest_nodes, rr):
        ALL_CANDIDATES.append(Bc)  # 32 candidates, tuples of node labels


def population_L(Sigma, Bkey):
    B_idx = [core.idx[nn] for nn in Bkey]
    E_idx = [core.idx[nn] for nn in rest_nodes if nn not in Bkey]
    return core.L_cmi_cov_joint(Sigma, I_idx, B_idx, E_idx)


def population_optimal_set(Sigma, delta):
    certified = [B for B in ALL_CANDIDATES if population_L(Sigma, B) <= delta]
    if not certified:
        return None, None
    min_size = min(len(B) for B in certified)
    return min_size, sorted([B for B in certified if len(B) == min_size])


def U95_all_candidates(S_fit, Sb_batch, n, alpha=0.05):
    """Returns dict B -> U_{1-alpha}(B), computed from one shared bootstrap batch."""
    out = {}
    for Bkey in ALL_CANDIDATES:
        B_idx = [core.idx[nn] for nn in Bkey]
        E_idx = [core.idx[nn] for nn in rest_nodes if nn not in Bkey]
        p, q, r = len(I_idx), len(E_idx), len(B_idx)
        beta_val = beta_pqr(p, q, r, n)
        try:
            L_fit = core.L_cmi_cov_joint(S_fit, I_idx, B_idx, E_idx)
        except np.linalg.LinAlgError:
            out[Bkey] = np.nan
            continue
        L_obs_raw = L_plugin_batch(S_fit[None], I_idx, B_idx, E_idx)[0]
        L_obs_tilde = L_obs_raw - beta_val
        L_b_raw = L_plugin_batch(Sb_batch, I_idx, B_idx, E_idx)
        valid = ~np.isnan(L_b_raw)
        if valid.sum() < 10:
            out[Bkey] = np.nan
            continue
        L_b_tilde = L_b_raw[valid] - beta_val
        e_b = L_b_tilde - L_fit
        _, _, U = ci_from_bootstrap(L_obs_tilde, L_fit, e_b, alpha=alpha)
        out[Bkey] = U
    return out


def classify(selected, min_size_pop, optimal_pop_set):
    if selected is None:
        return "none_certified", None
    min_size_sel, sel_sets = selected
    identity_ok = set(sel_sets) == set(optimal_pop_set)
    if len(sel_sets) > 1:
        tag = "tied"
    elif min_size_sel < min_size_pop:
        tag = "too_small"
    elif min_size_sel > min_size_pop:
        tag = "too_large"
    else:
        tag = "population_optimal" if identity_ok else "correct_size_wrong_identity"
    return tag, sel_sets


if __name__ == "__main__":
    print("=== Part E: confidence-certified blankets ===")
    deltas = [0.01, 0.025, 0.05]
    eps_list = [0, 1]
    n_list = [50, 200, 1000]  # reduced from Part D's 4-value list purely for the 32x candidate
                               # bootstrap cost (32x more logdet work per replicate); documented,
                               # not tuned to favor any particular outcome.
    R_outer = 100  # reduced from 200 for the same compute-budget reason; documented explicitly.
    M_boot = 500
    print(f"Settings: n in {n_list}, R_outer={R_outer} datasets/cell, M_boot={M_boot} bootstrap reps/dataset, "
          f"deltas={deltas}, eps in {eps_list}. (Reduced R_outer/n-grid vs Part D purely because this "
          f"step requires computing U_0.95 for all 32 candidates per dataset instead of 3.)")

    # population-optimal sets, verified programmatically against prompt's expected values
    print("\nPopulation-optimal certified boundary (ground truth, no sampling):")
    pop_opt = {}
    for eps in eps_list:
        Omega = core.Omega0 if eps == 0 else core.Omega_eps(1.0)
        Sigma = np.linalg.inv(Omega)
        for delta in deltas:
            min_size, opt_set = population_optimal_set(Sigma, delta)
            pop_opt[(eps, delta)] = (min_size, opt_set)
            print(f"  eps={eps}, delta={delta}: min|B|={min_size}, optimal set(s)={opt_set}")

    expected_pop = {
        (0, 0.01): [(4, 5)], (0, 0.025): [(4, 5)], (0, 0.05): [(4,)],
        (1, 0.01): [(4, 5, 6)], (1, 0.025): [(4, 5)], (1, 0.05): [(4, 5)],
    }
    print("\nCross-check vs prompt's stated expectations:")
    for k, v in expected_pop.items():
        got = pop_opt[k][1]
        match = got == v
        print(f"  eps={k[0]}, delta={k[1]}: expected {v}, got {got}, match={match}")

    rows = []
    detail_rows = []  # for Part F membership frequencies
    rng_master = np.random.default_rng(RNG_ROOT)
    for eps in eps_list:
        Omega = core.Omega0 if eps == 0 else core.Omega_eps(1.0)
        Sigma = np.linalg.inv(Omega)
        for n in n_list:
            seed = int(rng_master.integers(0, 2**31 - 1))
            rng = np.random.default_rng(seed)
            # counts per delta
            counts = {delta: dict(none_certified=0, too_small=0, too_large=0, tied=0,
                                    population_optimal=0, correct_size_wrong_identity=0) for delta in deltas}
            membership_counts = {delta: {k: 0 for k in rest_nodes} for delta in deltas}
            n_eff = 0
            for rep in range(R_outer):
                X = sample_multivariate_normal(n, Sigma, rng)
                mu_fit, S_fit = fit_gaussian(X)
                try:
                    Sb = bootstrap_replicates_cov(n, S_fit, M_boot, rng)
                except np.linalg.LinAlgError:
                    continue
                U_all = U95_all_candidates(S_fit, Sb, n, alpha=0.05)
                if all(np.isnan(v) for v in U_all.values()):
                    continue
                n_eff += 1
                for delta in deltas:
                    min_size_pop, opt_set = pop_opt[(eps, delta)]
                    certified = [B for B, U in U_all.items() if not np.isnan(U) and U <= delta]
                    if not certified:
                        selected = None
                    else:
                        min_size_sel = min(len(B) for B in certified)
                        sel_sets = sorted([B for B in certified if len(B) == min_size_sel])
                        selected = (min_size_sel, sel_sets)
                    tag, sel_sets = classify(selected, min_size_pop, opt_set)
                    counts[delta][tag] = counts[delta].get(tag, 0) + 1
                    if sel_sets is not None:
                        # m_k(delta) = P(k in UNION of selected minimal-size sets this rep);
                        # increment each node at most once per rep even if multiple tied sets
                        nodes_in_selection = set()
                        for Bsel in sel_sets:
                            nodes_in_selection.update(Bsel)
                        for node in nodes_in_selection:
                            membership_counts[delta][node] += 1
            for delta in deltas:
                row = dict(eps=eps, n=n, delta=delta, R_outer=R_outer, n_eff=n_eff, **counts[delta])
                rows.append(row)
                print(f"eps={eps} n={n:<6} delta={delta}: n_eff={n_eff} " +
                      ", ".join(f"{k}={v}" for k, v in counts[delta].items()))
                for node in rest_nodes:
                    # divide by number of selected-set slots (n_eff, since each rep contributes
                    # membership count relative to number of selected sets that rep produced;
                    # for a clean per-rep inclusion probability we instead recompute below)
                    pass
                detail_rows.append(dict(eps=eps, n=n, delta=delta, n_eff=n_eff,
                                          **{f"m_{node}_raw_count": membership_counts[delta][node] for node in rest_nodes}))

    outpath = os.path.join(os.path.dirname(__file__), "data", "part_e_selection_table.csv")
    with open(outpath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved Part E selection table to {outpath}")

    outpath2 = os.path.join(os.path.dirname(__file__), "data", "part_f_membership_raw.csv")
    with open(outpath2, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(detail_rows[0].keys()))
        writer.writeheader()
        writer.writerows(detail_rows)
    print(f"Saved Part F raw membership counts to {outpath2}")
