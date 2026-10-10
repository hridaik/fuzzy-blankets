"""Batch driver: generates the full primary landscape (task brief section 25)
-- for seeds 2,3,4, the 5 regimes (no_control/shell_only/same_direction/
opposite/disordered) at f_E=1.0, control-end snapshot -- and saves each to
data/. Run in background; logs progress to logs/run_all_snapshots.log."""
from __future__ import annotations

import json
import time
from pathlib import Path

from common_66 import PRIMARY_SEEDS
from archetypes import CONDITIONS
from run_landscape import run_snapshot, save_snapshot, DATA_DIR, LOG_DIR

N_CANDIDATES = 5000


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "run_all_snapshots.log"
    manifest = []
    t_start = time.time()
    with open(log_path, "a") as logf:
        logf.write(f"\n=== run_all_snapshots start {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        logf.flush()
        idx = 0
        for seed in PRIMARY_SEEDS:
            for condition in CONDITIONS:
                idx += 1
                rng_seed = seed * 1000 + CONDITIONS.index(condition)
                t0 = time.time()
                try:
                    result = run_snapshot(seed, condition, N_CANDIDATES, f_E=1.0,
                                           rng_seed=rng_seed, verbose=False)
                    save_snapshot(result, DATA_DIR)
                    elapsed = time.time() - t0
                    line = (f"[{idx}/15] seed={seed} condition={condition} "
                            f"n_unique={result['meta']['n_candidates_unique']} "
                            f"elapsed={elapsed:.1f}s fits={result['meta']['cache_stats']['n_fits']}")
                    manifest.append(dict(seed=seed, condition=condition,
                                          snapshot_id=result["meta"]["snapshot_id"],
                                          n_candidates_unique=result["meta"]["n_candidates_unique"],
                                          elapsed_seconds=elapsed, status="ok"))
                except Exception as e:  # noqa: BLE001
                    elapsed = time.time() - t0
                    line = f"[{idx}/15] seed={seed} condition={condition} FAILED after {elapsed:.1f}s: {e!r}"
                    manifest.append(dict(seed=seed, condition=condition, status="failed", error=repr(e)))
                print(line)
                logf.write(line + "\n")
                logf.flush()
        total = time.time() - t_start
        logf.write(f"=== run_all_snapshots done, total {total:.1f}s ===\n")
    with open(DATA_DIR / "snapshot_manifest.json", "w") as f:
        json.dump(dict(manifest=manifest, total_elapsed_seconds=total, n_candidates_target=N_CANDIDATES),
                   f, indent=1)
    print(f"DONE total={total:.1f}s")


if __name__ == "__main__":
    main()
