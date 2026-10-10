# STAGE6_SYNTHESIS.md

Final scientific summary of Stage 6 (flock), spanning `PROTOCOL_V1a` (the
frozen, corrected V1 protocol — see `v1_mechanism_audit/V1_RECORD_AUDIT.md`
section A2), `v1_mechanism_audit/`, and `v2_interface_control/`. This
document is the single place a reader should start; every claim below points
to the specific file/JSON that supports it.

## The key scientific question, answered

> **Which interface actually mediates control of an emergent flock?**

Answer: **the direct one-step dynamical interaction shell (`B^D`), not the
spectral/Fiedler boundary (`B^F`)**. `B^D` is also, independently, an exact
statistical Markov blanket for the frozen core's next state (Part H), and it
is the interface that empirical control leverage concentrates around (Part
C/D). These are not four unrelated facts — they are the same underlying
structural interface, viewed through four different lenses, and three of the
four lenses (spectral, empirical single/pair-response ranking) each capture
only a fragment of it on their own.

## Established

- The flocking-agent Python port is validated by 28 deterministic/algebraic
  unit tests (corrected count — see `v1_mechanism_audit/V1_RECORD_AUDIT.md`
  A1.1) plus qualitative reproduction of emergent alignment.
- `PROTOCOL_V1a`'s frozen canonical flock (seed 2, `t0=41`, `|I0|=20`) is
  atypical in `t0` (94th percentile, very late-forming) and eigengap (1.2nd
  percentile, an almost-borderline spectral identification), but **typical**
  in boundary size (`|B^F_0|=2` sits at the 49.7th percentile — median is 3)
  — correcting `RESULTS_V1.md`'s framing of the small boundary as the
  noteworthy anomaly (`v1_mechanism_audit/V1_RECORD_AUDIT.md` A3).
- A bird's next heading in this port depends **only** on its fixed Moore-lattice
  neighbors — birds occupy static lattice sites; only the heading (Potts-spin)
  state evolves. This is derived directly from
  `flock_sim.active_inference.compute_G` and `flock_sim.lattice.Lattice`, not
  assumed (`v1_mechanism_audit/MECHANISM_AUDIT_RESULTS.md` Part B).
- `B^D_0` (the set of exterior birds that are Moore-neighbors of the frozen
  core) is an **exact** statistical Markov blanket for the core's next state:
  0.0000 excess predictive log-loss vs. ground truth over 8,000 bird-samples,
  confirmed both by direct code-structural argument (H1) and by empirically
  corrupting everything outside it with zero effect (H2, Part H).
- The Fiedler/spectral boundary `B^F_0` is a strict subset of `B^D_0` on the
  canonical flock (2 of 12 members) and overlaps `B^D_0` only weakly across a
  small ensemble of other flocks (mean Jaccard 0.12; two flocks had zero
  overlap) — `B^F` is not a reliable proxy for the true interaction shell.

## Negative results (under frozen protocols)

- `PROTOCOL_V1a`'s own search (single-actuator exhaustive, pair-restricted to
  a top-10-by-response shortlist, greedy to k=6) failed to retarget the core
  — genuinely, not due to a search bug (`RESULTS_V1.md`).
- This audit's **full exhaustive pair sweep** (all `C(80,2)=3160` non-core
  pairs, `v1_mechanism_audit/data/pair_synergy.json`) confirms this
  generalizes: **zero of 3160 pairs** reach `P(success)>=0.5`; best pair
  `R_ij=0.160`. Sparse control genuinely cannot be achieved by any pair,
  however chosen.
- Fiedler-boundary-only control (`B^F_0`, 2 birds) fails completely
  (`p_success=0.00`) — confirming V1's own observation about this specific
  arm, now on a firmer structural footing (Part D/H).
- Under the manuscript's literally-stated "all precisions = 1," this model
  **essentially never flocks** (0/50 seeds qualify within 60 steps;
  mean polarization `Phi≈0.11` at t=30, versus 0.74 under the code's actual
  defaults) — see Part G. Whatever produced the paper's Figure 1, it was very
  unlikely to be the literal `ρ=ω=1` regime the text states.
- `P(success & integrity)` is 0.000 for **every** exterior-only control arm
  tested across both the mechanism audit and V2 replication, despite high
  target-heading success rates — see "Mechanistic findings" below.

## Mechanistic findings

- V1's negative result was a consequence of searching an **incomplete**
  candidate interface (a top-10 shortlist by single-bird response, drawn from
  all 80 exterior birds), not evidence that sparse external control is
  impossible. Once the search is restricted to the **structurally-derived**
  `B^D_0` (12 birds on the canonical flock), forcing the full set reaches
  `p_success=0.96` — matching all-80-exterior-bird forcing — and a
  **sparsified 9-bird subset within that same correct pool** already reaches
  `p_success=0.90` (`v1_mechanism_audit/data/shell_sparsification.json`).
- The established core shows **no sharp cascade/bistable threshold** under
  direct internal forcing (Part F) — response grows smoothly with the number
  of forced interior birds — consistent with a gradually-reinforcing
  consensus rather than a hard tipping point, and consistent with why
  correctly-targeted *exterior* propagation (through `B^D_0`) can succeed
  without needing to "break" anything abruptly.
- **Why does success not imply integrity?** Direct full-core forcing
  trivially satisfies `C_{I0}(t)>=0.8` throughout (it sets every core bird's
  heading directly), but **any propagation-based exterior control** —
  including the near-perfect `B^D_0` arm — necessarily passes through a
  transient period of partial internal disagreement while different parts of
  the core respond and re-converge, driving `C_{I0}(t)` below 0.8 at some
  point in the control window even when the FINAL target-heading fraction is
  high. This is a structural property of propagation-based steering in this
  model, demonstrated (not assumed) in Part D and reproduced in every V2
  replication flock. The frozen integrity criterion was not loosened in
  response; it is reported honestly, alongside a separately-labeled
  "recovery window" diagnostic, throughout.
- A genuinely good secondary finding: exterior-shell control, once it
  succeeds, is **more persistent post-release** (`P(persistence|success)≈1.0`)
  than direct full-core forcing (`0.64`) — plausibly because the shell
  continues reinforcing the target heading via ordinary local coupling even
  after the explicit pulse ends, whereas directly-forced core birds have no
  such external support once released.

## Boundary comparison — how the four candidate interfaces relate

| | Coincide with `B^D` (true interaction shell)? |
|---|---|
| `B^F` (spectral/Fiedler) | **No** — strict subset on canonical flock, weak/variable overlap across flocks (mean Jaccard 0.12), not an adequate statistical substitute (+0.032 nats excess log-loss) |
| `B^{MB}` (statistical/predictive screening) | **Yes, exactly** — `B^D_0` IS the statistical Markov blanket, by construction and by direct empirical verification (0.0000 excess log-loss) |
| `B^C` (empirical control-response ranking, single-bird or pairs) | **Partially** — high responders are enriched within `B^D_0` but individual/pairwise ranking alone never predicted that forcing the FULL shell jointly would succeed; no pair from the full 3160-pair space comes close |

**The most scientifically valuable outcome, confirmed**: the spectral and
dynamical interfaces do **not** coincide, and the useful control interface is
the one derivable directly from the model's own update structure — not the
one the paper's own spectral method identifies.

## V2 result

See `v2_interface_control/RESULTS_V2.md` for full detail. The frozen V2
policy (compute `B^D_0` from structure for each flock; force
`k=ceil(0.75|B^D_0|)` actuators chosen by one of four transparent rules) was
applied, unmodified, to the first 10 independently-emergent qualifying flocks
(seeds 2,3,4,8,9,10,11,13,14,16 — found by scanning seeds 0-16 in order,
since not every seed qualifies). Mean `P(success)` across all 10 flocks:
**full shell 0.983, Rule A (degree) 0.940, Rule B (leverage) 0.940, Rule D
(random-from-shell) 0.920, Rule C (connected patch) 0.783**, vs. baseline
(no control) 0.010. Two findings stand out:

1. **The `0.75`-of-shell fraction, derived from ONE flock, generalizes well**:
   9 of 10 flocks reach `P(success)>=0.83` under at least three of the four
   rules. The one partial exception is, strikingly, **the canonical flock
   itself (seed 2, 0.60-0.77 across rules)** — independently the hardest of
   the 11 flocks examined in this whole study, consistent with
   `v1_mechanism_audit/V1_RECORD_AUDIT.md` section A3 finding it an atypical,
   near-borderline spectral identification (94th-percentile `t0`,
   1.2-percentile eigengap). V1's original negative result was thus obtained
   on a harder-than-typical instance, compounding the "wrong interface
   searched" explanation with a secondary "somewhat harder flock" factor.
2. **Rule C (a single spatially-connected patch) is reliably the weakest and
   most variable rule** (dropping to 0.20 and 0.47 success on two flocks
   while every other rule stays >=0.77 on those same flocks) — concentrating
   the actuator budget on one contiguous arc of the shell leaves the rest of
   the core's boundary unforced. **Rule D (uniform random draw from the
   correct shell) performs nearly as well as the structured Rules A/B**
   (0.920 vs 0.940 mean) — supporting the interpretation that being in the
   physically correct interface matters far more than the precise
   within-shell ranking heuristic, provided the budget is not concentrated
   in one spatial patch.

`P(success & integrity)` under the original frozen criterion was **0.000 on
every one of the 50 (flock x non-baseline-rule) conditions tested** — this
replicates, and generalizes, the mechanism audit's Part D finding that the
zero-tolerance every-timestep coherence bar is structurally difficult for any
propagation-based (as opposed to direct-override) exterior control strategy
to satisfy jointly with target-heading success.

**Scope limitation, stated plainly**: because birds occupy fixed lattice
sites in this port, `B^D_t = B^D_0` for every `t` within one control episode
— the interface cannot literally move *during* a single steering attempt in
this model. What DOES vary, and is what V2 actually demonstrates, is that
**different flocks require different, structurally-recomputed actuator
sets** — i.e., the useful intervention is a *role* ("neighbor of the current
core"), not a fixed, hand-identified bird-ID list, even though within any one
episode that role happens to be static here. This is a genuine, partial
connection to the Stage-5 moving-boundary idea, not a full demonstration of
it — the full demonstration would need a model where the physical interaction
graph itself evolves (e.g. literal boids-style movement), which this port
does not implement (a stated, deliberate scope reduction inherited from
`METHODS_AUDIT.md`).

## Limitations

- **Port parity**: MATLAB/Octave remain unavailable in this environment
  (Octave install blocked by an interactive-sudo requirement, checked fresh
  this session). A deterministic cross-language fixture is ready for a
  collaborator to run (`v1_mechanism_audit/data/cross_language_fixture.json`,
  `v1_mechanism_audit/code/octave_fixture/run_fixture.m`), but no MATLAB-side
  confirmation exists yet.
- **Parameter ambiguity**: the paper's text and the released code disagree on
  `rho`/`omega`; this audit's Part G shows the disagreement is behaviorally
  material (0% vs 54% flock-qualification rate), not cosmetic. All V1/V2
  results use the code's actual defaults (`code_default`), which the Part G
  evidence suggests is what the paper's figures actually used — but this
  remains inferred, not confirmed by the authors.
- **Sample sizes**: most mechanism-audit and V2 numbers use "development
  scale" replicate counts (10-50/condition), explicitly below the protocol's
  stated 200+ final-comparison target, for this session's compute/time
  budget. Where an effect is large and clean (e.g., 0/3160 pairs succeeding,
  or 100.00% exact-match on the H2 structural check), replicate count is not
  the limiting factor; where an effect is closer to a threshold (e.g. some
  individual V2 flock/rule combinations near `p_success≈0.5-0.7`), a larger
  n would tighten the estimate.
- **High-dimensional CMI was not attempted**: Part H's empirical validation
  uses per-bird predictive log-loss with mean-field Monte-Carlo marginalization
  for the `B^F_0` conditioning set — an explicit, documented approximation,
  not exact joint conditional mutual information over the full 20-bird core.
- **Fiedler degeneracy**: at full polarization the heading-agreement graph
  becomes complete and `lambda2≈lambda3` (documented originally in
  `PORT_VALIDATION.md`); this audit's ensemble checks (Part C) additionally
  found at least one qualifying flock (seed 11) with an anomalously large
  spectral boundary (53 of 100 birds) despite a large eigengap — spectral
  boundary size is not a simple monotonic function of eigengap, a further
  reason to distrust `B^F` as a general-purpose control interface.
- **Static-lattice scope**: as stated above, this port's core physical
  assumption (fixed bird positions, heading-only dynamics) means the
  "adaptive vs. static shell" distinction (V1's Outcome 3) cannot be
  exercised within a single episode — only across different flocks.

## Next scientific experiments

Per the task brief's own sequencing, the retargeting/control problem should
be considered reasonably well understood (which interface, how sparse, why
V1 failed) before extending to:

1. **Resolving the integrity-criterion tension**: either accept that
   propagation-based control cannot satisfy an "always-coherent" bar and
   redefine what "integrity" should mean for indirect steering (a genuine
   `protocol_v3` design question, not a quick fix), or study whether a
   *staged* actuation schedule (e.g., ramping the forced set up/down rather
   than an all-or-nothing pulse) can reduce the transient coherence dip.
2. **A literal moving-boundary variant**: port the Reynolds-style spatial
   movement Reynolds' own boids formulation implies (birds change lattice
   position, not just heading) to actually exercise `B^D_t != B^D_{t'}`
   within a single episode — the natural next step toward the full Stage-5
   moving-interface analogy this port could only partially demonstrate.
3. **Merge / split / dissolve experiments**, as the task brief notes, only
   after the single-core retargeting problem above is on solid footing —
   which this audit + V2 now provide.
4. **MATLAB/Octave cross-validation**, whenever a collaborator with access is
   available, using the fixture already prepared.
5. **Confirm with Giovanni** which `rho`/`omega` values actually produced the
   published Figures 1-3, resolving the Part G ambiguity from the source
   rather than from inference.
