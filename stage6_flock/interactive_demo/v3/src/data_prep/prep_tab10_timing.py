"""v3 tab10 data prep: Closure C timing-susceptibility check. Pure re-export
of closure_analysis_summary.json's closureC section + the onset
class-availability table (shows live-edge topology change over time)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CLOSURE_DATA = ROOT / "final_translating_flock_closure" / "data"
OUT = Path(__file__).resolve().parents[2] / "data" / "tab10_timing.json"


def main():
    analysis = json.load(open(CLOSURE_DATA / "closure_analysis_summary.json"))
    onset_summary = json.load(open(CLOSURE_DATA / "closureC_timing_onset_summary.json"))

    out = dict(
        closureC=analysis["closureC"],
        onset_summary=onset_summary,
        n_rollouts=analysis["n_rollouts_C"],
        provenance=dict(
            source="final_translating_flock_closure/data/closureC_timing_*.json + closure_analysis_summary.json",
            method="final_translating_flock_closure/EXPERIMENT_PROTOCOL.md, TIMING_SUSCEPTIBILITY.md",
        ),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
