# SITUS_CALIBRATION.md — Part S (S1–S4) and Gate S

Labels: ESTABLISHED / PROVISIONAL / NOT DONE. Control target: the chiral body's mirror switch L <-> R. All runs relational (positional channel OFF), 24 cells, seeded start ("maternal prepattern"). Code: `code/s1.py`, `s2.py`, `s3common.py`, `s3_ladder.py`, `s3_grad.py`, `s4.py`, `s4_refine.py`, `s4_long.py`; data: `data/s1_*.json`, `s2_geometry.json`, `s3_ladder.json`, `s3_grad.json`, `s4_*.json`.

## **GATE S: FAILED. The mirror switch is NOT AVAILABLE** — not with any physical actuator family (S3), and not with the declared fate-bias fallback (S4). Parts I and T3 were completed regardless.

## Diagnosis test (the review's hypothesis) — CONFIRMED
At log pi_prior = −10 the slowest non-neutral belief rate is 3.7e-5 per time unit; at the best stable setting (below) 3.9e-4. The rate equals k_mu·pi_prior (1.4·e⁻⁸ = 4.7e-4): off-slot logits (p_slot ≈ 3e-4) are held in place only by the prior, because the sensory gradient on a logit is proportional to its own belief. Sharp beliefs and fast relaxation are therefore in direct conflict (see S1). Pulses cannot change fates, they move cells and tear the body (S3).

## S1 plasticity operating point
Declared (before measuring): (a) seeded success for L and R, 8 draws each (all must succeed); (b) minimum orbit belief >= 0.85; (c) slowest NON-NEUTRAL belief relaxation rate from the Jacobian at L >= 1e-2 per time unit (the 3 rigid-motion zero modes and the n decoupled logit-mean modes at −k_mu·pi_prior were excluded); (d) spontaneous L<->R switching at sigma_x = sigma_c = 0.02 plus sigma_mu, rate bound < 1e-3 per time unit. Belief noise: the engine already supports additive Langevin noise on mu (`sig_mu`, same counter-based per-cell streams).

**Scan 1 — log pi_prior x seeded success (log pi_s = 2; `s1_forms.json`, `s1_rates.json`)**
| log pi_prior | success (16 starts) | min / median orbit belief | slowest non-neutral rate | unstable modes |
|---|---|---|---|---|
| −6 | 0/16 | 0.21 / 0.62 | −4.6e-4 (max Re +0.19) | 1 |
| −7 | 0/16 | 0.75 / 0.89 | −6.8e-4 | 1 (marginal, +1e-4) |
| **−8** | **14/16** | 0.75 / **0.965** | **−3.9e-4** | 1 (+4e-6, numerical-neutral) |
| −10 | (T2d: 16/16 at 8+8 draws) | 0.95–0.99 | −3.7e-5 | 1 (+3e-6) |
**Scan 2 — belief noise at log pi_prior = −8 (8 seeds × 3000 time units each, from L (even) / R (odd), classified every 20 units; `s1_switch_*.json`)**
| sigma_mu | spontaneous L<->R flips | frames in defect | fraction of frames in the start form |
|---|---|---|---|
| 0 | 0 | 25/1200 (2 %: the 2 non-assembling starts) | 0.979 |
| 0.03 | 0 | 472/1200 | 0.607 |
| 0.1 | 0 | 813/1200 | 0.323 |
| 0.3 | 0 | 1112/1200 | 0.073 |
Belief noise does not make the form switch; it dissolves the body (the restoring rate 4e-4 is too small to hold logits against even sigma_mu = 0.03). **Scan 3 (extra axis, declared): log pi_s ∈ {3,4,5} × log pi_prior ∈ {−5..−8}** (`s1_grid_*.json`): the slowest non-neutral rate stays 1e-5 … 7e-4 wherever the body is stable (e.g. (4,−7): 15/16 stable, 5.9e-4; (5,−6): 9/16, 9.7e-5); no setting approaches 1e-2.
**The single declared variant (D6): Fisher-preconditioned (natural-gradient) belief flow** `dmu = −k_mu·(centred dF_sens/dp) − k_mu·pi_prior·mu` (`Params.nat_grad`, off by default; SPM's own D-step is curvature-preconditioned). Result: it does not restore plasticity and destabilises the seeded bodies: success 0, 0, 0, 0, 2 /16 for log pi_prior = −2, −4, −6, −7, −8, up to 13 unstable modes (`s1_forms_ng.json`, `s1_rates_ng.json`). Reason (PROVISIONAL): the mixing cost is quadratic in the off-slot belief, so its p-space gradient is also proportional to p_slot; preconditioning removes the softmax saturation only for a perturbation that creates a linear error term.
**Choice (no setting meets (a)–(c) together):** log pi_s = 2, log pi_prior = −8, sigma_mu = 0 — the setting that maximises plasticity subject to stable, crisp seeded bodies. (a) 14/16 (not all), (b) median 0.965 but 0.754 in the worst start, (c) **3.9e-4, a factor 25 below the target — FAILS**, (d) 0 flips in 24 000 body-time units: rate < 1.25e-4 per time unit (95 % one-sided Poisson bound; no escape-barrier analysis). The belief relaxation time 1/3.9e-4 ≈ 2 600 time units makes the "0.5–4 × relaxation-time" duration grid of S3 impractical (10⁴ units, and an end-to-end gradient through it); **declared deviation:** durations were 20 and 80 time units (≈ 1–4 position-relaxation times, ramp 5, release 150 (S3 ladder), 100 (S3 gradient), 300–6 000 (S4)). The Gate-S durability criterion (10 × relaxation time ≈ 26 000 units, 10 noise seeds per direction) was therefore never needed.

**Durability finding that the review did not ask for (ESTABLISHED, `natural_pilot2.json`):** at the chosen operating point the UNPERTURBED body is not durable under the operating noise sigma_x = sigma_c = 0.02: it dissolves (fragmentation / loss of complete slots) at a median of **≈ 3 300 time units (L) and 3 200 (R)**; all of 60 bodies are intact at 1 600, about half at 3 200 (the 3 000-unit runs of Scan 2 stopped just before this). So the relevant durability criterion is not spontaneous L<->R switching (0 flips) but dissolution within ≈ 1.2 relaxation times; the Gate-S requirement "stay in the new form for 10 × the relaxation time" (≈ 26 000 units) could not be met by ANY form of this body under operating noise. Fast position fluctuations decorrelate in 14–20 time units (detrended), the slow body deformation in ≈ 150.

## S2 switch geometry — ESTABLISHED (`s2_geometry.json`, `code/s2.py`)
* Position-only rigid distance L vs R: **0.0** with or without reflections allowed (the 24 positions form a mirror-symmetric set).
* Best type-free L→R correspondence: **0 cells move, 8 cells change type** (the two body rows: slots 8–15, types 2↔3 across the ±y halves).
* Type-preserving correspondence: 0 type changes but **8 cells move (mean 0.67, max 3.0)**.
* **Confirmed:** the mirror switch is a pure exchange of the identities (types) of the 8 cells in the two body rows between the +y and −y halves, with no net displacement. The typed rigid distance between the forms is 0.667.

## S3 white-box search with physical actuators (deterministic, noise 0, operating point) — NEGATIVE
Families (illuminated cells only, raised-cosine ramps 5): secretion of signal k (k = 1…4, sign ±), receptor gain for signal k (k = 1…4, ±), migration gain (±). Patterns (body frame): discs of radius 1.5 at head, trunk +y, trunk −y, tail, mid; two discs on opposite sides with opposite signs; half-body +y; half-body −y. Durations 20, 80.
* **Forward ladder** (1728 runs, L→R direction only; amplitude ladder 0.25…8 × base (secretion 1, gain 0.3, migration 0.5)): **0 runs ended in R**; 828 stayed L, 887 DEFECT (fragmentation, extrusion or incomplete slots), 13 OTHER. By family: secretion 215 L / 545 DEFECT / 8 OTHER; receptor gain 457 L / 306 DEFECT / 5 OTHER; migration 156 L / 36 DEFECT. (`s3_ladder.json`.) Bisection of a switch threshold is moot (no switch to bracket); the L→DEFECT disruption threshold was not bisected (NOT DONE).
* **Gradient search** (JAX reverse-mode through the full forcing + release trajectory, remat; 3 families × 6 patterns × 2 durations = 36 optimisations, 10 Adam steps, loss = code mismatch to the R fates + rigid-invariant shape penalty + dose): for receptor gain and migration the gradient is 1e-3–3e-1 and the code loss does not move (0.163 → 0.163; beliefs frozen); for secretion the gradient explodes (up to 1e24 or NaN: the optimiser drives the body to a defect); **no optimised candidate reached R** (`s3_grad.json`). Caveat: short optimisation from one initialisation; PROVISIONAL.
* R → L: not run for S3 (by the exact O(2) symmetry the answer is the same; S4 ran both directions and the outcomes mirror each other).
* Location dependence: not definable (nothing switched). Dose: n/a.

## S4 fallback — declared FATE-BIAS light channel — NEGATIVE
In illuminated cells a transient term b·w(t) is added to dmu/dt for all slots of one declared type (type 2 or 3); the 8 body-row cells are lit; "T3side→T2" biases the cells currently of type 3 toward type-2 slots, "T2side→T3" the converse, "both" does both (the exchange). Ladder: b ∈ {0.02…0.8}, durations 20, 80, release 300, both directions (`s4_ladder.json`, 144 runs); refinement (durations 40–320, b 0.06–0.6, release 800; `s4_refine.json`, 28 runs); long release up to 6 000 (`s4_long.json`, 12 runs).
* Low doses: unchanged L (R for the R start). Doses above b·duration ≈ 4–8 drive the body to an **intermediate state** (distance to R 0.34–0.5, minimum orbit belief 0.4–0.6 — mixed identity beliefs, incomplete slots) and above that to fragmentation. **No run reached a complete, crisp R** (orbit-complete, orbit belief ≥ 0.85). The intermediate states do not sharpen during 800–6 000 release units; at long release several fragment.
* Interpretation (PROVISIONAL): even a direct bias on the logits only moves the cells onto the mixed-belief manifold (neutral mixtures), because sharp states are stable only through the weak nonlinear field mismatch and the exchange requires 8 cells to pass through duplicate/vacant slots at the same time.
* Because the switch is not available, the TESTBED_SPEC statement "the switch relies on the fate-bias channel" does not arise.

## Consequences
The control target does not exist in the testbed as built. Open questions are in OPEN_QUESTIONS.md (13–15). Identity-event support and the interface were built independently of the switch (IDENTITY_EVENTS.md, INTERFACE.md, DATASETS.md); the SWITCH dataset (T3.4) was **not produced** (Gate S failed).
