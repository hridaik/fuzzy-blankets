"""v3 tab9 data prep: Closure A organizational-role class comparison. Pure
re-export of final_translating_flock_closure/data/closure_analysis_summary.json
(closureA section) + state manifest class-availability table."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CLOSURE_DATA = ROOT / "final_translating_flock_closure" / "data"
OUT = Path(__file__).resolve().parents[2] / "data" / "tab9_organizational_roles.json"


def main():
    analysis = json.load(open(CLOSURE_DATA / "closure_analysis_summary.json"))
    avail = json.load(open(CLOSURE_DATA / "closureAB_class_availability.json"))
    actuator_summary = json.load(open(CLOSURE_DATA / "closureAB_actuator_summary.json"))

    out = dict(
        closureA=analysis["closureA"],
        class_availability=avail,
        actuator_summary=actuator_summary,
        n_rollouts=analysis["n_rollouts_AB"],
        provenance=dict(
            source="final_translating_flock_closure/data/closureAB_*.json + closure_analysis_summary.json",
            method="final_translating_flock_closure/EXPERIMENT_PROTOCOL.md, ORGANIZATIONAL_ROLE_RESULTS.md",
        ),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
