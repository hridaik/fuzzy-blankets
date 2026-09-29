# OPEN_QUESTIONS.md

Consolidated from every `NOT DONE` in this stage's deliverables, ordered by
what blocks the most follow-on work.

1. **`spm_ADEM_diff.m`'s higher-generalized-order recursion** (`u.v{i}` on
   both sides of its own update for `i>=2`) was not resolved with
   confidence. This is the single blocker for L2/L3 equivalence, full-power
   characterization, and the Python side of the viewer. `PORT_DESIGN.md`
   gives a concrete, small next step (instrument `spm_ADEM_diff.m` itself,
   the same technique that caught this session's one actual error in
   `spm_DEM_embed`'s boundary case).

2. **`model.Mg`/`model.Gg` were not cross-checked live against Octave's
   `dem_morphogenesis_Mg.m`/`Gg.m`** on an identical `v`/`a` in this
   session (the formulas are unchanged from `m0_reconstruction`, which did
   verify them against source text, but not against live Octave numeric
   output). Low-risk, quick to close.

3. **Figure 3 (2015 paper) sanity check was qualitative only** (narrative
   match: dispersion, differentiation by ~bin 8, falling free energy — all
   confirmed). Pixel- or value-level comparison against the actual published
   figure image was not attempted.

4. **Friston 2015's five (six, with the intracellular conflict) sensitivity
   perturbations have no known code implementation anywhere fetched** in
   either this stage or m0. Confirmed absent again this session. If a future
   stage wants to implement them, the open design question is which
   generative-**process** Jacobian term each of `ψ_x`, `ψ_x1`, `ψ_s`,
   `ψ_c2`, `ψ_c3` corresponds to in the SPM `Gg` formulation — not resolved.

5. **Pio-Lopez 2022's high/low-precision and two-cell-rescue perturbations**:
   sweep values are provisionally declared (`PERTURBATIONS.md` §4) but the
   "two-cell rescue" mechanism's specific textual description was not
   re-read from the 2022 paper's own PDF in this session (only the task
   prompt's summary was used, same gap as m0).

6. **The 2022 paper (Pio-Lopez et al.) was never independently fetched and
   read as a PDF** in either m0 or m0b — every claim about it traces back to
   the task prompts' own summaries, not to primary-source verification. This
   is the largest remaining "trust but don't yet verify" gap across both
   stages.

7. **No Octave self-sensitivity control** (Octave vs. Octave+1e-10 initial
   perturbation) was run — needed before any future L3 deviation-growth
   analysis can distinguish port bugs from genuine chaotic sensitivity.

8. **Task 4's ramped onset/offset design** (`τ_pert(t)` reusing the
   developmental-sensitivity functional form) is a proposal, not validated
   against any published or textual ramping scheme — Kuchling et al. only
   warn against abrupt changes in prose, without giving an explicit ramp
   equation for perturbations specifically (their eq. 43 ramp is for normal
   development onset, not for perturbation onset).

9. **Task 5 (characterization) and Task 6 (viewer) were not started** —
   both explicitly require a validated port per the task's own wording
   ("validated port only"; "Octave-vs-Python synced comparisons"), which
   item 1 blocks.

10. **Runtime estimates for the full requested Task 4/5 scope** were given
    in `ORACLE_REPORT.md` for the *Octave* side only (~62 min for a full
    perturbation-config batch to 512 bins) — well under the 6-hour
    reductions-policy threshold. No estimate exists yet for the *Python*
    side (blocked on item 1) or for Task 5's E2/E3/E4 batches, which should
    be piloted and reported before execution once the port is unblocked.
