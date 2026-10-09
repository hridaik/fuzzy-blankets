# Morphogenesis programme — Stage M2a: audit of M1, protocol v2, skeleton, minimal interventions, library, blind package, viewer

## STATUS: `DONE` for the redirected queue (D1–D6, revised Part 2 library, Parts 3–4). `STOPPED` where instructed: no blind analyses, partitions, representation learning, identity trackers, controllers or port work were done.
Part 0 gate result (earlier): **FAIL** for one control (M1's AN runs never applied a single-cell perturbation, AUDIT_M1.md); all other controls passed. Work then continued under protocol v2 on your follow-up instructions. M1 data are "protocol v1"; everything new is "protocol v2" and the two are never mixed. m0, m0b, m0c, m1 and stage6_flock are untouched.

Labels used throughout: `ESTABLISHED` (measured, controls pass), `PROVISIONAL` (measured but limited by sample, base state or method), `NOT DONE`.

## Status table
| Part | Status | Document |
|---|---|---|
| 0 audit of M1 (injection controls, direct Octave cross-check, exactness, role maps, near-miss) | DONE (gate: AN control FAIL) | AUDIT_M1.md, AUDIT_M1_ADDENDUM.md |
| Protocol v2 (absolute clock T_dev = 32, continuation engine, noise extension) | DONE | PROTOCOL_V2.md, CONTINUATION.md, THRESHOLDS_v2.md |
| R1 census, R2 withdrawal battery, R3 kicks, R4 noise, reanalyses | DONE | CENSUS_V2, WITHDRAWAL_V2, ROBUSTNESS_V2, NOISE, REANALYSIS |
| Part 1 generalization (16-cell census, other perturbation families, initial state) | DONE | GENERALIZATION.md |
| D1 Jacobian spectra | DONE | SKELETON.md |
| D2 period-2 cycle: model or scheme | **UNRESOLVED** | SKELETON.md |
| D3 hysteresis (DH, DT, precision; from class 0 and class 1) | DONE (class-1 DH down-sweep INFERRED, not run) | HYSTERESIS.md |
| D4 minimal durable interventions (246 directions) | DONE | MINIMAL_PERTURBATIONS.md |
| D5 edge state | DONE, PROVISIONAL (one direction) | SKELETON.md |
| D6 replication on relabelled individuals | DONE (3 thresholds × 2 individuals) | SKELETON.md |
| Revised Part 2 library (6 bases, role × channel; 747 runs) | DONE | LIBRARY.md |
| Linearity | DONE (declared subset) | LINEARITY.md |
| Part 3 blind package | DONE; leak check PASS | `../m2_blind_package/` (DATA_DICTIONARY.md, LEAK_CHECK.md, splits.json, manifest.jsonl) |
| Part 4 viewer (OBSERVABLE and AUDIT; 55 entries) | BUILT, **not opened in a browser** | `../viz/` (VIEWER.md addendum, index.html) |
| Original Part 2 library | **NOT DONE (by instruction)** | — |
| COMPUTE_PLAN.md | piloted, updated 4 times; 24 h rule met (≈ 13.3 h wall for the D-stage queue) | COMPUTE_PLAN.md |

## Headline answers

**1. Does any transient intervention durably change SHAPE without an organisational defect (duplicated or vacant role, undifferentiated cell)? — No, in everything tested. `ESTABLISHED` for the class-0 mature body and the tested interventions; depends on class 1 counting as a defect (OPEN_QUESTIONS 2).**
Every durable shape change found ends in the same second attractor, class 1, which has a duplicated role, a vacant role and an undifferentiated cell (REANALYSIS e). Class 1 is reached from the mature body by: D4 SHAPE-SWITCH in 6 of 246 directions (single-cell displacement of the tail-end role, one whole-body eigen-direction, global ligand-4 pulse); large position kicks (6/200, 3 % [1.4 %, 6.4 %]); random smooth displacement fields (8/60 developmental and mature sham runs, 13 % [7 %, 24 %]). No third shape (NOVEL, PERSISTED, NONCONV) appeared in 2,309 D4 evaluations or 300 R2 runs beyond those class-1 cases. Withdrawal of the DH, DT and AN perturbations never changed shape. The opposite direction exists: the D3 DT loop repairs class 1 into class 0 (HYSTERESIS.md).

**2. Minimal durable interventions (MINIMAL_PERTURBATIONS.md; class-0 adult, one base state up to relabelling). `ESTABLISHED` for the listed direction sets; the ranking of roles is `PROVISIONAL` beyond them.**
| actuator class | FATE-SWAP min / median (directions with a threshold / total) | SHAPE-SWITCH min / median |
|---|---|---|
| single-cell displacement | 0.68 / 4.4 (52/128) | 1.9 / 5.5 (4/128) |
| whole-body displacement, eigen / random | 2.6 / 4.5 (5/5); 1.8 / 5.4 (15/20) | 9.5 (1/5); none (0/20) |
| single-cell secretion pulse | 3.3 / 16.5 (11/32) | none (0/32) |
| regional pulse | 2.6 / 8.8 (36/52) | none (0/52) |
| global pulse | 4.5 / 7.6 (4/4) | 20.9 (1/4) |
Amplitudes in native units, brackets 0.05–10 (displacement) and 0.05–50 (pulses); "none" = none up to the bracket. SHAPE-SWITCH is mostly "no threshold up to the maximum". A SHAPE-SWITCH is always preceded, as amplitude grows, by a FATE-SWAP at a lower amplitude (6/6). Just above a FATE-SWAP threshold the outcome is FATE-SWAP in 100 % of directions, usually a transposition of two cells; just above a SHAPE-SWITCH threshold the end shape is class 1 in 6/6. **Privileged roles/regions: yes.** Role 7 (tail end) is the easiest to swap by displacement (median 1.45) and the only role with any SHAPE-SWITCH by displacement; roles 2, 4, 6 are the hardest (4.8–5.9); role 3 is the most sensitive to a secretion pulse and role 0 insensitive to it (none up to 50); regional pulses are most effective near the tail end, with the minimum threshold rising monotonically from 2.6 at x = +1.74 to 7.5 at x = −1.78. Ratios of per-role medians: 4.0 (displacement), 9.1 (single-cell pulse, lower bound); of per-centre medians: 10.8. Mirror-image roles and regions agree exactly (6/6 pairs). Three thresholds replicate on two relabelled individuals (D6). 29 of 246 directions have non-monotone windows (cause NOT DONE).

**3. Is there hysteresis in any parameter family? — Yes in role assignment, no in shape for class 0; none under the precision multiplier. `ESTABLISHED` (D3; one base state; down-sweep from class 1 not run).** Quasi-static continuation of DH and DT strength ε up and back down returns the class-0 shape exactly but permutes the roles (DH: a 5-cycle; DT: a swap of two roles). The precision multiplier shows no hysteresis (baseline recovered). Class 1 collapses onto the class-0 trajectory at ε = 0.05 under DH, and under DT stays class-1-like to ε ≈ 0.2, merges at ε = 1.0 and ends in class 0 (a repair). Isolated period-2 cycles occur inside the DH and DT sweeps; some steps did not converge (DH 0.9 up, DT 0.3 up, DT 0.2 down).

**4. Is the period-2 cycle a model or a scheme property? — `UNRESOLVED`.** The one-bin map has an eigenvalue −1.54 at the sustained-DH state (a flip, with the unstable mode 73 % in the action / previous-action blocks) and the two-bin monodromy is stable (0.823). That fits either a model mechanism or the discrete scheme's one-bin delay. The engine diverges under sub-stepping for any perturbation, so the decisive finer-integration test could not be run.

**5. Does the published clock change the stable-shape census? — Yes (`ESTABLISHED`, CENSUS_V2.md).** Under the published fast clock (T_dev = 32) 97 of 100 individuals reach class 0 and 3 reach class 1 (all 3 among 50 secondary draws, 0/50 primary [0 %, 7 %]); under M1's slow clock the same 50 secondary draws never produced a second class, and the slow-clock "attractor" is the fast-clock fixed point seen early (d_pair 2.2e-5). The 16-cell census (30 individuals) is 17/30 in one class with ten clusters in all (GENERALIZATION.md).

**6. Can a mature-body durable SHAPE change be produced? — Only by large impulses into class 1.** See 1. Belief resets, secretion kicks and small position kicks all return to the same shape (R3: 100/100 for belief reset).

**7. Durable role change beyond sham, null and spontaneous? — Beyond null and spontaneous: yes. Beyond sham: only for the single-cell AN perturbation.** Null continuation 0/20; spontaneous role switches 0 in 72,000 bins at three noise levels (< 0.15 per 1000 bins). DT-ADULT relabels 20/20 but so does the random sham field (16/20; DT vs sham p = 0.11), and DT-ADULT is one experiment replicated (n_eff = 1). DH-ADULT is 0/20 noise-free but 10/10 at 1 % noise. AN-ADULT relabels 6/20 vs sham-AN 0/20 (p = 0.02; weak sham, only 8/20 took effect). D4 FATE-SWAP gives the dose-response: the threshold is finite for every actuator class.

**8. Fate of the single anomalous cell (AN, mature body)? — Shape: no sustained effect (20/20). Role: a deterministic function of the targeted role, 6/20 relabelled** (head-end slot 0: transposition; slot 3: 3-cycle; slots 1, 2, 4, 5, 6, 7: no change; 8 role cases, one mature state). Developmental timing gives 11/20 and depends on the individual's history (REANALYSIS a). `ESTABLISHED` for the class-0 body; class 1 as a base was not tested.

## What I did not do, and caveats
- Original Part 2 library (by instruction); blind analyses; D4 from class 1; amplitudes above the brackets; D2's finer-integration test; the D3 class-1 DH down-sweep; mechanism of D4 non-monotone windows; D5 from other directions.
- D4 used a 4-point amplitude grid for single-cell displacement (declared), so the threshold counts there are lower bounds.
- The base state is one body up to relabelling; "individuals" in R-series tables are partly the same experiment (n_eff columns in WITHDRAWAL_V2.md). The Wilson intervals above treat the stated units as the unit of replication.
- **The viewer was built and its files are structurally well-formed but nobody has opened it**: there was no browser or node in the session, so its JavaScript is unexecuted (VIEWER.md addendum).
- Role labels rest on the Hungarian slot match to the class-0 template; the "permuted roles" in D3 and the FATE-SWAP counts inherit that definition.

## The blind package (`../m2_blind_package/`)
2,418 segments, 891,632 bins, 156 conditions, 150 individuals, 152 MB; v2 data only; 60 16-cell segments; zero-noise canonical plus noise levels as unordered opaque labels NL0–NL3. Contents: `DATA_DICTIONARY.md`, `LEAK_CHECK.md` (PASS: 2,486 files, 891,632 position frames compared permutation-invariantly with the reference arrays, 45 forbidden patterns, key and label whitelists), `manifest.jsonl`, `splits.json` (30 held-out individuals, 23 held-out conditions, 4 held-out region centres; held out by individual AND by condition; 492 segments individual-held-out), `segments/*.npz`, `ladder/` + `ladder_index.json` (observation ladder O2–O4 rendered with M1's unmodified renderer, 34 segments, 1,562 frames; O1 = every segment). Role maps and cell types are excluded; the sealed mapping is `sealed/blind_mapping.json` in this directory and is never in the package. It includes the TRANSITION DATASET (390 D4 run segments around the thresholds) and the noisy R4 runs. The leak checker (`code/leak_check.py`) lives outside the package.

## Viewer (`../viz/`)
OBSERVABLE and AUDIT builds, 55 entries each (`viz/output/m2a/`), listed in an M2a section of `viz/index.html`: class-1 exemplars, the sustained-DH cycle, D3 up/down sweeps (synced), D4 near-threshold pairs (synced), the D5 edge state, R2 ADULT synced triples (DH, DT, AN, SHAM_DH); AUDIT only: role-map overlay and eigenmode visualisation. M1's `build_viewer.py` is untouched.

## Layout
```
PROTOCOL_V2 CONTINUATION THRESHOLDS_v2 COMPUTE_PLAN       protocol, engine, thresholds, compute record
CENSUS_V2 WITHDRAWAL_V2 ROBUSTNESS_V2 NOISE REANALYSIS     R1–R4 and reanalyses
GENERALIZATION SKELETON HYSTERESIS MINIMAL_PERTURBATIONS   Part 1, D1/D2/D5/D6, D3, D4
LIBRARY LINEARITY OPEN_QUESTIONS AUDIT_M1(+ADDENDUM)       library, linearity, questions, audit
oracle/  spm_ADEM_m2a.m (state-exporting engine copy), m2a_*.m, direct_morph.m
code/    run, analysis, package, leak-check and viewer scripts (python env: conda `fuzzy-blankets`)
tests/   test_engine_equivalence.py (patched engine = SPM12 bit-identical), test_toolkit.py, test_part0_findings.py
sealed/  blind_mapping.json, reference arrays and thresholds (never shipped)
data/    v2/ (all protocol-v2 runs and results), MANIFEST.md
```

> **UPDATE 2026-10-08:** the vanilla programme is CLOSED; this entry was applied, edited, as `../STATUS.md` (not in `stage6_flock/`); the closure synthesis is `../VANILLA_CLOSURE.md`; `../m2_blind_package/` is archived NOT FOR RELEASE.

## Proposed repository status entry (original text, superseded by ../STATUS.md)
> **2026-10-08 — Morphogenesis programme, Stage M2a (audit, protocol v2, skeleton, minimal interventions, library, blind package, viewer): done.** New directories `morphogenesis/m2a_audit_and_library/`, `morphogenesis/m2_blind_package/`, additions to `morphogenesis/viz/`. M1 audited: its single-anomalous-cell runs were bit-identical to the double-head runs (gate fail, corrected); the published developmental clock (T_dev = 32) yields a second, organisationally defective shape class (duplicated and vacant role, undifferentiated cell) in 3 of 50 secondary draws that M1's slow clock never showed. Dynamical skeleton: both adult shapes are linearly stable (slowest rates −0.13 and −0.07 per bin, belief-carried); the class boundary is, along the one direction examined, a saddle with a single unstable eigenvalue (edge state approximate). Minimal durable interventions by bisection over 246 directions: role swaps (shape unchanged) at displacements ≈ 0.7–8 or pulses ≈ 3–38 (tail-end role/region easiest); shape change only into the defective class, in 6 directions, always after a role swap; no defect-free durable shape change found. Hysteresis: none in shape for the healthy body, present in role assignment under the DH and DT loops; the defective body collapses or is repaired. Period-2 cycle: model vs scheme UNRESOLVED (engine not sub-steppable). Revised role × channel response library (747 runs, linear to 5 % except two gain channels) and a leak-checked blind package (2,418 segments, v2 only, 30 held-out individuals, 23 held-out conditions). Viewer built, not yet opened in a browser. No blind analyses performed.

## What I need from you
See OPEN_QUESTIONS.md: whether class 1 counts as a defect for headline 1; the noisy/16-cell segments in the first blind release; whether to run D4 from class 1 and above the brackets; whether to open the viewer and report rendering problems.
