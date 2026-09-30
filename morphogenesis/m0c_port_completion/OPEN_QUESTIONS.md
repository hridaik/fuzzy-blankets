# OPEN_QUESTIONS.md

Consolidated from every `NOT DONE`/reduction in this stage's deliverables.

1. **The full joint `dFduu` local-linearization solve was not ported.**
   (`EQUIVALENCE_REPORT.md`.) This is THE blocker for L2/L3 equivalence and
   for retiring the fallback engine in favor of a validated Python port.
   Concrete next step: construct the `dVduv`/`dVdua`/`dVdav`/`dVdau`
   cross-coupling blocks (currently missing from `code/dstep.py`) and the
   `Dp`/`Dq` shift-operator bookkeeping for the full `{p,q}` state stack,
   then re-test against `../m0b_reference_port/data/oracle_traces/dstep_dump_bin1.mat`
   and this stage's `data/oracle_traces/b1_dump.mat`.
2. **Pio-Lopez high-identity k=1..6 was not re-run to 512 bins** this
   session (already had 32-bin Octave traces from m0b Task 1).
3. **Pio-Lopez high/low sensory-precision sweeps (all 8 cells, per the A6
   correction) were not run** this session — design and code path exist
   (`dem_setup_perturbed.m`'s `sensory_precision_override`), just not
   executed, due to time budget after prioritizing the equation-based
   Kuchling/Friston items.
4. **Pio-Lopez two-cell rescue was not implemented or run** — mechanism now
   precisely known (A6: reduce both secretion and cross-sensitivity for the
   2 affected cells) but not coded.
5. **Kuchling anomalous-cell/rescue perturbations ran for 3 of 8 cells**
   (0, 3, 7), not all 8 — declared reduction, `PERTURBATIONS_EXECUTED.md`.
6. **The ramp-width (integrator-artifact) check ran for one perturbation
   only** (Kuchling double-head), not all of them — declared reduction.
7. **The Friston Figure 5 `friston_scale` implementation is one interpretation
   among others** (scaling `Gg`'s output channel directly, rather than an
   internal sensitivity parameter the model doesn't separately expose) —
   labeled as such, not resolved to a single "correct" reading.
8. **Octave-vs-Python synced viewer pairs were not built** — Part B did not
   reach a working Python trajectory (L2 failed), so there is no Python
   rollout to pair against the Octave oracle in the viewer. The viewer's
   Octave-only content (A3, A4, Part C perturbations) was built instead.
9. **The `kuchling_rescue` perturbation, as implemented, does not test an
   actual rescue.** It applies only the sqrt-distance field-kernel fix,
   without pairing it with the squared-position distortion it is meant to
   rescue — so it trivially stays near baseline. `PERTURBATIONS_EXECUTED.md`
   discloses this. Fix: combine `kuchling_head`/`tail`'s distortion and the
   sqrt-kernel fix on the same cell in one perturbation kind.
10. **No live-browser rendering test of the viewer HTML** was performed
    (headless environment, no `node`/browser available) — only static
    checks (brace/paren balance, byte-size limit, template-substitution
    completeness). `VIEWER.md` discloses this.
11. **`morphogenesis/m0_reconstruction`'s data schema design was reused**
    (not its deprecated solver) for `code/storage.py` — if that stage's
    `DATA_SCHEMA.md` itself is ever revised, this stage's copy will drift
    and should be reconciled.
12. **A6's Xenopus-laevis pharmacological validation (thioridazine, §6 of
    the 2022 paper) was read but not connected to any simulation in this
    programme** — it is an experimental (wet-lab) result, out of scope for
    a simulator-fidelity stage, noted for completeness only.
