# OPEN_QUESTIONS.md

Final list, all Tier-1 parts complete.

1. **Tier 2 (Friston 2015 Figure 5 interpretations) was not run.**
   `COMPUTE_PLAN.md` prioritized the Tier-1 Kuchling battery given the
   session's compute budget; the withdrawal/sham infrastructure built this
   session (on/off ramp mechanism, sham field) is directly reusable for
   Tier 2 in a follow-up.
2. **Belief-concentration relaxation after kicks** (Part C) was only fit
   for free energy, not tracked as a genuinely separate hidden-tier
   belief-concentration curve, despite the task asking for both
   "separately." A real, disclosed scope gap.
3. **`TYPE_MISMATCH_PENALTY=3.0`** (`code/analysis.py`) is a pragmatic,
   declared constant, not derived from census data. Caught and fixed a
   real bug this session (an earlier unconstrained-penalty version blew up
   to ~125000 when a perturbed cell's expression code didn't clearly match
   any canonical type). Future stages should treat it as a declared
   analysis parameter.
4. **Part E sham was matched to DH's RMS distortion only**, not separately
   to DT/AN (`COMPUTE_PLAN.md`'s declared reduction) — used as a single
   shared floor for all three. Given DH/DT/AN all showed identical (0%)
   durable-effect rates and the sham also showed 0%, this did not end up
   mattering for this stage's conclusions, but a DT/AN-specific sham was
   never built.
5. **Role-relabeling tally for the 180 REVERTED withdrawal runs** was not
   separately tabulated beyond the role-swap-invariant `d_pair` metric
   itself (which would not distinguish "reverted with the same roles" from
   "reverted to an equivalent but relabeled configuration"). Low priority
   given the homogeneity already established, but a genuine completeness
   gap — flagged in `WITHDRAWAL.md`.
6. **The single-attractor and universal-reversion findings were established
   for ONE target template (the 8-cell `L=2` template) and ONE
   perturbation family (Kuchling 2020's positional-sensation distortions).**
   Whether they generalize to the 16-cell template, other perturbation
   families (e.g. Friston 2015's sensitivity scalings, Pio-Lopez 2022's
   precision manipulations — both catalogued but not executed in m0c/this
   stage), or other developmental windows is genuinely open.
7. **A real orchestration bug** (`_vinit.mat` temp-file miscounting causing
   ~17 minutes of Part A/B compute contention) was caught and fixed
   mid-session — disclosed in `COMPUTE_PLAN.md`, did not invalidate any
   result, but is a reminder that file-count-based progress checks need
   care when the underlying engine (m0c's `fallback_engine.py`, imported
   unmodified) leaves temp files behind.
8. **No live-browser rendering test** of the extended viewer (image panel)
   was performed in this headless session — only structural checks
   (placeholder substitution, byte-size limits). Same gap as m0c's
   `VIEWER.md`, inherited and not re-verified here.
9. **Whether the model's single attractor is a genuine free-energy global
   minimum or a very strong but not-unique local minimum** was not tested
   — this stage's kicks (up to 1.5× neighbour spacing, full belief resets)
   are substantial but not exhaustive; a systematic basin-of-attraction
   mapping was explicitly out of scope (STOP conditions: no attractor
   census).
