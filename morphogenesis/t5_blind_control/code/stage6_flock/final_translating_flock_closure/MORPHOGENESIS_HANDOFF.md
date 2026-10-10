# Morphogenesis Handoff

This note is for whoever starts the morphogenesis programme, possibly in a
fresh session with no memory of the translating-flock work. It summarizes
conceptual lessons to carry forward and infrastructure NOT to import
blindly. It does not design the morphogenesis experiment — that is out of
scope here.

## Carry forward conceptually

1. **Separate identity from outcome.** The single biggest source of wasted
   effort across Stage 6.9–6.12C was conflating "did the traced object stay
   the same object" with "did the intervention work." Build (or reuse) an
   explicit, audited identity/continuity tracker BEFORE measuring any
   intervention effect, and report identity validity as its own quantity
   (`V`, `V_conservative` here), never folded silently into a single score.

2. **Distinguish intervention efficacy from actuator selectivity.** "Does
   forcing ever change the outcome" and "does WHICH actuator you force
   matter, reproducibly" are different questions requiring different
   designs (paired-vs-baseline for the first; held-out/cross-validated
   comparison for the second). The flock program repeatedly found the
   first weakly true and the second essentially false — conflating them
   produced overclaimed early results (Stage 6.11's withdrawn "3/5
   successful" claim).

3. **Use held-out evaluation for any claim of selectivity.** A
   train/select-then-evaluate split (or genuine cross-validation) is not
   optional polish; it is the only thing that distinguishes real
   selectivity from noise-fitting. `stable_selectivity_analysis/
   CROSS_VALIDATED_ORACLE.md` shows a naive best-of-K selection can look
   like a 6.9× effect and collapse to statistically indistinguishable from
   zero under cross-validation.

4. **Avoid winner's-curse oracle claims.** Never report "the best
   candidate we found achieved X" as evidence that X is achievable by
   design — it is a maximum-of-noisy-samples statistic and will look large
   even when the underlying quantity has zero true signal
   (`ORACLE_WINNERS_CURSE.md`: the per-stream clairvoyant maximum is a
   MATHEMATICAL IDENTITY under a permutation null, not a physical effect).

5. **Distinguish geometric proximity from actual causal influence.**
   "Within radius R" and "actually influences the update" can be
   materially different relations (undirected/FOV-free vs. directed/
   FOV-gated, in the flock's case). Identify and use the SIMULATOR'S OWN
   true interaction/influence relation from the start; do not assume a
   convenient geometric proxy is equivalent to it (`CONTACT_METRIC_AUDIT.md`
   — this gap went unnoticed for three stages).

6. **Evaluate organizational role/class before searching individual
   entities.** If individual-entity selectivity search is expensive or
   noisy, first ask whether a CLASS of entities (by structural role, not
   identity) has a reproducible class-level effect — this is cheaper to
   validate and, if it fails too, is stronger evidence that no stable
   entity-level interface exists at all (see this stage's Closure A).

7. **Report persistence after intervention, not just immediate effect.**
   An effect measured only at the end of forcing can vanish, reverse, or
   turn out to coincide with organizational disruption (split/merge) once
   you look at the release window. Always score a late-release/persistence
   window separately from the forcing-window response.

8. **Preserve negative results.** Every stage's `CURRENT_RESEARCH_STATUS.md`
   entry documents what did NOT work, in the same voice as what did. This
   is what let later stages avoid re-testing already-falsified hypotheses
   (e.g. Stage 6.12C explicitly forbids re-litigating static
   actuator-feature discovery). Do the same for morphogenesis.

9. **Use conservative identity semantics when organizational continuity is
   ambiguous.** When an identity/continuity tracker flags a possible
   split/merge/interruption event, do not silently count that trace as
   "valid" for outcome scoring — report both an association-continuity
   variant (permissive) and a conservative variant (strict), the way this
   programme reports `J_assoc` vs `J_conservative` throughout, and treat
   the conservative one as primary.

## Do NOT import blindly from the flock programme

These are FLOCK-SPECIFIC design choices, tuned to this system's density,
interaction radius, and detector — they have no a priori reason to transfer
to a morphogenesis substrate, and re-using them without re-deriving is a
likely source of a subtle, hard-to-detect bug:

- **The nearest-20 exterior pool** (`nearest_M_pool`, M=20) — an arbitrary
  size chosen for the flock's own actuator-search budget, not a general
  principle.
- **The flock-specific Jaccard≥0.30 identity threshold** — calibrated
  against flock-specific false-positive/false-negative distributions
  (`LINEAGE_V2_METHOD_AND_VALIDATION.md`); a different substrate's identity
  ambiguity profile will require its own calibration.
- **The moving-flock field-of-view (FOV) assumption** — `live_edges`'
  half-plane-forward-of-heading rule is specific to a model with a single
  scalar heading per agent; a morphogenesis substrate (e.g. diffusing/
  dividing cells) may have no analogous directional asymmetry at all, or a
  completely different one.
- **The flock-specific intervention duration** (`d=8` primary, `R_RELEASE
  =24`) — tuned to this flock's relaxation timescale; re-derive from the
  new substrate's own dynamics.
- **The flock-specific boundary definition** (live-edge crossing the
  target/non-target membership set) — presupposes a well-defined discrete
  membership set updated every step, which may not be the natural
  representation for a continuous or fuzzy-boundary morphogenetic process.

Morphogenesis must define its own identity semantics (what counts as "the
same structure" over time), its own interface/boundary semantics (what
counts as an actuation-accessible entity), and its own effect/persistence
metrics, informed by the CONCEPTUAL lessons above but not by copying the
flock's specific numeric constants or code paths.
