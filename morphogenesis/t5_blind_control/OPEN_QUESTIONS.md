# OPEN QUESTIONS / deviations
## Deviations from the brief
1. **Calibration/validation** of Part A used dev natural bodies split by body id (2100-2105 / 2106-2111); the package's 12 heldout_bodies natural runs were featurised (`logs/nat_feats.npz` contains them) but not analysed pre-freeze and **not analysed at all** afterwards either (NOT DONE).
2. The monitor is **O1 only**; O2/O3c state/identity monitoring and O2/O3c event tests are NOT DONE (tracker/detection spot checks only). The live controller used O1.
3. Pre-freeze B1/B2 used `MONITOR_CONFIG_draft.json` (numerically identical to the frozen `MONITOR_CONFIG.json`; code identical) because the probes were run before the freeze file was written; **no controller decision depended on it before the freeze**, but the sysid numbers did.
4. B3 controller selection among v3a-d, the fixed amplitude (2.0) and the abort rule (two development-driven changes) were made on the same 12 development dishes (6 per direction); development seeds 5000-5039 were reused many times.
5. A fixed amplitude/duration was chosen for the fixed baseline from the development panel (smallest amplitude with >= 90 % success).
6. `run_heldout.py` was dry-run once on the development pool before the freeze (2 dishes, 14 episodes) to catch bugs; the evaluation script had a reporting bug (missing `u_end` for the controller rows) fixed after the held-out run; it is reporting-only and not in the frozen hash.
7. The exemplar picks use the pre-declared rule (code/build_pages.py header); for S- the random pick coincided with the best dish (seed 6000).
8. Throughput ~60 tu/s, but a first `reset` of a new seed takes ~15 s (cached afterwards), so wall time was ~3 h; budget declared in COMPUTE_PLAN.md.
## Open scientific questions
* Why does the head region need 3-5x the dose of the centre and the whole body only ~1.5x? Per-cell sensitivity maps with single-cell masks were not done.
* The threshold is a function of the history (a fixed point of u is not a point of no return): what is the hidden slow variable? (flip/no flip prediction from the early response: 0.91 accuracy).
* Can the dish-specific threshold be predicted before acting (body size, pose) to let the controller save dose over the fixed pulse? Between-dish spread was only x1.4 and unexplained.
* L1, L2, L5: only screened at one location; only L3/L4 characterised. A transient-only actuator was not found.
* Are the two states mirror partners (c4/c5 and dipole swap together) or two organisations? Light flips all of c4, c5 and the dipole together while the geometry/material do not change: consistent with "same body, other collective state".
* Anticipation/directed influence: no natural changes exist to anticipate; influence tiny.
* The monitor's natural V_body false-alarm rate (~2.7 % per 600 tu on validation bodies; 2 of 68 held-out dishes at baseline plus 1 of 60 later) caps any SUCCESS that requires V_body_conservative at ~95-97 %.
