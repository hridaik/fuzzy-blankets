# CONTROLLER (B3/B4) — `code/controller.py`, `CONTROLLER_CONFIG.json`, hash in `FROZEN_HASH.txt`

Closed loop: observe (O1 every 1 tu through the frozen monitor) -> locate body frame (centroid, signed major axis e1 from the c6 slope; e2 = rot90 e1) -> decide -> act -> monitor -> stop.
1. **Baseline 20 tu** with no action (monitor baseline for geometry/pattern). If the state is not sure or V_body fails: no action ("baseline_not_clean").
2. **Direction/actuator** from the state read at baseline: S+ -> L4, S- -> L3 (learned in B1; both are one-directional).
3. **Location**: body-frame origin (centroid), disc r = 1.5 (B2: cheapest location; head is 3-5x worse).
4. **Pulses**: 10 tu, 2.5-tu raised-cosine ramps, first amplitude 1.6, then x1.1 per pulse ("chain": consecutive short pulses accumulate, because sub-threshold excursions decay with a 10-45 tu half time; waiting 3 tu between pulses to read the response).
5. **Commit**: if the progress `dev = -sign(u0)(u - u0)` (u = c4-c5 level difference of the 10-tu median) is >= 0.62 three tu after release the controller stops acting and waits for the state to settle. **Un-commit** (resume pulses) if after 60 tu the progress falls back below 0.3.
6. **Abort** (no further action, episode ended, reported): any SPLIT/EXTRUSION/LOSS/ARRIVAL event, or V_body_now false for 3 consecutive decisions. (The first version aborted on the 95 % `geometry_warn`; this was a natural fluctuation and was removed on development data; a second change added the 3-decision persistence after the seed-5014 natural cohesion false alarm.)
7. **SUCCESS** at time t: >= **120 tu** after the end of the last action (hold; the monitor's detection latency is <= 1 tu, the state-change time after release up to ~82 tu, natural state lifetime > 5600 tu), the monitor reports the target state with posterior >= 0.99 in **every frame of the last 40 tu**, and V_body_conservative is true throughout. The same rule is applied to all arms.
Episode limits (frozen): <= 8 pulses, dose <= 1500 (server per-episode limit 20000), amplitude <= 6, time <= 330 tu (server 600), no new pulse after t = 170.
Every decision is logged with a reason string (`decisions` in the episode log).

## Development (12 dishes, 6 per direction; seeds 5006-5022; one dish (5014) excluded from the tables because its untreated twin also leaves the cohesion bound = natural V_body false alarm)
| policy | success | mean dose of successes |
|---|---|---|
| ctrl v1 (dur 20, amp 1 then gain-based escalation) | 11/11 | 408 |
| ctrl v3a (amp0 1.2, x1.15) | 9/11 | 304 |
| **ctrl v3b (frozen)** (amp0 1.6, x1.1) | 11/11 | 283 |
| ctrl v3c (amp0 1.9) | 11/11 | 283 |
| ctrl v3d (earlier commit 0.5) | 10/11 | 289 |
| fixed single pulse, dur 20, amp 1.4 / 1.7 / 2.0 / 2.4 | 7 / 10 / 11 / 11 of 11 | 188 / 221 / **258** / 310 |
Honest reading on development: the adaptive controller did **not** beat the best fixed pulse on dose (283 vs 258; the fixed pulse was tuned on the same 11 dishes, which favours it). The dish-to-dish spread of the threshold is only ~x1.4, so a one-shot pulse at the 90th-percentile amplitude is close to optimal and probing costs roughly what it saves. What closed-loop adds is: abort on identity loss, stopping after commitment, top-up for the hard dishes.
Selection of v3b among v3a-d was on the same 12 dishes (a development-pool choice, no held-out data).
