"""Part 14 verification: independently recompute every scenario bundle's
`summary` fields from its raw arrays (trajectory/metrics/control), and
confirm they match what export_scenarios.py embedded. Catches arithmetic
bugs in the exporter without re-running the simulator. Run:

    python3 verify_bundles.py
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent


def dwell_min_crossing(series, threshold, dwell, start, end):
    n = len(series)
    for t in range(start, min(end, n - dwell) + 1):
        if all(series[t + j] >= threshold for j in range(dwell)):
            return t
    return None


def verify(bundle: dict) -> list[str]:
    problems = []
    tl = bundle["timeline"]
    m = bundle["metrics"]
    s = bundle["summary"]

    success = m["Hstar"][tl["control_end"]] >= 0.8
    if success != s["success"]:
        problems.append(f"success mismatch: recomputed={success} stored={s['success']}")

    persistent = m["Hstar"][tl["release_end"]] >= 0.5
    if persistent != s["persistent"]:
        problems.append(f"persistent mismatch: recomputed={persistent} stored={s['persistent']}")

    peak = max(m["n_actuators_t"]) if any(m["n_actuators_t"]) else 0
    if peak != s["peak_actuators"]:
        problems.append(f"peak_actuators mismatch: recomputed={peak} stored={s['peak_actuators']}")

    bird_steps = sum(m["n_actuators_t"])
    if bird_steps != s["bird_steps"]:
        problems.append(f"bird_steps mismatch: recomputed={bird_steps} stored={s['bird_steps']}")

    override_count = sum(sum(row) for row in bundle["control"]["overridden"])
    if override_count != s["override_count"]:
        problems.append(f"override_count mismatch: recomputed={override_count} stored={s['override_count']}")

    t_rec = dwell_min_crossing(m["coherence"], 0.8, 3, tl["control_start"], tl["release_end"])
    if t_rec != s["recovery_time_abs"]:
        problems.append(f"recovery_time_abs mismatch: recomputed={t_rec} stored={s['recovery_time_abs']}")

    t_hit = dwell_min_crossing(m["Hstar"], 0.8, 3, tl["control_start"], tl["release_end"])
    if t_hit != s["time_to_target_dwell3_abs"]:
        problems.append(f"time_to_target_dwell3_abs mismatch: recomputed={t_hit} stored={s['time_to_target_dwell3_abs']}")

    # Cross-check gamma2 against a direct per-timestep recount at the control-start timestep
    # (control window's own Gamma2 metric should equal the static summary value, since all
    # current bundles use a fixed actuator set for the whole window, not a staged schedule).
    if tl["control_end"] > tl["control_start"]:
        mid_gamma2 = m["double_coverage"][tl["control_start"]]
        if abs(mid_gamma2 - s["gamma2"]) > 1e-9:
            problems.append(f"gamma2 (fixed-set assumption) mismatch: metrics={mid_gamma2} summary={s['gamma2']}")

    return problems


def main():
    files = sorted(DATA_DIR.glob("seed*__*__*.json"))
    assert files, "no scenario bundles found -- run export_scenarios.py first"
    n_ok, n_bad = 0, 0
    for f in files:
        bundle = json.loads(f.read_text())
        problems = verify(bundle)
        if problems:
            n_bad += 1
            print(f"FAIL {f.name}:")
            for p in problems:
                print("   -", p)
        else:
            n_ok += 1
    print(f"\n{n_ok} bundles verified OK, {n_bad} with mismatches, out of {len(files)} total.")
    assert n_bad == 0, "verification failed -- see mismatches above"


if __name__ == "__main__":
    main()
