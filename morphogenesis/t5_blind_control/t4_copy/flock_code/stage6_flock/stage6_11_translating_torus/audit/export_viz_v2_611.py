"""Stage 6.11B item 14 (data prep): compact per-seed bundle for the audit
visualization, combining:
  - world-frame trajectory (already recorded, viz_bundle_611__seed{n}.json)
  - v1 AND v2 per-step identity (lineage_v2_replay_611__seed{n}.json)
  - per-step thingness metrics (C, D, Q, n_components, f_main) from
    lineage_forensics_611__seed{n}__hypotheses.csv (Part D) + a freshly
    computed f_main
No new simulation; pure data assembly.
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
from geometry_611 import local_scale  # noqa: E402
from lineage_v2_611 import component_sizes  # noqa: E402

SEEDS = (500, 501, 502, 503, 504)


def main():
    bundle = {}
    for seed in SEEDS:
        viz = json.load(open(DATA_DIR / f"viz_bundle_611__seed{seed}.json"))
        replay = json.load(open(AUDIT_DIR / f"lineage_v2_replay_611__seed{seed}.json"))
        hyp_rows = {int(r["t"]): r for r in csv.DictReader(open(AUDIT_DIR / f"lineage_forensics_611__seed{seed}__hypotheses.csv"))}
        replay_by_t = {r["t"]: r for r in replay["per_step"]}
        log = json.load(open(DATA_DIR / f"online_control_611__seed{seed}.json"))["log"]
        qual_t = next((e["t"] for e in log if e["event"] == "qualified_and_target_set"), None)

        frames = []
        for frame in viz["frames"]:
            t = frame["t"]
            rep = replay_by_t.get(t, {})
            hyp = hyp_rows.get(t, {})
            r = np.array(frame["r"])
            v2_members = np.array(rep.get("v2_members", []), dtype=int)
            f_main = None
            if len(v2_members):
                sizes = component_sizes(v2_members, r, L_BOX, local_scale(r, L_BOX))
                f_main = max(sizes) / max(1, sum(sizes)) if sizes else 1.0
            def rnd(v, nd=3):
                return [round(float(x), nd) for x in v] if isinstance(v, list) else round(float(v), nd)
            frames.append(dict(
                t=t, r=[[round(float(x), 3), round(float(y), 3)] for x, y in frame["r"]], z=frame["z"],
                phase=frame["phase"][0], centre=(rnd(frame["centre"]) if frame.get("centre") else None),
                actuators=frame["actuators"], target_heading=frame["target_heading"],
                v1=frame["interior"], v2=rep.get("v2_members", []),
                p1=(round(rep["v1_map_prob"], 3) if rep.get("v1_map_prob") is not None else None),
                p2=(round(rep["v2_map_prob"], 3) if rep.get("v2_map_prob") is not None else None),
                dw2=rep.get("v2_map_dwell"),
                ent2=(round(rep["v2_entropy"], 3) if rep.get("v2_entropy") is not None else None),
                mar2=(round(rep["v2_margin"], 3) if rep.get("v2_margin") is not None else None),
                ov=rep.get("overlap_v1_v2"),
                C=(round(float(hyp["C"]), 3) if hyp.get("C") not in (None, "") else None),
                D=(round(float(hyp["D"]), 3) if hyp.get("D") not in (None, "") else None),
                Q=(round(float(hyp["Q"]), 3) if hyp.get("Q") not in (None, "") else None),
                nc=(int(hyp["n_components"]) if hyp.get("n_components") not in (None, "") else None),
                fm=(round(f_main, 3) if f_main is not None else None),
            ))
        bundle[seed] = dict(N=viz["N"], L=viz["L"], ended_phase=viz["ended_phase"],
                              qualified_t=qual_t, frames=frames)
    with open(AUDIT_DIR / "viz_v2_bundle_611.json", "w") as f:
        json.dump(bundle, f, separators=(",", ":"))
    print(f"wrote viz_v2_bundle_611.json, seeds={list(bundle.keys())}, "
          f"frame counts={[len(b['frames']) for b in bundle.values()]}")


if __name__ == "__main__":
    main()
