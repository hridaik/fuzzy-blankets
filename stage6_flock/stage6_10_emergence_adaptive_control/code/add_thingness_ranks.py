"""Materialize Part E percentile ranks into the frozen reference file.

Backfill only: it recomputes nothing scientific, it ranks the (C, G, L, D)
values already in `uncontrolled_reference__main.json` against comparable
candidates and writes them back. Kept separate from the reference pass so the
expensive held-out fits are not re-run to add a derived column.
"""
from __future__ import annotations

import sys

import numpy as np

from common_610 import DATA_DIR, dump_json, load_json
from thingness import add_percentile_ranks, SIZE_TOL


def main(tag="main"):
    path = DATA_DIR / f"uncontrolled_reference__{tag}.json"
    d = load_json(path)
    cands = d["candidates"]
    before = set(cands[0].keys())
    add_percentile_ranks(cands)
    d["percentile_rank_spec"] = dict(
        size_tolerance=SIZE_TOL,
        comparable="same cardinal component count, area within +-25%",
        axes=["C", "G", "L", "D"],
        note="L is near-degenerate at this regime (87% of candidates <= 0.001); "
             "its ranks are stored for completeness but carry no information "
             "and are not used to select or order candidates.")
    dump_json(d, path)
    nc = np.array([c["n_comparable"] for c in cands])
    print(f"ranked {len(cands)} candidates; new keys: "
          f"{sorted(set(cands[0].keys()) - before)}")
    print(f"comparable-set size: median {int(np.median(nc))}, "
          f"min {nc.min()}, max {nc.max()}")
    for ax in ("C", "G", "L", "D"):
        r = np.array([c[f"rank_{ax}"] for c in cands], float)
        r = r[~np.isnan(r)]
        print(f"  rank_{ax}: n={len(r)} spread p10={np.percentile(r,10):.2f} "
              f"p50={np.percentile(r,50):.2f} p90={np.percentile(r,90):.2f}")
    thin = int((nc < 5).sum())
    if thin:
        print(f"NOTE: {thin} candidates have fewer than 5 comparable peers; "
              "their ranks are reported with n_comparable and should not be "
              "read as precise percentiles.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
