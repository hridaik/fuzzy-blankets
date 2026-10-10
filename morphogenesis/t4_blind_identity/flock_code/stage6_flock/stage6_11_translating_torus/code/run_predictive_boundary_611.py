"""Stage 6.11 driver: fit the relational passive predictor (item 6), report
the machine-readable corpus/fit statistics (item 5), and run predictive-
boundary construction + certification (item 7) for one detected candidate.
"""
from __future__ import annotations

import argparse
import gc
import json
import pickle

import numpy as np

from common_611 import DATA_DIR, LOG_DIR, dump_json, L_BOX
import predictive_boundary_611 as P
from detect_69 import propose

ONLINE_MODEL_M_OBS = 12   # the pool size the online control loop (item 14) reuses
MAX_ROWS_PER_EPISODE = 600   # reduced from 1500: bounds peak memory of this driver


def load_split(name: str) -> list[dict]:
    d = np.load(DATA_DIR / f"observational_corpus_611__{name}.npz")
    return [dict(seed=int(s), r_hist=d["r_hist"][k], z_hist=d["z_hist"][k])
            for k, s in enumerate(d["seeds"])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m_obs", type=int, default=None,
                     help="Run a single M_obs value (keeps peak memory bounded by running each "
                          "pool size as a separate process); omit to run the full M_OBS_GRID.")
    args = ap.parse_args()
    m_obs_grid = [args.m_obs] if args.m_obs is not None else list(P.M_OBS_GRID)

    rng = np.random.default_rng(42)
    train = load_split("train")
    val = load_split("val")
    test = load_split("test")

    out_path = DATA_DIR / "predictive_boundary_611.json"
    results = json.loads(out_path.read_text()) if out_path.exists() else {}
    for M_obs in m_obs_grid:
        print(f"[predictive_boundary_611] M_obs={M_obs}: estimating distance cuts from train...")
        dist_cuts = P.estimate_distance_cuts(train[0]["r_hist"], train[0]["z_hist"], L_BOX, M_obs, rng)
        train_rows = P.build_rows_multi(train, L_BOX, M_obs, dist_cuts, rng, max_rows_per_episode=MAX_ROWS_PER_EPISODE)
        val_rows = P.build_rows_multi(val, L_BOX, M_obs, dist_cuts, rng, max_rows_per_episode=MAX_ROWS_PER_EPISODE)
        test_rows = P.build_rows_multi(test, L_BOX, M_obs, dist_cuts, rng, max_rows_per_episode=MAX_ROWS_PER_EPISODE)
        print(f"  rows: train={len(train_rows)} val={len(val_rows)} test={len(test_rows)}")

        model = P.RelationalHeadingModel(M_obs=M_obs, dist_cuts=dist_cuts, L=L_BOX)
        model.fit(train_rows)
        train_ll = model.mean_logloss(train_rows)
        val_ll = model.mean_logloss(val_rows)
        test_ll = model.mean_logloss(test_rows)
        print(f"  mean logloss: train={train_ll:.4f} val={val_ll:.4f} test={test_ll:.4f} "
              f"(uniform baseline={np.log(4):.4f})")

        results[f"M_obs_{M_obs}"] = dict(
            M_obs=M_obs, dist_cuts=dist_cuts.tolist(),
            n_fit_rows=model.n_fit_rows, n_val_rows=len(val_rows), n_test_rows=len(test_rows),
            train_mean_logloss=train_ll, val_mean_logloss=val_ll, test_mean_logloss=test_ll,
            uniform_baseline_logloss=float(np.log(4)),
        )

        if M_obs == ONLINE_MODEL_M_OBS:
            # Persist the fitted model so the online control loop (item 14)
            # LOADS it instead of rebuilding the full corpus + refitting from
            # scratch inside a live episode -- avoids the memory/time blowup
            # of repeating this fit inside run_online_control_611.py.
            with open(DATA_DIR / "pretrained_relational_model_611.pkl", "wb") as f:
                pickle.dump(dict(model=model, dist_cuts=dist_cuts, M_obs=M_obs,
                                  train_rows_sample=train_rows[:4000]), f)
            print(f"  saved pretrained model (M_obs={M_obs}) to "
                  f"{DATA_DIR / 'pretrained_relational_model_611.pkl'}")

        # ---- item 7: boundary construction + certification, one candidate ----
        # Use a mid-episode snapshot from a VAL episode to detect a candidate.
        ep = val[0]
        t0 = 90
        r_t, z_t = ep["r_hist"][t0], ep["z_hist"][t0]
        z_window = ep["z_hist"][max(0, t0 - 5):t0 + 1]
        cands = propose(r_t, z_window, L_BOX)
        if not cands:
            print("  no candidate detected at this snapshot; skipping boundary construction")
            continue
        members = cands[0]
        from geometry_611 import local_scale
        periphery_radius = local_scale(r_t, L_BOX)
        print(f"  candidate: size={len(members)}, periphery_radius={periphery_radius:.3f}")

        construct_rows = P.rows_for_targets(val, members, L_BOX, M_obs, dist_cuts, periphery_radius, rng,
                                             max_rows_total=3000)
        print(f"  construction rows (val periphery): {len(construct_rows)}")
        bnd = P.construct_boundary(model, members, construct_rows)
        print(f"  B_pred = {bnd['B']} (interior_only_loss={bnd['interior_only_loss']:.4f}, "
              f"full_pool_loss={bnd['full_pool_loss']:.4f}, final_loss={bnd['final_loss']:.4f})")

        cert = P.certify(model, members, bnd["B"], test, L_BOX, M_obs, dist_cuts, periphery_radius, rng,
                          n_boot=100, max_rows_per_episode=400)
        print(f"  certification: L_challenge_upper={cert['L_challenge_upper']:.4f} "
              f"(delta={cert['delta']}) sufficient={cert['predictively_sufficient_rel_challenger_class']}")

        results[f"M_obs_{M_obs}"]["boundary"] = dict(members=members.tolist(), **bnd)
        results[f"M_obs_{M_obs}"]["certification"] = cert

        dump_json(results, out_path)
        print(f"[predictive_boundary_611] wrote {out_path} (after M_obs={M_obs})")
        del train_rows, val_rows, test_rows, construct_rows
        gc.collect()

    print("[predictive_boundary_611] done")


if __name__ == "__main__":
    main()
