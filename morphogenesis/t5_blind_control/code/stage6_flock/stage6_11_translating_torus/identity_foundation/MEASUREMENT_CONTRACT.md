# MEASUREMENT_CONTRACT.md

Full detail for the summary given in `IDENTITY_MODEL.md` §10 (spatial
measurement contract). This document is the single place that freezes
scale definitions, metric return shapes, and missingness handling for
everything the identity instrument reports — so that "G and L mean the
same thing everywhere," which the mandate notes earlier stages violated,
is actually true here. Nothing in this document is implemented yet; it is
the contract Phase 2's calibration and Phase 3's instrument panel must
both honor.

## 1. Four independently declared scales

No two of these may be defined in terms of each other, and none may be set
equal to (or silently derived from) the simulator's true interaction
radius `R` — that is the exact "privileged-radius" failure mode
`CLAIMS_LEDGER.md` item A6 documents for the control pool, generalized
here to every other place a "how far is local" decision gets made.

| scale | current value (as found in the codebase, §10 of `IDENTITY_MODEL.md`) | what it answers | what it must NOT be used for |
|---|---|---|---|
| **Detection scale** | `detect_69`'s affinity kernel: `SIGMA=1.1`, `KERNEL_CUTOFF=3.3` | "are these two birds close enough that a candidate-proposal mechanism should consider linking them" | morphology/compactness diagnostics (that is the next row's job) |
| **Field-smoothing scale** | `identity_69.field`'s `KERNEL_SIGMA = 0.9` (Gaussian smoothing kernel width, `identity_69.py:30`; the field grid extends `3*sigma` beyond each member's bounding box, `identity_69.py:54`) — confirmed by direct read this pass | how coarsely the co-moving phenotype descriptor smooths raw positions into a density/shape field | detection or morphology (a separate, narrower-purpose kernel) |
| **Morphology scale** | ADOPTED as the detection scale itself (3.3 units), per `THINGNESS_GATE_AUDIT.md`'s diagnosis that `geometry_611.local_scale` (≈0.2–0.3 units) answers a different, finer question ("individuation-band width") and produces spurious fragmentation (13–24 components) when misused as the morphology radius | "is this candidate one spatially coherent thing at the scale it was proposed at" — component count, compactness `Q`, anisotropy | fine-grained individuation-band diagnostics (`local_scale`'s original, narrower purpose, retained separately if still wanted) |
| **Exterior/periphery sampling scale** | `nearest_M20` (position-only k-nearest, M=20), per `BLIND_POOL_AUDIT.md`'s finding that this blind rule matches the oracle-radius pool's causal-parent recall almost exactly, while the `local_scale`-derived radius pool is numerically unstable (median pool size 0→6→60.5→267.5 across a 5–40× multiplier sweep) | which non-member birds count as "the periphery" for exterior-contrast (`D`) and any future actuator-candidate sampling | anything requiring a metric (not count-based) neighborhood — `nearest_M20` is explicitly a count-based rule, not a radius, and inherits the corresponding limitation (returns birds arbitrarily far away in a sparse region) |

**Stability check (Phase 2 requirement, not asserted here).** Each scale
above must be re-run at ±20% of its stated value on the synthetic
validation suite (§2 of `VALIDATION_PROTOCOL.md`, once written) and shown
to produce qualitatively stable component counts / contrast values /
existence calls — not merely reported once at a single setting. A scale
whose output changes sharply under ±20% perturbation is flagged, not
silently accepted merely because it happens to match some other quantity.

## 2. Metric return contract

Every metric this instrument reports — `C` (internal coherence), `G`
(predictive-boundary generalization gap), `L` (certified boundary
log-loss), `D` (exterior contrast), `Q` (compactness), existence
probability `e_ell`, membership probability `w_i^ell`, association
probability for any given candidate — returns a structured record, never a
bare number:

```
{
  value: float | None,
  valid: bool,
  effective_sample_size: int,        # 0 if valid=False
  computed_at: int,                  # simulator step t this was computed for
  staleness: int,                    # t_now - computed_at (0 if fresh)
  uncertainty: float | None,         # None if not estimated at this cadence
}
```

**Rules, stated once, applied everywhere:**

- `valid=False` (never a fallback numeric default) whenever the input to a
  metric is genuinely absent — e.g. an empty periphery for `D`, zero
  candidates for existence, a boundary construction that never terminates
  within its declared cap for `G`/`L`. This is the direct fix for
  `geometry_611.local_exterior_contrast`'s confirmed defect
  (`THINGNESS_GATE_AUDIT.md` §3): its `return 1.0` fallback on an empty
  periphery manufactured a false "perfectly distinct periphery" reading
  that was, for a time, treated as corroborating evidence
  (`LINEAGE_FORENSICS_6_11.md`, before retraction). No metric in this
  contract may special-case an empty/absent input to a value that would
  make a downstream gate pass.
- `effective_sample_size` reports the actual count behind the estimate
  (periphery birds found within the scale; rollouts used; held-out rows
  used for a certification bound) — not the nominal batch size requested.
  A caller MAY treat a low `effective_sample_size` as reason to widen
  `uncertainty` or refuse to gate on the value; this contract does not
  itself define that policy, only guarantees the number is available for
  one to be built on.
- `staleness` makes re-inference cadence visible on every output, not just
  in a log file — this generalizes the existing per-quantity age-tracking
  RESULTS_6_11.md §7 already does for `B_pred`/`B_causal`/authority
  (12/8/8-step cadences) to every metric in this contract, including the
  new identity-layer ones that have no precedent for it.
- `uncertainty` is `None`, not `0.0`, when a quantity has not been
  estimated with any dispersion measure at all (e.g. a point value read
  off a single deterministic computation with no resampling) — `0.0`
  asserts perfect certainty, which is a claim, not an absence of one.

## 3. Canonical meanings of `G` and `L`, frozen

Per the mandate's explicit instruction that earlier stages used
inconsistent definitions and this must stop:

- **`G`** = the predictive-boundary generalization gap
  `predictive_boundary_611`'s existing, already-validated `certify`
  procedure computes for a candidate's periphery — reused verbatim, never
  recomputed with a new definition inside the identity layer. `G` answers
  "does explicitly modeling this candidate's exterior sources reduce
  held-out periphery log-loss by more than the declared tolerance,"
  exactly the sense used in `RESULTS_6_11.md` §4 and re-certified in
  `BPRED_RECERTIFICATION.md`.
- **`L`** = the corresponding held-out log-loss the certified boundary
  achieves (the number the certification bound is computed against), same
  source module, same convention.
- Both are produced on `predictive_boundary_611`'s own re-inference cadence
  (12 steps, per `PARAMETER_DICTIONARY.md` §5), NOT recomputed by the
  identity layer on its own schedule — a candidate's `G`/`L` reading can
  be `staleness > 0` relative to the current step, and that staleness is
  reported (§2), not hidden.
- `thingness_611.passes_gate`'s existing convention — missing `G`/`L`
  reported as `None` in `checks`, distinguished from `False`, contributing
  to `all_evaluated=False` rather than failing the gate outright — is
  reused unchanged. The gate itself is not called in production today
  (`CLAIMS_LEDGER.md` item A4); this contract does not change that
  finding, only specifies what "wiring it in correctly" would have to
  preserve.

## 4. Missingness contract (summary; full case-by-case detail in `IDENTITY_MODEL.md` §10)

| situation | correct output | wrong output this replaces |
|---|---|---|
| No non-member bird within the periphery scale of any member | `D: {valid: False, effective_sample_size: 0, value: None}` | `D = 1.0` (the confirmed, retracted `geometry_611.local_exterior_contrast` fallback) |
| Candidate spans the whole population (no "outside" exists) | same as above | `D = 0.0` (the mirror-image wrong default, never actually observed in the codebase but explicitly forbidden here too) |
| Boundary construction hits its cap (`K_max=12`) before converging | `G`/`L` reported with `valid: True` but an explicit `capped: True` flag and the disclosed caveat that the boundary may be larger than `K_max` (already `RESULTS_6_11.md` §4's own disclosed behavior — reused, not weakened) | silently treating the capped result as if it were the converged boundary |
| A candidate has zero viable continuation candidates this step | `association: unresolved` (§7's "missed/ambiguous observation" event), existence held steady, position/shape uncertainty inflated | forced continuation onto the least-bad available candidate (v1's confirmed defect, `CLAIMS_LEDGER.md` item A3) |
| Two enumerated global hypotheses are pruned away by the `K`-hypothesis truncation (§5 of `IDENTITY_MODEL.md`) | their combined mass is added to an explicit, reported `unaccounted_mass` figure | assuming pruned mass is zero |

## 5. What this document does not settle

Whether the adopted morphology scale (3.3 units, same as detection scale)
actually produces a non-degenerate, useful spatial-integrity gate at the
primary regime's real densities is a Phase 2 calibration question — flagged
identically in `IDENTITY_MODEL.md` §12, not re-asserted as resolved here.
