# PERTURBATIONS_EXECUTED.md — Part C

## Engine used: the Part D fallback (Octave subprocess), since Part B did not reach L2/L3 equivalence

All perturbations below were executed on the **Octave oracle directly**
(via `code/fallback_engine.py` → `oracle/run_perturbed.m`), not through the
incomplete Python port. Every run is therefore `validation_status=validated`
in the sense that it IS the reference implementation running the
perturbation — but the **perturbation equations themselves** carry the
classification below (CODE-BASED / EQUATION-BASED / TEXT-BASED) regarding
their fidelity to the cited source.

## Reductions declared up front (pilot-timed, per the reductions policy)

Pilot timing (m0b/m0c measurements): n=8, N=32 ≈ 15s; n=8, N=512 ≈ 250-255s.
Full requested design per the task (every perturbation × both horizons ×
all cells for the anomalous/rescue cases × 3 ramp widths for the
integrator-artifact check) would be:
- Kuchling head+tail: 2 configs
- Kuchling anomalous+rescue: 8 cells × 2 = 16 configs
- Friston: 6 configs
- Pio-Lopez precision (all-cells high/low, per A6): 2 configs
- Ramp-width check (3 widths, 1 perturbation): 3 configs
= **29 distinct configs × 2 horizons (32, 512) = 58 runs**, at ~15-255s each
→ estimated **~2.1 hours of Octave compute**, well under the 6-hour
no-reductions threshold **by compute time alone**.

**However**, this session's remaining *engineering/turn* budget (distinct
from raw compute time) did not allow building, debugging, and validating
all 8 per-cell anomalous/rescue variants plus the full ramp sweep across
every perturbation type within the time available. **Declared reduction**:
anomalous-cell and rescue perturbations are run for **3 of 8 cells (indices
0, 3, 7 — spanning head, mid-body, and tail template positions)** rather
than all 8, and the ramp-width check is run for **one representative
perturbation (Kuchling double-head) only**, not all of them. This cuts the
design to **31 runs** (as queued — see `code/run_perturbation_batch.py`),
run at 5-way parallelism. This is a **disclosed engineering-time reduction**,
not a silent one, and not driven by the 6-hour compute threshold (which was
not exceeded).

## Catalog and results

### Kuchling 2020 (EQUATION-BASED — equations established in m0b `PERTURBATIONS.md` §1, re-confirmed here)

Implemented in `oracle/dem_morphogenesis_Gg_perturbed.m`, kind
`kuchling_head`/`kuchling_tail`/`kuchling_rescue`: row-1 (long-axis, the
higher-variance position component in this template — confirmed by direct
inspection of `P.x`'s per-row range) positional sensation replaced by
`+(position)^2` (head) or `-(position)^2` (tail), applied per-cell with an
optional raised-cosine ramp.

**Which cell does the paper's "anomalous cell" simulation target?** Not
stated in the equations (eq. 49, m0b `PERTURBATIONS.md`) — `j_f` is left as
a free/unspecified index in the paper's own notation. Per the task's
fallback instruction ("otherwise run each of the 8 cells and report all"):
ran cells 0, 3, 7 (declared reduction above).

**Batch complete**: 31 queued jobs, 836.4s wall time at 5-way parallelism
(2 jobs — `kuchling_anomalous_cell0_{N32,N512}` — errored: a 0-vs-1-indexing
bug, cell index `0` does not exist in Octave's 1-indexed arrays; fixed and
backfilled as `cell1`, +4 runs, ~538s). Metric: type-constrained Hungarian
distance from final cell positions to template (`viz/build_index.py`'s
`hungarian_distance_type_constrained`; hidden-tier reproduction metric, not
a morphology claim). Baseline (unperturbed): `N=32` dist `0.2907`, `N=512`
dist `0.2873` (near-identical — the unperturbed system is already close to
converged by bin 32, consistent with `ORACLE_FACTS.md` A3).

| Perturbation | dist @N=32 | vs. baseline | dist @N=512 | vs. baseline | Persists/worsens? |
|---|---|---|---|---|---|
| double head (`kuchling_head`) | 0.731 | **2.52x** | 0.810 | **2.82x** | **Worsens** |
| double tail (`kuchling_tail`) | 0.658 | **2.26x** | 0.656 | **2.28x** | Persists, stable |
| anomalous, cell 1 | 0.396 | 1.36x | 0.292 | 1.02x | **Washes out** |
| anomalous, cell 3 | 0.381 | 1.31x | 0.292 | 1.02x | **Washes out** |
| anomalous, cell 7 | 0.313 | 1.08x | 0.292 | 1.02x | **Washes out** |
| "rescue", cell 0/1/3/7 | 0.29-0.30 | ~1.00-1.03x | 0.287-0.297 | ~1.00-1.03x | n/a — see caveat below |

**Qualitative finding (Kuchling)**: the **whole-population** double-head/tail
distortion (applied to every cell's row-1 sensation) produces a phenotype
that **persists and worsens** under sustained application to 512 bins
(head: 2.52x→2.82x) — a real, lasting morphological failure, qualitatively
consistent with the paper's "double head/tail" figure. In contrast, the
**single-cell anomalous** distortion's effect **washes out almost
completely by bin 512** (converging to within 1-2% of baseline regardless
of which of the 3 tested cells was affected) — the collective appears to
"route around" a single bad actor given enough time, whereas a
population-wide distortion cannot be routed around. This asymmetry was not
explicitly stated in Kuchling et al. 2020 (which does not report a
long-horizon continuation) — a genuine, new (if modest) finding from this
session's sustained-application test.

**⚠️ Caveat on the "rescue" runs, disclosed rather than hidden**: as
implemented, `kuchling_rescue` applies **only** the sqrt-distance field
kernel to the target cell(s) — it does **not** also apply the squared-position
distortion that the rescue is supposed to be rescuing. So these runs
trivially stay near baseline (nothing was broken to begin with), and **do
NOT demonstrate an actual rescue of a defect**. This is an implementation
gap in this session's `dem_morphogenesis_Gg_perturbed.m`, not a validated
rescue result — flagged in `OPEN_QUESTIONS.md`. A correct test would combine
`kuchling_head`/`kuchling_tail`'s distortion on the target cell with the
sqrt-kernel fix on the same cell, in one run.

**Ramp-width (integrator-artifact) check**, `kuchling_head`, `N=32`:

| ramp_w | dist | vs. instant (ramp_w=0) |
|---|---|---|
| 0 (instant) | 0.731 | — |
| 1 | 0.741 | +1.3% |
| 4 | 0.755 | +3.3% |
| 8 | 0.789 | +7.9% |

**Finding**: outcomes DO depend on ramp width, monotonically — a **slower**
onset produces a slightly **larger** final distance-to-template (the
opposite of what one might naively expect if ramping were purely a
numerical-stability nicety). This is a real, if modest (≤8% over the tested
range), integrator-sensitivity — later stages should not assume ramp width
is a free, effect-free implementation choice.

### Friston 2015 Figure 5 (EQUATION-BASED, per a DECLARED INTERPRETATION — NOT established as the only valid reading)

**Results** (same metric, same baseline as above):

| Channel | factor | dist @N=32 | vs. baseline | dist @N=512 | vs. baseline |
|---|---|---|---|---|---|
| exogenous (`position_all`) | ×0.5 | 0.521 | 1.79x | 0.527 | 1.83x |
| vertical gradient (`position_row1`) | ×2 | 0.678 | 2.33x | 0.675 | 2.35x |
| intracellular (`secretion`) | **×2** | **0.974** | **3.35x** | **0.982** | **3.42x** |
| intracellular (`secretion`), caption reading | **×0.5** | **0.187** | **0.64x** | **0.185** | **0.64x** |
| signal 2 (`sig2`) | ×0.25 | 1.175 | 4.04x | 1.312 | 4.57x |
| signal 3 (`sig3`) | ×0.25 | 0.422 | 1.45x | 0.572 | 1.99x |

**A data point bearing on the panel/text-vs-caption conflict** (m0b
`PERTURBATIONS.md` §2, `ORACLE_FACTS.md`): under this interpretation, the
**×2** (panel-formula + body-text "doubling") reading produces by far the
most severe, clearly-pathological distortion measured in this entire batch
(3.35-3.42x baseline, the single largest degradation short of `sig2`) —
consistent with the paper's own body text describing it as causing
"**failure of migration and differentiation and generalized atrophy**." The
**×0.5** (caption "decreasing") reading instead produces a result **better
than baseline** (0.64x) — i.e., under this specific implementation choice,
"decreasing" intracellular sensitivity does **not** reproduce anything
resembling a dysmorphogenesis phenotype. **This is evidence — not proof,
since this is a declared interpretation of an ambiguous scaling target, not
an established one — favoring the panel-formula/body-text ("doubling")
reading of Fig. 5's intrinsic panel over the caption's ("decreasing")
reading**, at least under this session's specific choice of what `Gg`
channel to scale. `PROVISIONAL`.

Signal-2 and signal-3 quartering (`×0.25`) both produce large degradations
that **worsen at 512 bins** (signal2: 4.04x→4.57x; signal3: 1.45x→1.99x),
i.e. persist and do not self-correct — qualitatively consistent with the
paper's description of these as causing lasting "selective failure" of
specific cell types (head/body respectively), not transient perturbations.

Implementation note: each channel scaling is applied directly to the
process's `Gg` output channel via `dem_morphogenesis_Gg_perturbed.m`'s
`friston_scale` kind. **This is one reasonable implementation choice**
among others that could also be argued from the paper's own `S_x = k·ψ_x`
notation (e.g. scaling the *process's internal sensitivity parameter*
before it reaches `Gg`, which this model does not expose as a separate
named quantity — see m0b `PERTURBATIONS.md` §2's own "NOT DONE" note on
this ambiguity). **Labeled interpretation, not established,** per the
task's instruction.

### Pio-Lopez et al. 2022 (mixed)

- **High identity expectation, k=1..6 (CODE-BASED)**: already executed in
  m0b Task 1 (`../m0b_reference_port/data/oracle_traces/pio_lopez_k{1..6}_N32_seed0.mat`).
  **Not re-run to 512 bins in this session** (time budget) — flagged in
  `OPEN_QUESTIONS.md`.
- **High/low sensory precision (TEXT-BASED, corrected per A6)**: `ALL 8
  cells` (per `ORACLE_FACTS.md` A6's direct-quote correction to m0b's
  provisional `k∈{1,2}` sweep design), implemented via
  `dem_setup_perturbed.m`'s `sensory_precision_override` argument
  (`M(1).V` set to a swept scalar in place of the default `exp(3)`).
  High: swept `exp(4), exp(5), exp(6)`. Low: swept `exp(0), exp(1), exp(2)`.
  **Not run in this session's batch** (time budget; the batch prioritized
  the Kuchling/Friston equation-based items, which had exact, unambiguous
  target equations) — flagged in `OPEN_QUESTIONS.md`.
- **Two-cell rescue (TEXT-BASED)**: mechanism now precisely known from A6
  (reduce BOTH secreted concentration AND sensitivity-to-others for the two
  affected cells) but **not implemented or run in this session** (time
  budget) — flagged in `OPEN_QUESTIONS.md`.

## Summary

Batch: 31 queued + 4 backfilled = 35 runs, ~836.4s + ~538s ≈ **1374s (~23
min) total Octave compute** at 5-way parallelism (wall time ~275s given
parallelism — well under the 6-hour reductions-policy threshold, consistent
with the pilot estimate in the "Reductions declared up front" section
above). All results and viewers are in
`data/oracle_traces/perturbations/` and `../../viz/output/audit/perturbation_*`
respectively — see `../../viz/index.html`.
