# SYSID (B1/B2) — live, development pool only (seeds 5000-5039; held-out pool locked until freeze)

All numbers from `logs/b1_results.jsonl` (stages 1,2a,2b,3), `logs/b2_results.jsonl` (bisection), episode logs in `episodes/`. Effect measured by the frozen-config monitor (draft file identical) at 1-tu sampling for 90 tu after release, against the **CRN twin**: with the same seed the no-action trajectory is identical to the pre-action probe trajectory (positions identical to 1e-12 in the CRN check, sham positions identical to the twin; the sham logs dose 0). Natural state changes never occur, so any state change is caused by the probe.

## B1 actuator classification (centre of the body, r = 1.5, 10 tu, amp 1/5/25; one S+ and one S- dish)
| channel | effect | class |
|---|---|---|
| L1 | none at dose 60/300; at amp 25 (dose 1500): SPLIT, cohesion destroyed | no effect -> **damaging** at high dose |
| L2 | pattern change from amp 1 (pat dz 10-20); SPLIT at amp >= 5 | persistent change of PATTERN, then **damaging** |
| L3 | S- -> S+ (flips at amp 5, dose 300; amp 25 also, no damage). On an S+ dish: nothing | **persistent state change, one direction (to S+)** |
| L4 | S+ -> S- (flips at amp 5; amp 25 also no damage). On an S- dish: nothing | **persistent state change, one direction (to S-)** |
| L5 | pattern change from amp 1; EXTRUSION/SPLIT at amp >= 5 | pattern change then **damaging** |
No transient-only actuator was found at these doses; sub-threshold L3/L4 pulses produce a transient excursion of u that decays (recovery 10-45 tu).
## B2 L3/L4: dose-response, location, duration (4 dishes, 288 + 360 + 90 episodes, **0 identity events, 0 material/geometry violations in all L3/L4 episodes; pattern z max 11.5 in a few L4 episodes**)
* **Threshold-like dose-response**: below threshold the excursion (peak of u) grows ~linearly with amp x dur and fully recovers; above it the dish goes to the other state (umax_dev 1.5-1.6 = the whole separation). Flip/no flip is highly reproducible within a dish and shifts by about x1.4 between dishes (5001/5002 easier than 5004/5005).
* **Minimum effective duration**: 2 tu never flips (amp up to 80); 5 tu needs 3-4x the dose; **>= 10 tu** the integrated drive amp x dur needed is constant (centre: 28-47 at 10 tu, 21-34 at 20 tu, 22-30 at 40 tu) and dose* (= amp x dur x cells, bisection resolution x1.4) is minimal at 20-40 tu.
* **Dose by body-frame location (r = 1.5, dose* geometric mean, 20-40 tu)**: centre ~165-205; side (q = +1.5) 180-290; tail (p = -3) 320-340; **head (p = +3) 575-1000 (3-5x centre)**; whole body (24 cells, amp x dur 9-13) 250-320. Per-cell efficiency is higher where the body is thin and lower at the head; with small discs (r = 0.8, 1-4 cells) the excursion per unit dose is about constant (1.7-4.9 per 1000 dose), i.e. location matters mostly through coverage and a head-ward penalty.
* **Direction**: L4 (to S-) needs ~15 % less dose than L3 (to S+) at the centre (165-175 vs 195-205).
* Variance share (type-I, log dose*, B2): see `logs/heldout_eval.json` -> `dose_variance_share_dev_B2` (duration, location, direction, dish).
* **Response slowing as an online cue (tested, NEGATIVE)**: half-recovery time after a sub-threshold probe rises with peak excursion (10 tu at 0.15-0.3, 18 at 0.45-0.6, 44 at 0.75-1.0; Spearman 0.78) — slowing is real. But for predicting the remaining gap to the threshold (log of dose*/applied) leave-one-dish-out R2 is 0.44 from the peak alone and **0.37-0.42 when the slowing features are added**: the cue carries no information beyond the excursion size. Not used by the controller (`use_cue: false`).
* A single threshold on the excursion at release+8 tu classifies flip vs no flip with 0.91 accuracy only; the point of no return is not a fixed value of u (history-dependent), so the controller waits and can un-commit.
