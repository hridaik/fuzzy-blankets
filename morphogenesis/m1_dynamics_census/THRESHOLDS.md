# THRESHOLDS.md

## Stationarity criterion (restated from m0c, made formal here)

m0c (`ORACLE_FACTS.md` A3/A4) established the process noise floor: marginal
std `≈ 3.35e-4` (`= 1/exp(8) = sqrt(1/G(1).V)`, `G(1).V=exp(16)`). This
stage's **formal, frozen stationarity criterion**: a run is stationary at
bin `b` if, for all `b' >= b`, the max per-bin displacement (Euclidean, all
cells' positions) AND the max per-bin secretion change (Euclidean, all
cells' 4 channels) are both below **`3× the noise floor ≈ 1.0e-3`**,
sustained for **32 consecutive bins**. This matches (and is now formally
adopted from) the threshold `m0_reconstruction`'s deprecated solver used
informally; here it is grounded in the actual measured noise floor rather
than an arbitrary round number. **`ESTABLISHED`** as this stage's operative
definition, timestamped **2026-09-30, before any Part B individual was
analysed** (though pilot individuals were run to gather the timing
statistics in `COMPUTE_PLAN.md` — those 8 pilot individuals ARE folded into
the 250-individual Part B census, not thrown away, since running them twice
would waste compute and the criterion itself does not depend on their
outcomes).

## Classification thresholds — INITIAL declared values (pre-census)

Per the task's ground rules, these are declared before seeing full census
results, then revised only from census *variability* (not cherry-picked to
produce a desired count), then frozen.

- `tau_pos = 0.25 × (minimum nearest-neighbour target spacing)`.
  Nearest-neighbour spacing computed directly from the `L=2` template
  (`decode_template()`): per-cell nearest-neighbour distances are
  `[1.414, 1.118, 1.118, 1.0, 1.0, 1.0, 1.0, 1.0]` (mean 1.081, **min
  1.0**). Using the **minimum** (not the mean) as the conservative,
  tightest-packing reference distance: **`tau_pos = 0.25 × 1.0 = 0.25`**.
- `tau_pair = tau_pos = 0.25` (same spacing-derived basis, per the task's
  instruction that both share the `0.25 × nearest-neighbour spacing` basis).
- `tau_bel = 0.9` (as declared in the task).

**Status: `PROVISIONAL` until revised from Part B census variability and
frozen below.**

## Frozen values

**FROZEN 2026-09-30 13:45 CEST, after full Part B census completion
(n=250: 200 primary + 50 secondary).**

Census variability inspected: `d_target` was found to be **essentially
constant across the entire population** — `0.2873` for every one of 250
individuals (both primary and secondary), and pairwise `d_pair` between any
two individuals' end-states `< 1e-12` (all 250 cluster as a single class at
every `tau_pair` tested, including `×0.5` and `×2`). **There is no
variability to revise the threshold from** — the population does not
contain a mix of "clearly assembled" and "clearly defective" individuals
whose boundary a threshold could be tuned against; it contains one outcome.
Per the ground rules ("revise only from census variability, then freeze"),
absent any such variability, **the initially-declared values are kept
unchanged and frozen as-is**:

- `tau_pos = 0.25` (frozen, unchanged)
- `tau_pair = 0.25` (frozen, unchanged)
- `tau_bel = 0.9` (frozen, unchanged)

**Threshold sensitivity result (part of the freeze decision, not a
post-hoc check)**: at `tau_pos × 0.5 = 0.125` and `tau_pos × 2.0 = 0.5`,
the classification is **unchanged — still 100% DEFECT** at both. The
per-cell residuals driving this (`{0.009, 0.132, 0.132, 0.296, 0.296,
0.335, 0.484, 0.615}` template-units, `CENSUS.md`) span a wide enough range
that even doubling the threshold does not reclassify any individual — the
largest residual (`0.615`) exceeds `tau_pos×2` too. **This is a robust,
threshold-insensitive finding, not an artifact of exactly where `tau_pos`
was set.**

Parts C-E (already partly executing at the time of this freeze, per the
compute policy's parallelism — see `COMPUTE_PLAN.md`'s addendum) are
classified against these frozen values.

## Sensitivity to thresholds (×0.5, ×2)

Every headline count in `CENSUS.md`/`ROBUSTNESS.md`/`WITHDRAWAL.md`/`SHAM.md`
is re-reported at `tau × 0.5` and `tau × 2` alongside the frozen value, per
the ground rules — see each document's "threshold sensitivity" subsection.
