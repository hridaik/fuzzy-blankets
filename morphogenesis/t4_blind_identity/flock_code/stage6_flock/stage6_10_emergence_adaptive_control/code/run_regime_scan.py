"""Stage 6.10 Part G -- operating-regime search from UNCONTROLLED data only.

For each (beta, s) cell this reports, from uncontrolled trajectories:
  policy saturation          candidate size distribution
  persistence                clumpness Q_clump
  membership turnover        boundary (interface) turnover
  non-globality              susceptibility chi_tau to the standardized weak probe

The regime is NOT selected by later controller performance -- no controller is
run here and none is importable from this script. The target is a
ROBUST-RESPONSIVE window: the collective persists, a weak cue has a measurable
but non-saturating effect, the lineage stays coherent, the interface changes,
and the policy posterior is not numerically locked.
"""
from __future__ import annotations

import sys

import numpy as np

from common_610 import DATA_DIR, dump_json, rotate_cw, UV4
from episode_data import make_simulator, run_episode, observation_record
import candidate_detection as cd
import adaptive_control as ac
import reference_truth as rt
from morphology import morphology
from regime_probe import susceptibility, policy_saturation

NT = 90
T_EVAL = list(range(60, 81, 5))      # states at which candidates are characterized
T_PROBE = 70                          # single state for the susceptibility curve
SEEDS = list(range(8))
MIN_SIZE, MAX_SIZE = 12, 90           # "moderate size" band, declared here


def characterize(sim, seed, L):
    res = run_episode(sim, seed, nt=NT, record_oracle=False)
    rows, track = [], None
    for t in T_EVAL:
        obs = observation_record(sim, res.z_hist, t)
        ok, _ = cd.propose(obs)
        if not ok:
            continue
        # Follow one lineage by maximum overlap, exactly as the blind tracker
        # does. The lineage is SEEDED on the moderate-size, most clump-like
        # candidate rather than the largest: the desiderata ask for a
        # moderate-size clump-like collective, and characterising the ~120-bird
        # blob instead makes every response look dead simply because the
        # interface is a tiny fraction of it. Declared here, before the scan is
        # read; it uses only size and morphology, never any control outcome.
        if track is None:
            mod = [c for c in ok if MIN_SIZE <= c.size <= MAX_SIZE]
            pool = mod if mod else list(ok)
            cand = max(pool, key=lambda c: morphology(
                np.array(sorted(int(x) for x in c.members)), L)["q_clump"])
        else:
            cand = max(ok, key=lambda c: len(set(c.members.tolist()) & set(track)))
        I = np.array(sorted(int(x) for x in cand.members))
        prev = set(track) if track else set(I.tolist())
        track = I.tolist()
        m = morphology(I, L)
        B = rt.structural_interface(sim, res.z_hist[t], I)
        rows.append(dict(t=t, size=len(I), I=[int(x) for x in I], q_clump=m["q_clump"],
                         n_components=m["n_components"],
                         turnover=len(set(I.tolist()) - prev) / max(1, len(I)),
                         jaccard=len(set(I.tolist()) & prev) / max(1, len(set(I.tolist()) | prev)),
                         B_size=int(len(B)), B_ids=[int(x) for x in B],
                         sizes_all=[c.size for c in ok], n_cands=len(ok)))
    sat = policy_saturation(sim, res.z_hist[T_PROBE])
    return res, rows, sat


def main(tag="main"):
    grid = [(b, s) for b in (1.0, 0.6, 0.5, 0.4) for s in (1.0, 0.75, 0.5)]
    out = dict(protocol="stage6_10 Part G regime scan (uncontrolled only)",
               nn=400, nt=NT, seeds=SEEDS, t_eval=T_EVAL, t_probe=T_PROBE,
               moderate_size_band=[MIN_SIZE, MAX_SIZE], cells=[])
    L = 20
    for beta, s in grid:
        sim = make_simulator(400, beta, s)
        per_seed, chis = [], []
        for seed in SEEDS:
            res, rows, sat = characterize(sim, seed, L)
            if not rows:
                per_seed.append(dict(seed=seed, tracked=False, **sat)); continue
            sizes = [r["size"] for r in rows]
            per_seed.append(dict(
                seed=seed, tracked=True, n_frames=len(rows),
                mean_size=float(np.mean(sizes)),
                frac_moderate=float(np.mean([(MIN_SIZE <= x <= MAX_SIZE) for x in sizes])),
                frac_global=float(np.mean([x > 0.55 * 400 for x in sizes])),
                mean_q=float(np.nanmean([r["q_clump"] for r in rows])),
                mean_comp=float(np.mean([r["n_components"] for r in rows])),
                mean_turnover=float(np.mean([r["turnover"] for r in rows[1:]])) if len(rows) > 1 else 0.0,
                mean_jaccard=float(np.mean([r["jaccard"] for r in rows[1:]])) if len(rows) > 1 else 1.0,
                mean_B=float(np.mean([r["B_size"] for r in rows])),
                B_turnover=float(np.mean([
                    len(set(rows[i]["B_ids"]) - set(rows[i-1]["B_ids"])) / max(1, len(rows[i]["B_ids"]))
                    for i in range(1, len(rows))])) if len(rows) > 1 else 0.0,
                n_cands=float(np.mean([r["n_cands"] for r in rows])), **sat))
            # susceptibility at the probe state, on the tracked candidate
            probe_row = [r for r in rows if r["t"] == T_PROBE]
            if probe_row and seed < 4:
                # susceptibility of the TRACKED lineage at the probe state --
                # the same object the scan characterises everywhere else
                I = np.array(sorted(int(x) for x in probe_row[0]["I"]))
                z = res.z_hist[T_PROBE]
                h0 = int(np.bincount(z[I], minlength=4).argmax())
                h_star = rotate_cw(h0)
                B = [int(x) for x in rt.structural_interface(sim, z, I)]
                chi = susceptibility(sim, z, I, h_star, B, seed=1000 + seed)
                chi["seed"] = seed; chi["I_size"] = len(I); chi["h0"] = h0; chi["h_star"] = h_star
                chis.append(chi)
        ok_rows = [p for p in per_seed if p.get("tracked")]
        agg = {}
        for k in ("mean_size", "frac_moderate", "frac_global", "mean_q", "mean_comp",
                  "mean_turnover", "mean_jaccard", "mean_B", "B_turnover", "n_cands",
                  "frac_locked", "median_max_ut", "median_G_gap"):
            v = [p[k] for p in ok_rows if k in p]
            agg[k] = float(np.mean(v)) if v else float("nan")
        chi_max = [c["chi_max"] for c in chis] or [float("nan")]
        cell = dict(beta=beta, s=s, per_seed=per_seed, chi=chis,
                    chi_max_mean=float(np.nanmean(chi_max)),
                    frac_dead=float(np.mean([c["dead"] for c in chis])) if chis else float("nan"),
                    frac_saturating=float(np.mean([bool(c["saturating"]) for c in chis])) if chis else float("nan"),
                    **agg)
        out["cells"].append(cell)
        print(f"beta={beta:<4} s={s:<5} locked={agg['frac_locked']:.2f} "
              f"ut={agg['median_max_ut']:.4f} size={agg['mean_size']:6.1f} "
              f"mod={agg['frac_moderate']:.2f} glob={agg['frac_global']:.2f} "
              f"Q={agg['mean_q']:.2f} comp={agg['mean_comp']:.1f} "
              f"turn={agg['mean_turnover']:.3f} Bturn={agg['B_turnover']:.2f} "
              f"chi={cell['chi_max_mean']:.3f}", flush=True)
        dump_json(out, DATA_DIR / f"regime_scan__{tag}.json")
    dump_json(out, DATA_DIR / f"regime_scan__{tag}.json")
    print("wrote", DATA_DIR / f"regime_scan__{tag}.json")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
