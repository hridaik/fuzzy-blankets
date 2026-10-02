# SHAM.md — Part E

## Status: `ESTABLISHED`. Full 60-run batch complete (20 individuals × 3 timings), RMS-matched per-individual to their own SUSTAINED-DH twin.

## Result: sham ALSO reverts 100%, i.e. the floor is at 0% — same as the real perturbations

| Timing | n | outcome | mean `d_pair` to unperturbed twin | mean `d_pair` to SUSTAINED-DH twin | mean RMS matched |
|---|---|---|---|---|---|
| DEV-SHORT | 20 | 20/20 REVERTED | **0.0000** | 0.6951 | 1.3698 |
| DEV-LONG | 20 | 20/20 REVERTED | **0.0000** | 0.6951 | 1.3698 |
| ADULT | 20 | 20/20 REVERTED | **0.0000** | 0.6951 | 1.3698 |

**Every sham run reverts exactly to the unperturbed twin**, identically to
every real DH/DT/AN withdrawal run (`WITHDRAWAL.md`). The RMS-matching
calibration worked as intended (mean matched RMS `1.3698`, consistent with
the manually-checked value `~1.369` for the canonical individual — a real,
substantial distortion magnitude, not a negligible one; confirmed
functional this session via a direct test showing a sham field produces
position deviations from baseline comparable in order of magnitude to DH's
own effect).

## The floor comparison

Per the task: sham rows are the floor any real withdrawal effect must
exceed. **Both the floor (sham) and every real perturbation (DH/DT/AN) sit
at exactly 0% PERSISTED/NOVEL rate** — there is no "signal above floor" to
report because neither the real perturbations nor the sham control produced
ANY durable effect. This is not a null result *due to* an inadequate sham
(the sham WAS a real, RMS-matched, substantial distortion, confirmed
functional) — it is consistent with `WITHDRAWAL.md`'s own finding that this
model's dynamics revert essentially unconditionally once a transient
distortion is removed, for perturbations of this magnitude and duration.

**No paired individual-level comparison of PERSISTED rates is meaningful
here** (0/20 vs 0/20 in every cell) — there is nothing to compare
statistically beyond confirming both are at floor, which the raw counts
already show unambiguously.

## Threshold sensitivity

As in `WITHDRAWAL.md`: `d_pair` to the unperturbed twin is exactly `0.0`
for all 60 sham runs, so the REVERTED classification is completely
insensitive to `tau_pair×0.5` / `×2`.
