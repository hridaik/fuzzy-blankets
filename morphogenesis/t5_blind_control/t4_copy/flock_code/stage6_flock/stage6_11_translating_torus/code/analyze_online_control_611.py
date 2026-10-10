"""Stage 6.11 release/persistence analysis (task brief item 17).

Reads an `online_control_611__seed*.json` produced by `run_online_control_611.py`
and classifies the outcome:

  - "turned while externally forced": frac_interior_at_target rose during the
    control phase but decays back toward baseline (~0.25, chance level for 4
    headings) once released.
  - "entered a new self-maintaining translating state": frac_interior_at_target
    stays elevated through the release window on its own, with no
    intervention active.
  - "lost the collective": interior_size collapses toward 0 (dissolved)
    during control or release -- turning destroyed the thing rather than
    steering it.

Purely descriptive; does not feed back into any fitting/threshold/lineage
decision (task brief item 18's discipline applied to this stage's own
control outcome, not only to the oracle).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

CHANCE_LEVEL = 0.25


def analyze(path: Path) -> dict:
    result = json.loads(path.read_text())
    log = result["log"]
    control = [e for e in log if e["event"] == "control_step"]
    release = [e for e in log if e["event"] == "release_step"]

    out = dict(seed=result["seed"], ended_phase=result["ended_phase"], final_t=result["final_t"],
               n_control_steps=len(control), n_release_steps=len(release))

    if control:
        out["control_frac_at_target_start"] = control[0]["frac_interior_at_target"]
        out["control_frac_at_target_end"] = control[-1]["frac_interior_at_target"]
        out["control_interior_size_start"] = control[0]["interior_size"]
        out["control_interior_size_end"] = control[-1]["interior_size"]

    if release:
        release_fracs = [e["frac_interior_at_target"] for e in release if e["frac_interior_at_target"] is not None]
        release_sizes = [e["interior_size"] for e in release]
        out["release_frac_at_target_series"] = release_fracs
        out["release_interior_size_series"] = release_sizes
        out["release_frac_at_target_mean"] = float(np.mean(release_fracs)) if release_fracs else None
        out["release_frac_at_target_final"] = release_fracs[-1] if release_fracs else None
        out["release_interior_dissolved"] = any(s == 0 for s in release_sizes)

        control_gain = (out.get("control_frac_at_target_end", 0) or 0) - (out.get("control_frac_at_target_start", 0) or 0)
        out["control_turned"] = bool(control_gain > 0.1)  # forced phase actually raised alignment
        release_high = bool(release_fracs and
                             np.mean(release_fracs[-max(1, len(release_fracs) // 3):]) > CHANCE_LEVEL + 0.15)

        if out.get("release_interior_dissolved"):
            classification = "lost the collective"
        elif not out["control_turned"]:
            classification = "actuation never turned it (control phase itself failed)"
        elif release_high:
            classification = "entered a new self-maintaining translating state"
        else:
            classification = "turned while externally forced, reverted on release"
        out["classification"] = classification
    else:
        out["classification"] = "no release phase reached (" + result["ended_phase"] + ")"

    return out


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if path is None:
        from common_611 import DATA_DIR
        path = DATA_DIR / "online_control_611__seed500.json"
    report = analyze(path)
    print(json.dumps(report, indent=2, default=str))
