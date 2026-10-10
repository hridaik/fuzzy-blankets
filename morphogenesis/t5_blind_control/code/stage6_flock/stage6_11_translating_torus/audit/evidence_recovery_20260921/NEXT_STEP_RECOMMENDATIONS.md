# Next-step recommendations (implications only — Step 2 not performed here)

These follow directly from `audit_findings.md`. None are implemented in
this pass. Ranked by how directly the recovered evidence points to them.

1. **A forward, explicit material-continuity trace for seeds 501 and 502,
   independent of both v1's bare argmax and v2's softened-but-still-tracker
   -mediated pointer**, starting from the exact t0 qualified cohort and
   applying a disclosed, pre-registered continuity rule (not tuned on
   outcome) through to release. This is the one piece of evidence that
   would directly answer "did the originally selected flock physically
   turn" for these two seeds, which this pass explicitly could not resolve
   (`audit_findings.md` §5).

2. **Do not adopt a material-retention threshold from this pass's
   distribution plot.** The flagged-vs-ordinary R_old distributions overlap
   enough that no value is an obvious clean cut in this 5-seed sample
   (`audit_findings.md` §6); more data (more seeds, more steps) or a
   different formulation (e.g. combined with duration/persistence
   evidence, given seed 503's finding that duration matters more than
   selection) would be needed before treating retention as a sole
   validated identity criterion.

3. **If a confirmatory/controllability study (already-scoped as Parts J/K
   in `METHODS_AUDIT_6_11.md` §6) is run, use the blind `nearest_M20` pool**
   (`BLIND_POOL_AUDIT.md`, 100% recall parity with the oracle pool) and the
   **duration-matched authority estimand `A_S(τ,d)` with d matching the
   controller's actual hold length**, not the original one-shot `d=1`
   estimator — both are already implemented and validated in
   `audit/blind_pool_611.py` / `audit/authority_v2_611.py`, not novel work.

4. **Seed 503's real effect appears to be duration-driven, not
   selection-driven** (matched-random exterior nearly matches the
   algorithm's own choice). Any future controllability claim should
   include a duration-matched random-exterior comparator as a standing
   check, not an occasional spot-check, given how load-bearing this
   comparator turned out to be for the one unambiguous success in the
   5-seed sample.

5. **The `thingness_611.py` spatial-integrity gate is fully built,
   unit-tested, and simply never wired into qualification.** Whether wiring
   it in would change which seeds qualify (and when) is an open question
   `LINEAGE_FORENSICS_6_11.md` §6's own "possible, not established" list
   already names — worth prioritizing given how much of this audit's
   findings trace back to spatially-fragmented, MAP-unstable interiors
   qualifying for control unchecked.

6. **If the source of the reported seed-500 t=46→47 visual observation is
   later identified** (a specific figure, an older demo build, a different
   frame-indexing convention), it should be checked directly against
   `viz_bundle_611__seed500.json`'s recorded frames the same way this pass
   checked `interactive_demo/v2` — the method is cheap and already written
   (`code/derive_material_retention.py`'s frame-diff logic generalizes
   directly).

Nothing above is a redesign instruction; each is contingent on future
explicit scoping, per the task's Step 1 boundary.
