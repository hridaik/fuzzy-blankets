# morphogenesis/testbed — continuous-time engine (T1) and testbed modifications (T2)

Entry point. Scope: build and validate the engine, design and calibrate the testbed. No blind analyses, trackers, controllers, interface or partition analyses were run. `stage6_flock/` and earlier morphogenesis stages were not modified (new files only, plus a link block in `viz/index.html` and an appended section in `viz/VIEWER.md`). Labels: ESTABLISHED / PROVISIONAL / NOT DONE.

## Headline answers
| question | answer |
|---|---|
| **Is the engine faithful?** | **Yes, with one declared correction — ESTABLISHED.** Adult fixed point matches the Octave oracle to d_pair = 8.7e-5 (gate 0.01); RK4 order 4; class-0/1 relaxation times −0.125 vs −0.127 and −0.072 vs −0.066 per unit; census from the oracle's own initial beliefs 98/100 per-draw class agreement (secondary draws 48/1/1 engine vs 47/3/0 oracle). The task's literal free energy is *not* the oracle's: `spm_ADEM` drives action with its own precision and an action prior (D0 in ENGINE_SPEC.md; the factor 1.5 is a fit, PROVISIONAL). The oracle's period-2 cycle under sustained DH/DT is absent in the engine (all fixed points) — evidence, not proof, of a scheme artefact. |
| **Does assembly survive dropping the positional channel?** | **No — ESTABLISHED negative.** Vanilla 8-cell, positional OFF: 0/50 (ON control 50/50); two minimal fixes (dispersed start; + long-range signalling): 0/50 each. 24-cell compact body A, OFF, near-uniform beliefs: 0/50. It assembles and is stable **only from a seeded start** (committed identities, jitter 0.3: 49/50; jitter 0.6: 37/50), with log π_prior = −10 and no action priors (crisp roles: every cell > 0.95). |
| **Does body-plan memory give a durable, switchable, identity-preserving bistability?** | **No — not found, P2 fails — ESTABLISHED within the explored space.** Plan A is a stable attractor; plan B (two-headed) is not, even stand-alone (0/78 seeded draws; Jacobian unstable); in the plan-mixture model with a memory ligand a B start decays to A for every coupling tried; slow-manifold scans show no double well. P3–P6 NOT DONE. |
| **Does chirality?** | **Mirror forms: yes. Switching: not found.** Both enantiomorphs of the chiral 24-cell body are stable and complete (16/16, Jacobian stable; by exact O(2) symmetry of the relational model). No disc pulse (3 centres × 2 signals × 7 doses up to 32, 20 time units) produced the mirror form: 8/42 left it unchanged, 34/42 disrupted the body; outcomes non-monotone. |

## Status table
| item | status | file |
|---|---|---|
| Part B bridge inventory + 13 testbed requirements | ESTABLISHED (read-only, nothing run) | BRIDGE.md |
| T1.1 model / T1.2 integrator / T1.3 calibration | ESTABLISHED | ENGINE_SPEC.md |
| T1.4 (a)–(e) faithfulness | ESTABLISHED (c: PROVISIONAL interpretation) | FAITHFULNESS.md |
| **GATE T1** | **PASSED** | |
| T2a positional OFF | ESTABLISHED negative; seeded start works | TESTBED_SPEC.md |
| T2b crisp roles | ESTABLISHED (log π_s 2, log π_prior −10) | TESTBED_SPEC.md |
| T2c P1 | NOT MET as specified (seeded only) | MEMORY_CALIBRATION.md |
| T2c P2 | FAILS (plan B unstable) | MEMORY_CALIBRATION.md |
| T2c P3–P6 | NOT DONE (no bistability) | MEMORY_CALIBRATION.md |
| T2d chirality | forms ESTABLISHED; switch NOT FOUND | CHIRALITY.md |
| T2e noise / CRN / natural ensemble | ESTABLISHED (σ = 0.02; CRN to 1e-14); ensemble B invalid | NOISE_AND_CRN.md |
| T2f ground-truth exports + audit-gated loader | ESTABLISHED | GROUND_TRUTH_EXPORTS.md |
| T2g chiral motility, turnover | flags only, OFF | TESTBED_SPEC.md |
| Viewer + exemplars (18 HTML) | built; **never opened in a browser** | ../viz/testbed_index.html |
Exemplars present: T1.4 oracle-vs-engine side by side (2), T2a (2), T2c A/B adults, memory A vs B start (decay, with ligand heatmap and plan ring), T2d mirror forms, T2d pulse vs sub-threshold vs disruptive (sham included), natural ensemble under noise. **Absent because the underlying result does not exist:** P5 switch run vs matched-dose non-switching region vs sham; P3 hysteresis sweep.

## Operating point for later stages (if used at all)
Relational compact 24-cell bodies A and chiral, positional OFF, `log π_s = 2`, `log π_prior = −10`, `k_mu = 1.4`, `k_a = 0.4`, dt 0.02 (check dt·ρ < 1), noise σ_x = σ_c = 0.02, seeded start. **Caveat for any later identity or control work:** there is no second body plan, and the hidden belief block is nearly frozen (rates ~1e-4).

## Other deliverables
ENGINE_SPEC.md, FAITHFULNESS.md, TESTBED_SPEC.md, MEMORY_CALIBRATION.md, CHIRALITY.md, NOISE_AND_CRN.md, GROUND_TRUTH_EXPORTS.md, COMPUTE_PLAN.md, OPEN_QUESTIONS.md, `data/MANIFEST.md`, code in `code/` (exploration scripts in `code/explore/`), tests in `tests/` (`python -m pytest tests`, 6 pass, ≈ 12 s).

## Proposed text for a repository status entry (not applied to any status file)
> **Morphogenesis testbed T1/T2 (continuous-time engine).** T1 PASSED: a JAX continuous-time gradient-flow engine reproduces the Octave `spm_ADEM` adult fixed point (d_pair 8.7e-5), relaxation rates and a ~2 % second-attractor census after one declared correction (action-side precision/prior, D0); sustained DH/DT end in fixed points, not cycles (evidence the oracle's period-2 cycle is a scheme artefact, PROVISIONAL). T2: dropping the positional channel breaks self-assembly (0/50 at 8 and 24 cells; fixes F1/F2 0/50); compact 24-cell bodies are stable and crisp (all beliefs > 0.95) from a seeded start at log π_prior = −10. The designed two-plan body-plan memory did NOT produce bistability (plan B not an attractor; no double well in the slow plan variable; P3–P6 NOT DONE). Chiral body: both mirror forms stable; no identity-preserving disc-pulse switch up to the tested bracket. CRN verified to 1e-14; two-tier ground-truth exports with an audit-gated loader built. Open: redesign of the memory (OPEN_QUESTIONS 3–4).


---
# TESTBED v1 UPDATE (follow-up instruction: situs calibration, identity events, T3 interface and blind package)

## Headline answers (v1)
| question | answer |
|---|---|
| **Is the mirror switch available, and via which family?** | **No. Gate S FAILED; the switch is NOT AVAILABLE** — not with any of nine physical actuator families (secretion ±, receptor gain ±, migration gain; 1 728 forward runs, 36 gradient optimisations, 0 reached the other form) and not with the declared fate-bias fallback (184 runs; the body is driven to an intermediate mixed state and then fragments). The review's diagnosis was confirmed: the slowest non-neutral belief rate is k_mu·pi_prior (3.9e-4 at the best stable setting vs the 1e-2 target) and no setting restores plasticity while keeping the body stable. (SITUS_CALIBRATION.md) |
| **At what minimal dose?** | Not defined (no switch). The disruption (body destroyed) threshold exists but was not bisected. |
| **Is it location-dependent?** | Not definable. S2 shows the switch would be a pure exchange of the types of the 8 cells in the two body rows between the ±y halves (zero net displacement). |
| **Do the identity events behave sensibly?** | **Partly.** Single replacement: the naive cell re-specifies into the vacated slot in 9/24 cases (5–285 time units) and the body is complete in 9/24; extrusion: the cell rejoins in 23/24 and the body is complete in 13/24; serial replacement (Ship of Theseus), cut and fusion destroy the body (4/4, 2/2, 12/12, 12/12 runs defective). Neither slot completeness nor chirality survives complete turnover. The unperturbed body also dissolves under the operating noise at ≈ 3 300 time units. (IDENTITY_EVENTS.md) |
| **Is the blind package ready?** | **Yes for identity / observation work, not for control.** `testbed_blind_v1/`: 740 runs at levels O1–O3, opaque labels, leak check PASS, split manifest, experimenter-style data dictionary; natural ensembles 2 200 + 600 samples per form (effective ≈ 900, just under the M2 target of 1 000); 60 CRN-matched identity-stress triplets. **No switching dataset exists.** (DATASETS.md) |

## Status of the v1 items
| item | status |
|---|---|
| Plasticity operating point (S1) | ESTABLISHED negative: target not met; chosen log pi_s 2, log pi_prior −8, sigma_mu 0 |
| Switch geometry (S2) | ESTABLISHED: pure fate exchange of 8 cells |
| S3 physical-actuator search / S4 fate-bias fallback | ESTABLISHED negative |
| Gate S | FAILED -> Parts I and T3 completed regardless |
| Part I (alive mask, ids, 7 event types, 5 behaviour checks) | ESTABLISHED |
| T3.1/T3.2 renderer and actuator API | ESTABLISHED as code; pipette/bath exercised only in tests; arena light path not used in any dataset |
| T3.3 natural ensembles | ESTABLISHED; M2 just short by autocorrelation estimate |
| T3.4 identity-stress dataset | ESTABLISHED; SWITCH dataset NOT PRODUCED |
| T3.5 hidden truth: LNA covariance, influence matrices, event logs | ESTABLISHED with caveats (saturated belief modes) |
| T3.6 blind package v1 + leak check | ESTABLISHED |
| Viewer exemplars | 22 new files (S1, S2, S3/S4 synced switch vs wrong location vs sham, five event types incl. serial replacement, natural O1 vs O3); **3 pages rendered in headless Chromium (playwright) without JS errors and screenshots inspected** (`viz/output/testbed/screenshots/`); the others were not rendered |
New documents: SITUS_CALIBRATION.md, IDENTITY_EVENTS.md, INTERFACE.md, DATASETS.md; updated GROUND_TRUTH_EXPORTS.md, TESTBED_SPEC.md, COMPUTE_PLAN.md, OPEN_QUESTIONS.md (items 12–15); blind package `morphogenesis/testbed_blind_v1/`. Tests: `python -m pytest tests` (9 pass).

## Proposed text for a repository status entry (v1; not applied to any status file)
> **Morphogenesis testbed v1.** Control target (chiral body mirror switch, L<->R) NOT AVAILABLE: Gate S failed. At the most plastic stable operating point (log pi_prior −8) the belief relaxation rate is 3.9e-4 (target 1e-2); belief noise, a natural-gradient belief flow and higher sensory precision do not help; 1 728 physical-actuator runs, 36 gradient optimisations and 184 fate-bias runs never produced a complete other form. The two forms differ by an exchange of 8 cell types with zero net displacement. Unperturbed bodies dissolve under the operating noise at ≈ 3 300 time units. Identity events: single replacement repaired in 9/24, extrusion 13/24, serial replacement / cut / fusion destroy the body. Built: alive-mask / permanent-id event engine, experimenter-level actuator API (arena light masks, pipette, bath, tweezers, surgery, sham), observation levels O1–O3, natural ensembles (2 200 + 600 samples per form), 60 CRN-matched identity-stress triplets, and blind package v1 (740 runs, leak check PASS). Next: identity/continuity and partition work can proceed on the package; any control work needs a redesigned plastic testbed (OPEN_QUESTIONS 13–15).
