"""Stage 6.11B item 3: actually invoke the thingness/clump gate.

Calibrates ThingnessThresholds from UNCONTROLLED development data only
(never from control outcome, per PLAN.md Section V rule 6), then applies the
UNCHANGED gate (`thingness_611.passes_gate`, imported not reimplemented) to:
  (a) the calibration set itself (sanity check on the calibrated percentile),
  (b) all five online seeds' actual per-step MAP interior (v1), reusing the
      C/D/Q/n_components/size_frac already computed in
      audit/lineage_forensics_611__seed{n}__hypotheses.csv (Part D of the
      prior pass) plus a freshly-computed f_main (NOT present in that CSV),
  and reports, per seed, whether the step at which the ORIGINAL pipeline
  actually set a control target would have passed the intended gate.

G and L are never computed anywhere in the reported Stage 6.11 online
pipeline (METHODS_AUDIT_6_11.md / LINEAGE_FORENSICS_6_11.md 5) -- they are
reported here as unavailable, which `thingness_611.passes_gate` already
handles correctly (a None check does not count against `passes`), rather
than invented. This is disclosed, not silently patched.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(AUDIT_DIR))
sys.path.insert(0, str(CODE_DIR))
import common_611  # noqa: E402,F401

from common_611 import DATA_DIR, L_BOX, dump_json  # noqa: E402
from flock_sim.model import UV4  # noqa: E402
from detect_69 import propose  # noqa: E402
from thingness_611 import geometry_features, calibrate_thresholds, passes_gate, ThingnessThresholds  # noqa: E402
from geometry_611 import local_scale  # noqa: E402
from lineage_v2_611 import component_sizes  # noqa: E402

SEEDS = (500, 501, 502, 503, 504)
AFFINITY_WINDOW = 6
N_DEV_EPISODES = 10
DWELL_MIN = 30   # QUALIFY_MIN_DURATION, for the gate's own dwell check


def collect_dev_records():
    d = np.load(DATA_DIR / "observational_corpus_611__train.npz")
    episodes = [dict(r_hist=d["r_hist"][k], z_hist=d["z_hist"][k]) for k in range(min(N_DEV_EPISODES, len(d["seeds"])))]
    records = []
    for ep in episodes:
        r_hist, z_hist = ep["r_hist"], ep["z_hist"]
        z_window = []
        for t in range(0, r_hist.shape[0], 4):
            z_window.append(z_hist[t])
            if len(z_window) > AFFINITY_WINDOW:
                z_window.pop(0)
            if len(z_window) < 2:
                continue
            cands = propose(r_hist[t], z_window, L_BOX)
            for c in cands[:3]:
                geo = geometry_features(c, r_hist[t], z_hist[t], L_BOX, UV4)
                records.append(geo)   # G, L absent -- never computed by construction, consistent with production
    return records


def f_main_for(members, r, L):
    sizes = component_sizes(members, r, L, local_scale(r, L))
    return max(sizes) / max(1, sum(sizes)) if sizes else 1.0


def main():
    print("[thingness_gate_audit] collecting uncontrolled dev records for threshold calibration...", flush=True)
    dev_records = collect_dev_records()
    print(f"  n_dev_records={len(dev_records)}", flush=True)
    thr = calibrate_thresholds(dev_records, dwell_min=DWELL_MIN, percentile=25.0)
    thr_dict = dict(C_min=thr.C_min, G_min=thr.G_min, L_max=thr.L_max, D_min=thr.D_min, Q_min=thr.Q_min,
                      size_frac_range=thr.size_frac_range, dwell_min=thr.dwell_min, percentile=thr.percentile)
    print(f"  calibrated thresholds: {thr_dict}", flush=True)

    # (a) sanity check: pass rate on the calibration set itself for each hard check
    dev_pass_rates = {}
    for key in ("C", "D", "Q"):
        vals = np.array([r[key] for r in dev_records])
        dev_pass_rates[key] = float((vals >= getattr(thr, f"{key}_min")).mean())
    dev_pass_rates["one_dominant_component"] = float(np.mean([r["n_components"] == 1 for r in dev_records]))
    dev_pass_rates["size_frac_in_range"] = float(np.mean(
        [thr.size_frac_range[0] <= r["size_frac"] <= thr.size_frac_range[1] for r in dev_records]))
    dev_n_components_dist = np.array([r["n_components"] for r in dev_records])

    # (b) apply to all five online seeds' actual per-step MAP interior
    per_seed = {}
    for seed in SEEDS:
        rows = list(csv.DictReader(open(AUDIT_DIR / f"lineage_forensics_611__seed{seed}__hypotheses.csv")))
        viz = json.load(open(DATA_DIR / f"viz_bundle_611__seed{seed}.json"))
        frames_by_t = {f["t"]: f for f in viz["frames"]}
        log = json.load(open(DATA_DIR / f"online_control_611__seed{seed}.json"))["log"]
        qual_t = next((e["t"] for e in log if e["event"] == "qualified_and_target_set"), None)

        step_results = []
        for row in rows:
            t = int(row["t"])
            frame = frames_by_t.get(t)
            interior = np.array(frame["interior"], dtype=int) if frame else np.array([], dtype=int)
            f_main = f_main_for(interior, np.array(frame["r"]), L_BOX) if len(interior) else 1.0
            record = dict(C=float(row["C"]), D=float(row["D"]), Q=float(row["Q"]),
                           n_components=int(row["n_components"]), size_frac=float(row["size_frac"]),
                           G=None, L=None)
            gate = passes_gate(record, thr, dwell=DWELL_MIN)   # dwell evaluated at its qualifying value
                                                                  # (this checks the GATE, not re-deriving dwell)
            step_results.append(dict(t=t, passes=gate["passes"], checks=gate["checks"], f_main=f_main,
                                       n_components=record["n_components"], C=record["C"], D=record["D"],
                                       Q=record["Q"], size_frac=record["size_frac"]))

        frac_pass = float(np.mean([s["passes"] for s in step_results])) if step_results else None
        qual_step = next((s for s in step_results if s["t"] == qual_t), None) if qual_t is not None else None
        per_seed[seed] = dict(
            qualified_t=qual_t, n_steps=len(step_results),
            frac_steps_passing_full_gate=frac_pass,
            qualification_moment_passes_gate=(qual_step["passes"] if qual_step else None),
            qualification_moment_checks=(qual_step["checks"] if qual_step else None),
            qualification_moment_f_main=(qual_step["f_main"] if qual_step else None),
            mean_f_main=float(np.mean([s["f_main"] for s in step_results])) if step_results else None,
        )
        print(f"  seed {seed}: qual_t={qual_t} frac_pass_gate={frac_pass:.3f} "
              f"qual_moment_passes={per_seed[seed]['qualification_moment_passes_gate']}", flush=True)

    out = dict(calibrated_thresholds=thr_dict, n_dev_records=len(dev_records),
                dev_pass_rates_sanity_check=dev_pass_rates,
                dev_n_components_percentiles=dict(p50=float(np.percentile(dev_n_components_dist, 50)),
                                                     p90=float(np.percentile(dev_n_components_dist, 90))),
                per_seed=per_seed,
                note="G and L are never computed by the online pipeline (confirmed in METHODS_AUDIT_6_11.md); "
                     "reported here as None throughout, which passes_gate treats as not-yet-evaluated, not failing.")
    dump_json(out, AUDIT_DIR / "thingness_gate_audit_611.json")
    print(json.dumps({k: v for k, v in out.items() if k != "per_seed"}, indent=1, default=str))


if __name__ == "__main__":
    main()
