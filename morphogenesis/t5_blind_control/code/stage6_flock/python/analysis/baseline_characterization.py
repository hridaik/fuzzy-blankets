"""Phase 2 / 2A: baseline characterization run BEFORE any control experiment.
No control outcomes are consulted anywhere in this script. Produces the raw
material for PROTOCOL_V1.md's frozen thresholds.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import numpy as np

from flock_sim.simulation import run_simulation
from flock_sim.spectral import analyze_window, jaccard
from flock_sim.metrics import coherence, polarization, target_heading_fraction, modal_heading
from flock_sim.model import rotate_cw

TW = 5
NN = 100
NT = 60
N_REPLICATES = 300
EIGENGAP_MIN = 1.0
COHERENCE_MIN = 0.90
N_MIN, N_MAX = 10, 30
JACCARD_MIN = 0.6
STABILITY_STEPS = 3  # require the rule to hold at t, t+1, t+2


def find_qualifying_t0(z_hist: np.ndarray) -> dict | None:
    nt_plus1 = z_hist.shape[0]
    candidates = []
    for t in range(TW - 1, nt_plus1 - STABILITY_STEPS):
        ok = True
        info_list = []
        for dt in range(STABILITY_STEPS):
            tt = t + dt
            window = z_hist[tt - TW + 1: tt + 1]
            if window.shape[0] < TW:
                ok = False
                break
            sr = analyze_window(window)
            if sr.eigengap < EIGENGAP_MIN:
                ok = False
                break
            # try both core1 and core2 as candidate interior; take whichever
            # satisfies coherence/size (paper doesn't distinguish a priori which
            # side is "the" flock -- both are valid macro-agent candidates).
            found_side = None
            for side_nodes in (sr.core1_nodes, sr.core2_nodes):
                if N_MIN <= len(side_nodes) <= N_MAX and coherence(z_hist[tt], side_nodes) >= COHERENCE_MIN:
                    found_side = side_nodes
                    break
            if found_side is None:
                ok = False
                break
            info_list.append((tt, found_side, sr))
        if not ok:
            continue
        # lineage stability across the STABILITY_STEPS window (consecutive Jaccard)
        stable = True
        for k in range(len(info_list) - 1):
            j = jaccard(info_list[k][1], info_list[k + 1][1])
            if j < JACCARD_MIN:
                stable = False
                break
        if not stable:
            continue
        t0, I0, sr0 = info_list[0]
        h0 = modal_heading(z_hist[t0][I0], nu=4)
        candidates.append(dict(t0=int(t0), I0=I0.tolist(), h0=int(h0),
                                eigengap=float(sr0.eigengap), size=len(I0),
                                coherence=float(coherence(z_hist[t0], I0))))
        return candidates[0]  # FIRST qualifying time only, per protocol (no cherry-picking)
    return None


def main():
    rows = []
    n_found = 0
    for seed in range(N_REPLICATES):
        res = run_simulation(nn=NN, nt=NT, seed=seed)
        q = find_qualifying_t0(res.z_hist)
        if q is None:
            rows.append(dict(seed=seed, found=False))
            continue
        n_found += 1
        t0, I0, h0 = q["t0"], np.array(q["I0"]), q["h0"]
        h_star = rotate_cw(h0)  # genuine 90-degree turn; see model.ROT_CW docstring
        row = dict(seed=seed, found=True, t0=t0, h0=h0, size=q["size"],
                   eigengap=q["eigengap"], coherence=q["coherence"])
        for Tu in (10, 20, 30, 40):
            end = t0 + Tu
            if end < res.z_hist.shape[0]:
                row[f"Hstar_spontaneous_Tu{Tu}"] = target_heading_fraction(res.z_hist[end], I0, h_star)
                row[f"coherence_h0_Tu{Tu}"] = coherence(res.z_hist[end], I0)
            else:
                row[f"Hstar_spontaneous_Tu{Tu}"] = None
                row[f"coherence_h0_Tu{Tu}"] = None
        rows.append(row)

    out_dir = Path(__file__).resolve().parents[2] / "data" / "baseline_v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "baseline_rows.json", "w") as f:
        json.dump(rows, f, indent=1)

    found_rows = [r for r in rows if r["found"]]
    print(f"N_REPLICATES={N_REPLICATES}  qualifying_t0_found={n_found} ({100*n_found/N_REPLICATES:.1f}%)")
    if found_rows:
        t0s = np.array([r["t0"] for r in found_rows])
        sizes = np.array([r["size"] for r in found_rows])
        gaps = np.array([r["eigengap"] for r in found_rows])
        cohs = np.array([r["coherence"] for r in found_rows])
        print(f"t0: mean={t0s.mean():.1f} median={np.median(t0s):.1f} min={t0s.min()} max={t0s.max()}")
        print(f"|I0|: mean={sizes.mean():.1f} median={np.median(sizes):.1f} min={sizes.min()} max={sizes.max()}")
        print(f"eigengap: mean={gaps.mean():.2f} median={np.median(gaps):.2f} min={gaps.min():.2f}")
        print(f"coherence: mean={cohs.mean():.3f} min={cohs.min():.3f}")
        for Tu in (10, 20, 30, 40):
            vals = np.array([r[f"Hstar_spontaneous_Tu{Tu}"] for r in found_rows if r[f"Hstar_spontaneous_Tu{Tu}"] is not None])
            if len(vals) == 0:
                print(f"Tu={Tu}: no complete data (ran past nt)")
                continue
            frac_high = np.mean(vals >= 0.8)
            print(f"Tu={Tu}: n={len(vals)} mean_Hstar_spontaneous={vals.mean():.3f} "
                  f"P(Hstar>=0.8 spontaneously)={frac_high:.3f}")


if __name__ == "__main__":
    main()
