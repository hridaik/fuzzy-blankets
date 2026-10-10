# EVALUATION (Part C) — held-out pool, run once after `freeze(hash)`
Frozen hash `2d2c9539...c44898` (monitor + rig + controller + run script + both configs); unchanged after the run (re-computed, identical). `freeze()` was called by `code/run_heldout.py`; the held-out pool then unlocked. Held-out seeds 6000-6067. Per dish 7 arms on the same seed: controller, CRN twin (no action), matched sham, random-location (same actuator/duration/pulse times, **dose per pulse equal to the controller's, disc centred on a random cell**), fixed (dev-learned: centre, r 1.5, 20 tu, amp 2.0, one pulse), whole-body same amplitude, whole-body dose-matched. Numbers: `logs/heldout_eval.json`, `logs/heldout_summary.jsonl`. All CIs: dish-clustered percentile bootstrap (5000), n = 60 dishes (30 per direction).
**Selection.** 68 dishes were drawn; 6 were skipped because their direction's quota (30) was already full (decided from the baseline state before any action) and 2 were excluded as `baseline_not_clean` (monitor reported V_body false before any action, i.e. natural false alarm). They have no arms. 428 held-out episodes were used, 122,124 dose.

## Headline table (mean [95 % CI])
| arm | success | V_body | persistence (target held at end) | dose (all dishes) | time first action -> target sustained (tu) | events |
|---|---|---|---|---|---|---|
| **controller** | **0.933 [0.867, 0.983]** | 0.983 [0.95, 1] | 0.950 [0.883, 1] | 266 [245, 289] | 71 [64, 79] | 0 |
| twin (no action) | 0 | 0.983 | 0 | 0 | - | 0 |
| sham | 0 | 0.983 | 0 | 0 | - | 0 |
| random location (dose matched) | 0.067 [0.017, 0.133] | 0.983 | 0.100 [0.03, 0.18] | 267 | 108 (n=4) | 0 |
| fixed (dev-learned) | **0.983 [0.95, 1.0]** | 0.983 | 1.0 | 259 [253, 265] | **38 [37, 40]** | 0 |
| whole body, same amplitude | 0.983 [0.95, 1.0] | 0.983 | 1.0 | **977 [903, 1059]** | 24 | 0 |
| whole body, dose matched | 0.017 [0, 0.05] | 0.983 | 0.017 | 266 | - | 0 |
V_body_conservative equals V_body in every arm. The single dish with V_body false is the same in every arm including the twin (natural cohesion fluctuation beyond the frozen bound, cf. dev seed 5014): **no arm caused an identity loss; 0 SPLIT/MERGE/EXTRUSION/LOSS/ARRIVAL events in 428 episodes.** That dish also fails the controller's and fixed arm's SUCCESS (which requires V_body_conservative), so excluding it, controller 55/59 = 0.93, fixed 59/59.
Controller by direction: S+ -> S- 0.933 [0.83, 1.0], S- -> S+ 0.933 [0.83, 1.0] (fixed 0.967 / 1.0). Controller dose to success 261 [240, 284]; probes (pulses) 2.4 [2.2, 2.6].
## Paired effects (dish level, vs the CRN twin and the matched sham)
Sham minus twin (progress toward the target at the end): 0.000 [0, 0] (the sham procedure does nothing, positions identical). Controller minus twin: success +0.933 [0.867, 0.983], end progress (|u| units; 1.56 = full state change) **+1.48 [1.38, 1.56]**; controller minus sham identical. Random minus twin: +0.067, +0.18 [0.05, 0.31]; fixed/whole minus twin: +0.983, +1.563.
## Selectivity (location) at matched dose, permutation (sign-flip over dishes, 20000)
* controller minus random: success **+0.867** (CI [0.77, 0.95], p < 5e-5), end progress +1.31 [1.15, 1.44]; realised dose ratio random/controller 1.003 [1.00, 1.01]. Random discs hold on average 6.2 cells (similar to the controller's ~6-7), so the difference is where, not how many.
* The dose-matched whole-body arm fails (0.017) too: at the controller's dose a whole-body dose is below its own threshold.
* **Controller minus fixed**: success -0.050 (CI [-0.117, 0], p = 0.25); dose +6.7 [-14, +29] (p = 0.55). **Controller minus whole-body**: success -0.050 (p = 0.25); the whole-body arm needs 3.68x [3.62, 3.75] the dose.
* Variance share of body-frame location in log dose* (development bisection B2, type-I sequential: duration, location, direction, dish): duration 0.20, **location 0.54**, direction 0.03, dish 0.11, residual 0.13.
## Failures of the controller (reported, not fixed)
4 of 60 `time_limit`: (a) 3 dishes (6026, 6027, 6042) where the frozen commit rule (progress >= 0.62 three tu after release) fired at 0.63-0.74, the response then relapsed, and un-commit only triggers 60 tu later, so the 330-tu limit was reached; (b) 1 dish (6040) reached the target but failed on the natural V_body false alarm. A higher commit level / faster un-commit would be the obvious fix (not applied: post-freeze). Budget: session used 1372/1500 episodes, 194,855/500,000 tu, 441,869/3.5e6 dose.

## Reading, by claim
* ESTABLISHED (held-out, paired, n=60): the controller durably changes the collective state (93 %, held 120 tu after the last action and at the end in 95 %) with body identity preserved (no events; V_body as good as the untreated twin); location matters (random placement at the same dose: 7 %).
* NOT ESTABLISHED / NEGATIVE: that the online controller **beats** the baselines. Against the dev-tuned fixed pulse it is not better (success -5 pp, n.s.; dose the same; slower: 71 vs 38 tu); it is much cheaper than the whole body (3.7x less dose at 93 vs 98 % success, n.s. difference) and much better than random placement. The fixed baseline was tuned on development dishes with the same dish-to-dish threshold spread (about x1.4) that bounds what adaptivity can gain.
* PROVISIONAL: one body per seed, both directions with one body type (24 cells); only O1 (the monitor is O1-only); one hold definition.
