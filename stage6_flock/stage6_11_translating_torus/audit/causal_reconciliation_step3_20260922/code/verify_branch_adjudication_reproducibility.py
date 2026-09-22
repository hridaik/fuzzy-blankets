"""Task F0/E prerequisite: verify branch_adjudication_611.run_seed is
exactly reproducible (deterministic given its own fixed internal seeds),
by re-running it for one seed and diffing every readout against the
already-persisted audit/branch_adjudication_611__seed{seed}.json to
floating-point tolerance 1e-9.

This does not modify branch_adjudication_611.py -- imported and called
unmodified. Expensive (the four repaired-authority/beam-search branches
each run N_ROLLOUTS_REPAIRED Monte Carlo rollouts); ~25-30+ CPU-minutes
per seed in this environment, which is why this was only run for seed 501
in this pass (see COUNTERFACTUAL_MATERIAL_TRACES.md for the disclosed
scope limitation).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

AUDIT_DIR = Path(__file__).resolve().parents[2]
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(AUDIT_DIR))
sys.path.insert(0, str(CODE_DIR))

import branch_adjudication_611 as BA  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"


def verify(seed: int):
    trig = json.load(open(AUDIT_DIR / "trigger_states_611.json"))[str(seed)]
    mf = ROC.make_flock()
    t0 = time.time()
    out = BA.run_seed(seed, trig, mf)
    elapsed = time.time() - t0
    saved = json.load(open(AUDIT_DIR / f"branch_adjudication_611__seed{seed}.json"))

    mismatches = []
    for name in out["branches"]:
        a = out["branches"][name]["readouts"]
        b = saved["branches"][name]["readouts"]
        for k in a:
            va, vb = a[k], b[k]
            if va is None and vb is None:
                continue
            if va is None or vb is None or abs(va - vb) > 1e-9:
                mismatches.append(dict(branch=name, field=k, rerun=va, saved=vb))

    result = dict(seed=seed, elapsed_seconds=elapsed, n_mismatches=len(mismatches),
                  mismatches=mismatches,
                  status="REPRODUCED_EXACTLY" if not mismatches else "MISMATCH")
    json.dump(result, open(OUT / f"branch_adjudication_reproduction_seed{seed}.json", "w"), indent=2, default=str)
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 501
    verify(seed)
