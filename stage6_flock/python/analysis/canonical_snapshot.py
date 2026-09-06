"""Phase 2B: build and save the canonical snapshot per PROTOCOL_V1.md section 3."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import numpy as np

from flock_sim.simulation import run_simulation
from flock_sim.lattice import Lattice
from analysis.baseline_characterization import find_qualifying_t0  # reuse exact frozen rule
from flock_sim.model import rotate_cw

SEED = 2
NT_TOTAL = 100


def main():
    lattice = Lattice(nn=100, nh=8)
    res = run_simulation(nn=100, nt=NT_TOTAL, seed=SEED, lattice=lattice)
    q = find_qualifying_t0(res.z_hist[:61])  # exactly reproduce the nt_search=60 discovery window
    assert q is not None, "canonical seed no longer qualifies -- protocol assumption violated"
    t0, I0, h0 = q["t0"], np.array(q["I0"]), q["h0"]
    assert t0 == 41 and h0 == 2 and len(I0) == 20, f"mismatch vs PROTOCOL_V1.md: t0={t0} h0={h0} n={len(I0)}"
    h_star = rotate_cw(h0)  # genuine 90-degree turn (see model.ROT_CW)

    out_dir = Path(__file__).resolve().parents[2] / "data" / "protocol_v1"
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_dir / "canonical_snapshot.npz",
        z_hist_full=res.z_hist,
        I0=I0,
        t0=t0,
        h0=h0,
        h_star=h_star,
        seed=SEED,
    )
    meta = dict(seed=SEED, t0=int(t0), h0=int(h0), h_star=int(h_star), I0=I0.tolist(),
                size=len(I0), nt_total=NT_TOTAL,
                eigengap=q["eigengap"], coherence=q["coherence"])
    with open(out_dir / "canonical_snapshot_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
