# TESTBED_SPEC.md — chosen parameters per variant, with reasons; T2a/T2b results; planned add-ons (T2g)

Labels: ESTABLISHED / PROVISIONAL / NOT DONE. Engine: ENGINE_SPEC.md. Templates: `code/templates.py`. Runner/classifier: `code/asm.py`.

## Common definitions (declared before measuring)
* **Assembly success** (`asm.analyse`): type-constrained, permutation-invariant, rigid-motion-invariant (proper rotations; reflections reported separately) mean distance of the final configuration to the template `< 0.4` (= 0.4 × template nearest-neighbour spacing; for the vanilla model the oracle's own near-miss is 0.277), AND shape stationary (max pairwise-distance speed < 1e-3 per time unit; rigid motion allowed), AND *orbit-complete* (cells assigned to belief-orbits of template slots with the right multiplicities; slots with identical code + expected-field fingerprints, i.e. mirror twins, form an orbit because no reflection-invariant cue can separate them), AND type counts right.
* Roles: role of a cell = argmax of its place belief. "Max belief" is reported at orbit level.
* Rigid distance: alternating Hungarian assignment / Procrustes from 48 starting angles (`shape.d_rigid`).

## Variants
| variant | n | positional channel | action priors | log π_s / log π_prior | k_mu, k_a | status |
|---|---|---|---|---|---|---|
| **vanilla** (faithfulness) | 8 | ON (absolute) | π_act = 1.5e², π_a = e⁻² | 3 / (e⁻²+e⁻⁸) | 1.4, 1.2 | ESTABLISHED (FAITHFULNESS.md) |
| **testbed body A** (one-headed) | 24 | **OFF** | none (π_a = 0, translation invariant) | **2 / −10** | **1.4, 0.4** | assembles only from a *seeded* start (below) |
| body B (two-headed) | 24 | OFF | none | same | same | **not a stable attractor** (MEMORY_CALIBRATION.md) |
| **chiral body** | 24 | OFF | none | same | same | both mirror forms stable (CHIRALITY.md) |
| memory model (K = 2 plans + 5th signal) | 24 | OFF | none | same + π_m, π_ζ | same | **no bistability found** (MEMORY_CALIBRATION.md) |
Reasons: (i) no action priors and `π_prior = e⁻¹⁰` — with the published `π_a = e⁻²` the action prior pulls every position toward the origin and the belief prior toward uniform, which erodes sharp states (template one-hot start decays to a soft blob, d = 1.4, within 100 time units); (ii) `k_a = 0.4` rather than 1.2 lowers the stiffness ρ (≈ 20–55 vs 75–190), allowing dt = 0.02 instead of 0.004; basin structure depends on `k_a/k_mu` but the testbed is not required to match SPM; (iii) log π_s = 2 satisfies the T2b criterion (below).

## Body geometry (declared design; spacing 0.9–1.0, κ = 1)
Compact rows of cells (row spacing 0.9, cells 1.0 apart within a row): **A** rows `1,3,4 | 4,4 | 2,2,2,2` = head (type 1, red, 8 cells), trunk (type 2, blue, 4 centre cells of two body rows), limbs (type 3, green, 4 outer cells), tail (type 4, gold, 8). Extent 7.2 × 3.0. **B**: slots 0–15 identical, the 8 tail slots are re-coded as a second head (type 1) and re-arranged as rows `3,3,2` beyond the body (33 % of slots change colour and position; extent 6.3 × 3.0). **Chiral**: A with the four limb cells all on the +y side (rows read T2,T2,T3,T3). Channel 0 of the secretion code is a graded axial morphogen (0.3 anterior … 2.3 posterior, by the cell's own plan-specific x), giving every slot a distinct code; channels 1–3 are the three type bits as in the vanilla model. (Design iterations: a first, elongated A (12.6 long, 8-cell tail line) was not stable relationally; an unsymmetrised/graded-free code was not stable at 24 cells; amplitude 2.0 of the gradient was needed. See `code/explore/`.)

## T2a — positional channel OFF — result: FAILS for development; assembles from a seeded start (50 draws each, `data/t2a_results.json`, log π_s = 2 operating point for the 24-cell rows)
| condition | success / 50 | median distance to template | orbit-complete |
|---|---|---|---|
| vanilla 8, positional **ON** (control) | **50 / 50** | 0.271 | 50 |
| vanilla 8, positional **OFF**, near-uniform beliefs | **0 / 50** | 0.73 | 0 |
| + fix F1 (cells start dispersed in a disc r = 3) | 0 / 50 | 0.60 | 0 |
| + fix F2 (F1 and every signal also sensed at long range κ = 0.25) | 0 / 50 | 1.02 | 0 |
| 24-cell body A, OFF, near-uniform beliefs | **0 / 50** | 0.81 | 0 |
| 24-cell body A, OFF, **seeded start** jitter 0.3 | **49 / 50** | 0.024 | 50 |
| same, jitter 0.6 | 37 / 50 | 0.116 | 46 |
*Seeded start* = committed identities (logit 8, random cell → slot assignment, jitter 0.3 on logits) with cells at their slot positions + Gaussian jitter. It tests the basin of the assembled state, not self-assembly.
Why (mechanism, PROVISIONAL): predictions are linear in belief and each cell's own action makes its position and secretion equal to its prediction for ANY belief, so the own-channel errors vanish on a continuum of mixed-belief states; only the nonlinear field error sharpens beliefs, weakly. With positional OFF there is no per-cell anchor, so the undifferentiated cluster is stable (vanilla 8: beliefs stay 0.14, all cells type 2). For 24 cells even the published-style ON model does not assemble from near-uniform beliefs (0/4 at the earlier template; engine on the oracle's own 16-cell template: 11–13 distinct argmax slots of 16, d ≈ 0.6–0.8).
Other attempts, outside the two-fix quota, reported for completeness (small n, `code/explore/`): a rigid-motion-invariant radial cue (distance to centroid) and a body-frame cue (principal-axis (u,|v|)) — the body-frame cue assembled vanilla-8 shapes to d ≈ 0.09–0.3 with a spontaneously translating and rotating body (centroid speed 0.1, rotation ±8° per unit; argmax collisions of mirror twins) but not 24-cell bodies. NOT adopted.
**Rigid drift/rotation of the assembled body** (seeded A, 50 draws): median centroid speed 4e-4, median |rotation rate| 1e-3 °/time unit (practically stationary; the 3 rigid zero-modes of the Jacobian are neutral). Under noise it diffuses (NOISE_AND_CRN.md).

## T2b — crisp roles — ESTABLISHED (body A; 6 seeded draws per cell, `data/t2b_results.json`)
Grid log π_s ∈ {2,3,4} × log π_prior ∈ {−2,−4,−6,−8,−10}. Rows with assembly: (2,−8) 6/6 (min orbit belief 0.92; 3/6 draws > 0.95), (2,−10) 5/6 (**all 6 draws have every cell's orbit belief > 0.95**, min 0.956), (3,−8) 2/6, (3,−10) 5/6 (5/6 draws > 0.95, worst 0.875), (4,−10) 5/6 (worst 0.90); everything with log π_prior ≥ −6 gives 0/6 assemblies at log π_s = 2–3 (soft, wrong shapes) or soft beliefs. **Chosen: log π_s = 2, log π_prior = −10** (the only cell where every cell exceeds 0.95 in every draw while assembly succeeds in 5/6). Trade-offs: the prior must be essentially removed; sharp beliefs make the slow belief modes extremely slow (rates ~1e-4: saturated softmax), so relaxation of beliefs after a perturbation takes ≫ 1000 time units; π_s = e⁴ needs dt ≈ 0.005. A companion sweep for body B (`data/t2b_B_results.json`, `t2b_ka1.2_results.json`): 0 successes in 54 + 24 draws at every setting (also at k_a = 1.2).

## T2g — deferred add-ons (flags only, OFF by default, no calibration, no tests of behaviour)
* **Chiral active motility**: `Params.omega` adds a rigid rotation `ω · ẑ × (x_i − centroid)` to every cell's position flow. Implemented as a flag only; ω = 0.
* **Cell turnover**: `Params.turnover_rate` exists as a parameter; no code path (cell birth/death would need a variable cell set; planned as masked slots with an `alive` array, already exported as all-True).


## Testbed v1 scope declarations (follow-up instruction)
* **Default start = seeded start**, declared as a **"maternal prepattern"**: cells hold committed identities (random cell -> slot assignment) and sit at their slot positions plus jitter. **De novo self-assembly is out of scope** (0/50 at 8 and 24 cells with the positional channel off; TESTBED_SPEC T2a).
* Positional channel OFF (relational, O(2)-symmetric) remains the testbed setting; the control target is the chiral body's mirror switch L <-> R ("situs inversus"). The two-plan memory model is parked (OPEN_QUESTIONS 12).

## Testbed v1 operating point (replaces the T2b point for all v1 work; SITUS_CALIBRATION.md S1)
Chiral 24-cell body, positional channel OFF, **log pi_s = 2, log pi_prior = −8** (was −10), k_mu 1.4, k_a 0.4, dt 0.02, sigma_x = sigma_c = 0.02, **sigma_mu = 0** (belief noise dissolves the body), plain gradient belief flow (the natural-gradient variant D6 is implemented but OFF). Reasons: it is the most plastic setting at which the seeded bodies are still stable and crisp (14/16 seeded starts, median minimum orbit belief 0.965). Measured properties and limits (all deterministic unless noted): slowest non-neutral belief relaxation rate 3.9e-4 per time unit (target 1e-2 NOT met); no spontaneous L<->R switching in 24 000 body-time units (rate < 1.25e-4); the unperturbed body **dissolves under the operating noise at a median of ≈ 3 300 time units**; fast position fluctuations decorrelate in 14–20 time units, body-shape deformation in ≈ 150; mirror switch NOT available (SITUS_CALIBRATION.md).
**Declared scope:** default start = seeded start ("maternal prepattern"); de novo self-assembly out of scope; the two-plan memory model is parked.
**New engine capabilities** (ENGINE_SPEC addendum): `N_cells ≠ n_slots`, alive mask, control inputs (secretion `ext`, receptor gain `rg`, migration gain `mig`, fate-bias drive `fb`, pipette sources, bath) with raised-cosine ramps (`run_ctl`, differentiable with `remat`), `nat_grad` belief variant (off). Tests: `tests/test_engine.py` (6), `tests/test_interface.py` (3).
