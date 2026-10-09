# PROTOCOL_V2.md — protocol v2 (all new M2a data); M1 data = "protocol v1"

## Clock (ESTABLISHED, R0.1; details and diff in CONTINUATION.md)
`s(b) = 1 − exp(−2 b / T_dev)`, `b` = absolute bin since the start of development, independent of N.
CANONICAL T_dev = 32 (published schedule); SECONDARY T_dev = 512 (M1's census clock). Adult = b ≥ b_adult = 10·T_dev = 320 (1 − s < 1e-8): the system is autonomous and its fixed point is exact (speed 0.0). The ramp is never frozen at an intermediate value.

## Continuation (ESTABLISHED, R0.2)
Adult interventions are continuations from the saved full D-step state on the same absolute clock; they never restart the ramp. Engine: `oracle/spm_ADEM_m2a.m` (state-exporting copy of SPM12 `spm_ADEM`, bit-identical on fresh runs). Splits at b0 = 64, 300, 320, 1000 reproduce the single run to 0.0; the null continuation from b = 320 stays at the fixed point to 0.0. The matched UNPERTURBED twin of every perturbed run uses the same protocol, clock, continuation point and horizon.

## Noise (R0.3; canonical = none)
Canonical data have zero process noise (`G(1).V = exp(16)`; SPM's `spm_DEM_z` returns zeros; verified bit-identical). The extension uses SPM's own mechanism: process-noise precision `G(1).V` (noise on the 80 sensory channels; `G(2).V`, the exogenous cause, is unused by the model and left at exp(16)), Gaussian smoothness `M(1).E.s = 1` bin, one noise realisation over the whole horizon indexed by absolute bin (segments of one run share it; split-vs-single control with noise: 0.0). Declared levels, chosen from a pilot (`data/r0/noise_*`) to give adult RMS positional fluctuation (RMS over cells and coordinates of the time-std of position, 300 bins after a 100-bin burn-in, 3 seeds) of 1%, 3%, 10% of the reference phenotype's mean nearest-neighbour spacing (0.880):

| Level | `G(1).V` | measured RMS fluctuation (3 seeds) |
|---|---|---|
| NOISE-L1 | exp(10.6) | 0.97%, 0.98%, 0.98% |
| NOISE-L2 | exp(8.4) | 2.92%, 2.95%, 2.93% |
| NOISE-L3 | exp(6.0) | 9.69%, 9.81% in two pilot seeds; 9.8% in the 6000-bin runs (NOISE.md) |
Reduction control: precision exp(16) is bit-identical to canonical (max abs 0.0 in positions and secretion). Noise data are always flagged and never mixed with canonical data.

## Declared constants
RAMP_W = 4 bins (raised-cosine on/off width, M1's recommendation); stationarity criterion (state-based; declared before any v2 analysis): per-bin speed = max(‖Δposition‖, ‖Δsecretion‖, ‖Δbeliefs‖) < 1e-6 for all later bins of the run, ≥ 32 bins at the end; time to stationarity = first bin of the final streak. Took-effect check: max over the on-window (+8 bins) of the RMS-over-cells index-wise position deviation from the matched twin ≥ 0.05 (as AUDIT_M1 0.1c). AN cell = individual index mod 8 (0-based), as M1 intended. Individuals: R1 primary 0–49 + secondary 0–9 (+ primary 0–9 at T_dev 512); R2 primary 0–19; R3 primary 0–4; R4 primary 0–3 (long runs) and 0–9 (reduced R2).

## Outcome taxonomy (v2)
Each perturbed run vs its matched unperturbed twin (same individual, clock, continuation, horizon):
- **SHAPE** (permutation-invariant d_pair to the unperturbed twin U and to the sustained twin S): REVERTED (d_U < τ, d_S ≥ τ) / PERSISTED (d_S < τ ≤ d_U) / NOVEL (both ≥ τ) / NONCONVERGED (not stationary at the end); if the sustained twin itself equals the unperturbed shape the run is flagged NO-SUSTAINED-EFFECT.
- **ROLES**: each cell is assigned to a reference-phenotype slot by Hungarian matching (position + secretion). SAME-ROLES if the assignment equals the twin's, else RELABELLED, with the number of cells whose slot differs and the cycle structure of the slot permutation between the two assignments.
- **TARGETED-CELL FATE** (single-cell interventions): whether the targeted cell's end slot differs from its twin's.
τ and the reference phenotype are calibrated/frozen in THRESHOLDS_v2.md after R1. tau_bel = 0.9 is retired. The template is audit-only.
