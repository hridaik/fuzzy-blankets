"""Stage 6.10 Part H -- apply the predeclared operating-task selection rules.

Mechanically implements `logs/task_selection_predeclared.txt`, which was written
before the corrected controllability scan existed:

  RULE 1  frozen cell   = smallest-resource cell with frac_above_hi >= 0.50
                          (actuator fraction first, then horizon).
                          If none qualifies, the highest frac_above_hi cell,
                          flagged as reliability-not-established.
  RULE 2  primary set   = episodes where the BENCHMARK reached H >= 0.60 in
                          that cell. Nothing else may define this set.
  RULE 3  scope         = the excluded count travels with every Part I result.

Writes the decision into the controllability data file so that Part I reads its
episode list from a frozen artefact rather than recomputing it.
"""
from __future__ import annotations

import sys

import numpy as np

from common_610 import DATA_DIR, dump_json, load_json

HI = 0.60
RELIABLE = 0.50


def main(tag="main"):
    path = DATA_DIR / f"controllability__{tag}.json"
    d = load_json(path)
    cells = d["cells"]

    rows = []
    for key, c in cells.items():
        rows.append(dict(key=key, frac=c["frac"], horizon=c["horizon"],
                         mean=c["mean_final"], above=c["frac_above_hi"],
                         below=c["frac_below_lo"]))
    rows.sort(key=lambda r: (r["frac"], r["horizon"]))

    print(f"{'cell':<12}{'meanH':>8}{'>=0.60':>9}{'<=0.10':>9}   qualifies")
    for r in rows:
        print(f"f{r['frac']:<4} T{r['horizon']:<5}{r['mean']:>8.3f}{r['above']:>9.2f}"
              f"{r['below']:>9.2f}   {'yes' if r['above'] >= RELIABLE else 'no'}")

    ok = [r for r in rows if r["above"] >= RELIABLE]
    if ok:
        pick = ok[0]                      # already sorted smallest-resource first
        established = True
    else:
        pick = max(rows, key=lambda r: r["above"])
        established = False

    cell = cells[pick["key"]]
    primary = sorted(int(row["seed"]) for row in cell["rows"] if row["final_H"] >= HI)
    excluded = sorted(int(row["seed"]) for row in cell["rows"] if row["final_H"] < HI)

    dec = dict(
        rule_source="logs/task_selection_predeclared.txt",
        frozen_cell=dict(frac=pick["frac"], horizon=pick["horizon"], key=pick["key"]),
        reliability_threshold=RELIABLE, h_threshold=HI,
        reliability_established_at_cell_level=established,
        primary_episodes=primary, excluded_episodes=excluded,
        n_primary=len(primary), n_excluded=len(excluded),
        selected_by="full-model control benchmark only; no inference arm was run "
                    "on any cell before this decision",
        claim_scope=("All Part I conclusions are scoped to the stratum where the "
                     "full-model benchmark itself steers the collective. "
                     f"{len(excluded)} of {len(primary) + len(excluded)} qualifying "
                     "episodes are excluded and no claim covers them."))
    d["frozen_task"] = dec
    dump_json(d, path)

    print(f"\nFROZEN CELL: actuator fraction {pick['frac']}, horizon {pick['horizon']}"
          f"   (reliability established at cell level: {established})")
    print(f"PRIMARY EPISODES ({len(primary)}): {primary}")
    print(f"EXCLUDED  ({len(excluded)}): {excluded}")
    if not established:
        print("\nNOTE: no cell reached the 0.50 reliability bar. The task is NOT "
              "established as reliably controllable at the cell level; Part I "
              "runs only on the per-episode primary stratum, and every claim "
              "carries that scope.")
    if len(primary) < 6:
        print(f"\nWARNING: the steerable stratum has only {len(primary)} episodes. "
              "Per the predeclaration this is reported as the result rather than "
              "fixed by enlarging the control budget.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
