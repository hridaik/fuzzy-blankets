"""Part B driver (Hard Gate B). B1/B2 seed scan -> B3/B4 four-controller
comparison on qualifying flocks -> B6 aggregation -> B7 exploratory
correlations. Writes data/discriminating_flocks.json and
data/four_controller_comparison.json.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

CODE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_DIR))

from seed_scan import scan  # noqa: E402
from four_controller_compare import compare_all  # noqa: E402
from aggregate import summarize  # noqa: E402
from inference_quality_vs_control import quality_vs_control  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def main():
    print("=== B1/B2: seed scan for discriminating flocks ===")
    scan_result = scan()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "discriminating_flocks.json", "w") as f:
        json.dump(scan_result, f, indent=1)
    print(f"\nScanned seeds {scan_result['scan_start']}-{scan_result['scan_end_inclusive']} "
          f"({scan_result['n_qualifying_flocks_scanned']} qualifying flocks found by find_flock), "
          f"{scan_result['n_discriminating']} discriminating: {scan_result['discriminating_seeds']}")

    seeds = scan_result["discriminating_seeds"]
    if not seeds:
        print("No discriminating flocks found -- stopping here, per B2's explicit instruction "
              "to report rather than loosen the criterion.")
        return

    print("\n=== B3/B4: four-controller comparison ===")
    rows = compare_all(seeds)
    with open(DATA_DIR / "four_controller_comparison.json", "w") as f:
        json.dump(dict(seeds=seeds, n_replicates=50, rows=rows), f, indent=1,
                   default=lambda o: o.tolist() if isinstance(o, np.ndarray) else o)
    print(f"\nWrote {DATA_DIR / 'four_controller_comparison.json'}")

    print("\n=== B6: aggregation ===")
    summary = summarize(rows)
    print(json.dumps(summary, indent=1))

    print("\n=== B7: inference quality vs. control (exploratory) ===")
    quality = quality_vs_control(rows)
    print(json.dumps({k: v for k, v in quality.items() if k != "raw"}, indent=1))

    with open(DATA_DIR / "aggregate_summary.json", "w") as f:
        json.dump(dict(summary=summary, quality_vs_control=quality), f, indent=1)
    print(f"\nWrote {DATA_DIR / 'aggregate_summary.json'}")


if __name__ == "__main__":
    main()
