"""Runs the remaining Octave-heavy batches SEQUENTIALLY (one at a time, per
the compute policy's parallelism-within-a-batch-not-across-batches norm
this session has followed), in dependency order:
  1. Part A rescue (needs nothing beyond the engine)
  2. Part C kicks (needs Part B census final states)
  3. Part D SUSTAINED twins (needs nothing beyond the engine, but run after
     kicks to avoid overlapping with it)
  4. Part D withdrawal (DEV-SHORT/DEV-LONG/ADULT; ADULT needs Part B census)
  5. Part E sham (needs Part D's SUSTAINED-DH twins)
Each step's own script already parallelizes across 8 cores internally; this
orchestrator just sequences the steps and logs progress.
"""
import json
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(REPO_ROOT, "code")
LOG_DIR = "/tmp"


def wait_for_census():
    """BUGFIX (caught this session): must count only real per-individual
    result files, not leftover '_vinit.mat' temp files that
    fallback_engine.run()'s v_override path never cleans up -- those
    inflated the count and triggered this function (and hence Part A) ~18
    secondary individuals early, causing real CPU contention between
    run_census.py and run_rescue.py. See COMPUTE_PLAN.md's addendum."""
    census_dir = os.path.join(REPO_ROOT, "data", "census")
    while True:
        n = len([f for f in os.listdir(census_dir)
                 if (f.startswith("primary_") or f.startswith("secondary_"))
                 and f.endswith(".mat") and "_vinit" not in f])
        if n >= 250:
            return
        time.sleep(60)


def run_step(name, cmd, log_name):
    print(f"=== starting {name} at {time.strftime('%H:%M:%S')} ===", flush=True)
    t0 = time.time()
    with open(os.path.join(LOG_DIR, log_name), "w") as f:
        result = subprocess.run(cmd, cwd=REPO_ROOT, stdout=f, stderr=subprocess.STDOUT)
    elapsed = time.time() - t0
    print(f"=== {name} finished in {elapsed:.1f}s, returncode={result.returncode} ===", flush=True)
    return result.returncode == 0


if __name__ == "__main__":
    print("Waiting for census (250 individuals) to complete...", flush=True)
    wait_for_census()
    print("Census complete. Starting orchestrated sequence.", flush=True)

    ok = run_step("Part A rescue", [sys.executable, "code/run_rescue.py"], "m1_orch_rescue.log")
    ok2 = run_step("Part C kicks", [sys.executable, "code/run_kicks.py"], "m1_orch_kicks.log")
    ok3 = run_step("Part D SUSTAINED twins", [sys.executable, "code/run_withdrawal.py", "--which", "sustained"], "m1_orch_sustained.log")
    ok4 = run_step("Part D withdrawal", [sys.executable, "code/run_withdrawal.py", "--which", "withdrawal"], "m1_orch_withdrawal.log")
    ok5 = run_step("Part E sham", [sys.executable, "code/run_sham.py"], "m1_orch_sham.log")

    summary = {"rescue": ok, "kicks": ok2, "sustained": ok3, "withdrawal": ok4, "sham": ok5}
    print("SEQUENCE COMPLETE:", summary, flush=True)
    with open(os.path.join(REPO_ROOT, "data", "orchestrate_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
