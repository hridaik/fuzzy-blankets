# COMPUTE_PLAN (declared before Part A/B)
Confirmed caps (status()): session 1500 episodes, 500000 tu, dose 3.5e6; per episode 600 tu, 20000 dose, 20 actions. Pool dev seeds 5000-5399 (400).
Throughput ~60 tu/s wall => wall-clock is negligible (<<24 h); offline Part A is CPU-bound on 8 cores.
Already used (smoke): 3 episodes, 30 tu, dose 6 (dev).
## Allocation (episodes / tu)
| phase | episodes | tu |
|---|---|---|
| B1 safe-probe sysid (5 actuators x doses x durations x locations, with sham) | <=450 | <=130k |
| B2 threshold search per direction | <=250 | <=100k |
| B3 controller tuning/dev trials | <=150 | <=60k |
| reserve (dev) | 50 | 20k |
| Part C held-out: 30 dishes/direction x 6 arms (controller, twin, sham, random, fixed, whole) | 360 (+ <=40 spare) | <=180k |
Total <= ~1300 episodes, <=490k tu. Held-out episode/tu reserve is kept untouched until freeze().
Episode limits for controller (to be frozen): max episodes length 500 tu, max 8 probes, max dose set after B1 (<=5000).
Part A is offline (no budget). All usage reported in EVALUATION.md from the per-episode logs.

## Actual usage (final status() of the session)
Episodes 1372 / 1500 (development ~944: smoke 6, B1 ~420 incl. seed scans, B2 360 (+90 stage-3 inside B1), B3 ~150; held-out 428 = 60 dishes x 7 arms + 6 quota skips + 2 baseline-not-clean), simulated time 194,855 / 500,000 tu, dose 441,869 / 3.5e6 (held-out 122,124). Wall-clock: ~4.5 h from first live call (new-seed reset ~15 s dominates). Offline Part A: ~15 min of CPU on 8 cores. All within the 24 h cap.
