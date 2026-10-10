"""Cross-snapshot analysis backing RESULTS_6_6.md's final scientific
questions (task brief section 36). Reads data/*.json only; does not re-run
the simulator or refit any model. Prints a report and writes
data/results_summary.json for citation."""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = STAGE_DIR / "data"


def load_all():
    out = {}
    for p in sorted(DATA_DIR.glob("seed*__*.json")):
        d = json.loads(p.read_text())
        out[d["meta"]["snapshot_id"]] = d
    return out


def summarize(d: dict) -> dict:
    rows = d["rows"]
    meta = d["meta"]
    C = np.array([r["C_internal"] for r in rows])
    G = np.array([r["G_internal"] for r in rows])
    Lv = np.array([r["L_blanket"] for r in rows])
    D = np.array([r["D_local"] for r in rows])
    Sh = np.array([r["structural_shell_size"] for r in rows])
    Pa = np.array([r["is_pareto"] for r in rows])
    used_full = Sh <= meta["K_boundary_budget"]

    def stats(x):
        return dict(min=float(x.min()), mean=float(x.mean()), max=float(x.max()), std=float(x.std()))

    def corr(a, b):
        if a.std() < 1e-12 or b.std() < 1e-12:
            return None
        return float(np.corrcoef(a, b)[0, 1])

    ideal = (G > np.percentile(G, 80)) & (Lv < np.percentile(Lv, 20)) & (C > 0.9) & (D > np.percentile(D, 80))
    hiC_loG = (C > 0.9) & (G < np.percentile(G, 20))
    loL_loD = (Lv < np.percentile(Lv, 20)) & (D < np.percentile(D, 20))

    return dict(
        snapshot_id=meta["snapshot_id"], seed=meta["seed"], condition=meta["condition"],
        n=len(rows),
        C=stats(C), G=stats(G), L=stats(Lv), D=stats(D),
        corr_C_G=corr(C, G), corr_C_D=corr(C, D), corr_G_L=corr(G, Lv),
        corr_L_D=corr(Lv, D), corr_G_D=corr(G, D),
        frac_used_full_shell=float(used_full.mean()),
        n_pareto=int(Pa.sum()),
        n_ideal_region=int(ideal.sum()),
        n_hiC_loG=int(hiC_loG.sum()), n_hiC=int((C > 0.9).sum()),
        n_loL_loD=int(loL_loD.sum()), n_loL=int((Lv < np.percentile(Lv, 20)).sum()),
        candidate_source_counts=dict(Counter(r["candidate_source"] for r in rows)),
    )


def main():
    all_data = load_all()
    summary = {sid: summarize(d) for sid, d in all_data.items()}
    (DATA_DIR / "results_summary.json").write_text(json.dumps(summary, indent=1))
    print(f"{len(summary)} snapshots summarized -> data/results_summary.json\n")
    hdr = f"{'snapshot':40} {'n':>5} {'C_mean':>7} {'G_mean':>7} {'L_mean':>9} {'D_mean':>7} {'D_max':>6} {'r(C,G)':>7} {'r(L,D)':>7} {'n_ideal':>8} {'n_pareto':>8}"
    print(hdr)
    for sid, s in summary.items():
        rcg = f"{s['corr_C_G']:.2f}" if s['corr_C_G'] is not None else "n/a"
        rld = f"{s['corr_L_D']:.2f}" if s['corr_L_D'] is not None else "n/a"
        print(f"{sid:40} {s['n']:5d} {s['C']['mean']:7.3f} {s['G']['mean']:7.4f} {s['L']['mean']:9.6f} "
              f"{s['D']['mean']:7.3f} {s['D']['max']:6.3f} {rcg:>7} {rld:>7} {s['n_ideal_region']:8d} {s['n_pareto']:8d}")


if __name__ == "__main__":
    main()
