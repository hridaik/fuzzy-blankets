# Audit findings — Stage 6.11 evidence recovery, 2026-09-21

## 1. What historical code actually did

Confirmed by direct reading (not inference) of `code/lineage_611.py`,
`code/run_online_control_611.py`, `code/control_authority_611.py`,
`code/intervention_api_611.py`, cross-checked against the already-verified
0-mismatch replay in `LINEAGE_FORENSICS_6_11.md`:

- Identity is a **global MAP over a branching hypothesis tree**, read out by
  bare `argmax(prob)` with no margin, entropy, or confidence gate
  (`run_online_control_611.py:104-107`). This is exactly the mechanism the
  current handoff describes as "v1 identity could switch between unrelated
  branches because it used a global MAP over branching histories," and it
  is confirmed, not merely alleged: `LINEAGE_FORENSICS_6_11.md` §1.1 fully
  decomposes one instance (seed 500, t=20→21); this audit independently
  reconfirms it from raw frame data (see §6 below) and finds five more
  instances across the other four seeds (seed 500 t=39; seed 501 t=32; seed
  502 t=32,52,68; seed 503 t=35,47).
- The candidate/actuator pool for the causal probe and authority estimator
  is built from the **true interaction radius R** (`near_exterior`,
  `intervention_api_611.py:152-168`), a firewall violation the existing
  topology-leakage test suite does not catch because it checks import
  provenance, not information content (`METHODS_AUDIT_6_11.md` §2).
- The authority estimator that selects actuators evaluates a **one-shot,
  released-after-one-step** intervention, while the controller **holds**
  the same actuators forced for up to 8 consecutive steps — a genuine
  estimand/execution mismatch (`METHODS_AUDIT_6_11.md` §1.5), directly
  confirmed at seed 503 by comparing `old_set_one_shot` (transient blip)
  against `old_set_held_actual_duration` (large, persistent effect) using
  the identical actuator set.
- Actuator selection is plain top-K by individual authority with **no
  abstention floor** — ties (including exact-zero ties) are broken by pool
  list order, not by any secondary criterion (`METHODS_AUDIT_6_11.md` §4.7).
- The `thingness_611.py` spatial-integrity gate (component count,
  compactness, exterior contrast) is fully implemented, unit-tested, and
  **never invoked by any driver script** — qualification uses only
  persistence + size-fraction + net displacement (`LINEAGE_FORENSICS_6_11.md`
  §5). The tracked interior is spatially fragmented into multiple
  disconnected pieces at 96–100% of steps in every one of the 5 seeds,
  including all 3 originally-reported successes.

## 2. What "ID-independent rescoring" actually meant

Full reconstruction: `rescoring_provenance.md`. Summary: a single script
(`audit/branch_adjudication_611.py`) computing, per branch per seed, four
parallel readouts at end-of-control and end-of-release — `v1` (v1's own
membership), `v2` (v2's own membership, comparator only), `original_material`
(bird IDs frozen at trigger t0, no turnover allowed), and `field_direction`
(ALL birds within a fixed radius of v2's current centroid, membership-blind
once the centroid is fixed). A seed is called "controllable" only if a
reference (non-privileged-pool) branch shows a release-persistent rise
corroborated by `original_material` OR `field_direction` — a v1-only rise
is explicitly insufficient. This directly and correctly withdraws seeds
501 and 502 (v1-only rises, contradicted by every other readout on the same
branches) while correctly NOT withdrawing seed 503 (all four readouts
agree). One residual, disclosed-here-not-previously-flagged caveat: the
`field_direction` anchor's *location* depends on v2's own membership, so it
is not fully independent of tracker behavior, even though the *readout*
itself (once centered) counts all nearby birds regardless of ID — see
`rescoring_provenance.md`'s caveat section. This did not change either
seed's verdict in the actual data (both `original_material` and
`field_direction` agree in seeds 501/502), but is flagged as a residual
property of the "ID-independent" name, not a defect that changes any
number in this pass.

## 3. Seed-by-seed adjudication

See `seed_500.md` through `seed_504.md`. Compact cross-seed table:
`seed_summary.csv`.

## 4. Seed 500 t=20→21 and t=46→47

**t=20→21**: real, decomposed in full in `LINEAGE_FORENSICS_6_11.md` §1.1
and independently reconfirmed by this pass's frame-level cross-check
(zero displayed-interior overlap, 38→17 members). Mechanism: cross-branch
MAP-argmax overtake — the previously-displayed thread had a viable but
probability-diluted continuation (branching softmax split its mass across
two candidates); an independent thread had one undiluted, well-matched
continuation and won the argmax with only a 0.050 margin. This is a real
tracker defect (unguarded global-MAP readout), not a "no-death-state forces
a bad match" defect (a different, also-real, separately-confirmed defect,
`METHODS_AUDIT_6_11.md` §3).

**t=46→47**: **not substantiated by any recorded production or replay
artifact checked in this pass.** Interior is the identical 38-member set at
both t in `viz_bundle_611__seed500.json`, `interactive_demo/v2/data/
tab6_translation.json`, and the independently-replayed
`lineage_forensics_611__seed500__hypotheses.csv` (R_retain=R_purity=1.0,
not a flagged transition). No target has been set yet at this point in the
episode (`target_heading=None`; qualification occurs at t=61), so a
"tracker selecting an already-aligned flock" mechanism is not even possible
here regardless of tracker behavior. Centroid displacement between the two
frames is 0.28 spatial units — far below any torus-wrap scale (`L=24`).
**This is a genuine "the reported observation does not match any located
artifact" result**, reported as such per the stop-condition instructions,
not resolved into either "confirmed" or "refuted-and-explained." Two
non-adjudicated possibilities are noted in `seed_500.md`: a different
rendering path not covered by this pass's checks, or a frame-index/timing
misattribution (e.g. conflating this window with the real t=39 jump six
steps earlier, or the real t=61 qualification event fifteen steps later).

## 5. Seeds 501 and 502

**Did the originally selected material flock, allowing ordinary gradual
turnover, physically undergo the apparent turn?** Not established either
way by this pass. What IS established: both seeds contain at least one
genuine, zero-overlap displayed-membership break **inside their own control
windows** (501: t=32; 502: t=32, 52, 68) — meaning the v1 record alone
cannot support the claim that a single continuously-identified material
entity was qualified, then held, then observed to turn. A rigorous answer
requires an explicit forward material-continuity trace from the t0 cohort,
distinct from both v1's argmax pointer and v2's softened-but-still-tracker-
mediated pointer — this is exactly the kind of analysis flagged for Step 2,
not performed here (per the task's explicit instruction not to redesign the
identity method in this pass).

**Separately, intervention attribution**: in both seeds, the only branches
showing a large v1 rise (`beam_search_benchmark` for 501, same for 502)
show NO corroborating rise on `v2`, `original_material`, or
`field_direction` — the clearest evidence in the study that a v1-only
apparent success can be a pure identity-tracking artifact, independent of
whatever the material-continuity question above eventually resolves to.

**These two questions are kept separate, as instructed**: "does the
originally selected flock, allowing gradual turnover, physically turn" is
NOT established; "was any apparent v1 rise caused by the learned actuator
selection" IS established as negative for every tested branch in both
seeds (all evidence-gated repaired branches abstain; the one branch with a
real, corroborated rise anywhere in the study is seed 503, and there the
effect is shown to be duration-driven, not selection-driven).

## 6. Material-retention evidence

`data/material_retention_seed{500..504}.csv` (this pass's derivation,
frame-to-frame, from raw recorded interior lists — see
`code/derive_material_retention.py`'s docstring for exact method) and
`plots/*.png`. Zero-overlap-transition counts by seed: 500: 2 (both
pre-control); 501: 1 (during control); 502: 3 (during control/release);
503: 2 (during control); 504: 0. A simple binary rule ("any zero-overlap
transition marks a broken lineage") would flag 501, 502, and 503 alike —
i.e. it does NOT cleanly separate the one seed with a corroborated real
turn (503) from the two withdrawn seeds (501, 502) on zero-overlap alone.
The distribution plot (`plots/R_old_distribution_ordinary_vs_flagged.png`)
shows flagged transitions cluster at low R_old but with meaningful overlap
against the ordinary-step distribution's lower tail — **no single R_old
threshold value is visually obvious as a clean separator in this 5-seed,
~400-step sample, and this pass does not propose one** (per the explicit
instruction not to tune a threshold to rescue or reject any seed). This is
consistent with, not contradicting, the handoff's framing that a
material-retention criterion "may eventually solve a large part of the
identity problem" — it is a promising DIAGNOSTIC axis (it correctly flags
every genuine cross-branch overtake this pass checked), but is not yet
shown to be a sufficient SOLE discriminator for the turn/no-turn question,
which also depends on duration/selection-attribution evidence (seed 503)
that is orthogonal to material continuity.

## 7. Visualization audit

- **`geometry_611.torus_delta`** (`(a-b+L/2)%L - L/2`) is used consistently
  wherever this pass checked periodic distance computation: the production
  `field_direction_readout` (`branch_adjudication_611.py:173`), and the
  interactive demo's co-moving-frame rendering (`interactive_demo/v2/src/js/
  tab6.js:15`, byte-identical formula, JS `%` behavior confirmed equivalent
  to Python's for this expression). No inconsistency found between the two.
- **The demo's "World frame" pane plots raw, unwrapped positions.** A pair
  of torus-adjacent birds near opposite edges of the box can appear far
  apart in this view — an inherent property of any flat rendering of a
  periodic domain, not a bug, and it is already mitigated by the existing
  dual-pane design (the co-moving frame, centered on the tracked
  interior's own centroid via `torus_delta`, is the pane meant for
  continuity judgements; the world frame is for absolute-position context).
  This pass did not find evidence that any SCORING metric (as opposed to
  the world-frame display only) uses unwrapped distance — `field_direction
  _readout`, `LineageTracker611`'s own `R_retain`/`R_purity` (pure set
  arithmetic, position-independent), and `identity_69.estimate_translation`
  (bulk-translation alignment, torus-aware per its own docstring) were all
  checked.
- **No torus-wrap artifact was found at seed 500 t=46→47** (§4 above) —
  centroid displacement 0.28 units, far below wrap scale.
- This pass did **not** exhaustively audit every figure-generation script
  under `figures/` or the static `translating_collective_611.html`; only
  `interactive_demo/v2` and the raw data files were checked. If the
  originally-reported visual observation came from one of those unaudited
  paths, this pass would not have caught a bug there. Flagged as an
  explicit gap, not silently assumed clean.

## 8. Exact formulas and configuration recovered

See `code_provenance.md` and `intervention_timing.md`.

## 9. Contradictions with the current handoff

None found that require rewriting any historical number. One clarification:
the handoff states "the possibility that some previous adjudication or
visualization is misleading" motivated by the t=46→47 observation — this
pass's finding is that the ADJUDICATION (`branch_adjudication_611.py`,
`LINEAGE_FORENSICS_6_11.md`) is, if anything, MORE cautious than the
original result and internally well-corroborated (multiple independent
readouts agree at every seed where a claim is made); the specific
VISUALIZATION claim (t=46→47) is the one piece that could not be
substantiated against any artifact this pass located. This is reported as
a gap in evidence, not as a refutation of the handoff, since the source of
the original visual observation was not identified.

## 10. Remaining uncertainties

- **Source of the t=46→47 observation** — not identified; see §4.
- **Whether the originally-qualified material in seeds 501/502 physically
  turns, once a rigorous forward lineage trace (distinct from v1's argmax
  and from v2) is applied** — not established either way (§5).
- **Whether a material-retention rule, combined with something else (not
  yet specified), would be a sufficient identity criterion** — the
  retention signal alone does not cleanly separate 503 from 501/502 in
  this sample (§6); what additional criterion would be needed is not
  determined here.
- **Whether repairing the firewall violation (true-R pool) or the
  intervention-duration mismatch would recover a genuine detectable
  authority signal, or whether the true signal is simply weak/absent** —
  explicitly left open by `LINEAGE_FORENSICS_6_11.md` §9 and not
  addressed further by this pass.
- **Whether any figure/visualization path outside `interactive_demo/v2`
  contains a rendering bug** — not checked in this pass (§7).
