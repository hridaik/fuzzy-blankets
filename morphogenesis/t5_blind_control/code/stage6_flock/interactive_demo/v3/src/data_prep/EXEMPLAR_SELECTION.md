# Tab 6 (Translation) exemplar selection — v3

This note documents which (state, actuator, physics-stream) tuples
`prep_tab6_translation_v3.py` replays for the Translation tab, and why, per
the final programme findings in `stage6_flock/TRANSLATING_FLOCK_FINAL_SYNTHESIS.md`
and `stage6_flock/CURRENT_RESEARCH_STATUS.md`.

## Why not seeds 500-504

Seeds 500-504 are v1 (`LineageTracker611`)'s own historical seed set, and
two of them (502, 503) are v1's own documented failure cases (a
wrong-population transfer and a tracker substitution/material-fragmentation
event respectively — see `CURRENT_RESEARCH_STATUS.md`'s "Established
findings"). Once v1 is demoted to a secondary/historical role (or dropped —
see below), re-using its own seed set as "the" translation exemplars no
longer makes sense: they were never sampled or intended as exemplars of the
final, frozen `ForwardMaterialTrace611`-based protocol. All new exemplars
below are drawn from the CONFIRMATORY seed manifests that were qualified
under the frozen K=1/d=8/release=24 protocol used throughout Stage 6.12C and
the final closure.

## v1 dropped entirely from this tab

Tab 6 now shows `ForwardMaterialTrace611` only, with no v1 toggle. v1's
historical narrative (the withdrawn "3/5 successful blind adaptive
controls" claim, its wrong-population-transfer failure modes) is already
carried in Tabs 1/2's historical material and in this tab's own provenance
panel; re-deriving v1 against the NEW confirmatory seeds would require
re-running the complex probabilistic MAP-over-branching-histories tracker
(`LineageTracker611`) purely to show it disagreeing with the now-primary
identity layer — extra implementation risk for a comparison the program has
already made definitively (`material_identity_step2_20260921/`,
`causal_reconciliation_step3_20260922/`) on the ORIGINAL seeds. Dropping it
here simplifies the fix and avoids re-litigating a closed question on new
data it was never validated against.

---

## Second-pass curation (this revision)

The first v3 pass (5 exemplars: `64206_a346`, `64203_a174`, `63203_a237`,
`63203_a372`, `63201_a266`) was mechanically sound — every replayed
`delta_J_conservative` exactly matched the recorded value in
`closureAB_rollouts.json` / `k1_rollouts_612c.json` — but the CURATION was
poor. Reviewer feedback, verbatim:

> "the split/merge case doesn't actually look like a split. The control in
> all of these cases looks like absolutely nothing... none of the
> collectives actually move to the target heading... It is also missing
> the scanning phase, adaptive control with multiple actuators, actual
> success for the one marked clean is also not apparent... the samples
> should span success, failure, and be such that you can see why... These
> need to be chosen more carefully, and verified through a separate method
> than what our blind tracker/controller says."

Independently confirmed before starting this pass (see the parent task's
own investigation, not re-derived here): the physics replay itself is
numerically exact (cross-checked against `k1_rollouts_612c.json`'s
`target_size_end` — exact match); the problem was entirely curation, not a
simulation bug. The previous "split" exemplar had exactly one flagged
frame out of 33 buried in constant population churn; the previous "clean
success" case's `frac_at_target` only rose in the final ~5/32 frames, long
after the actuator (active only t=0–7) was released — not a
forcing-window-aligned effect.

### The scan

`scan_candidates.py` (run from scratch, not committed — see below) pulled
a 48-tuple pool spread across 8 `612c` states (0,1,2,3,5,6,7,9) and all 8
`closure` states, 3 candidates per state (worst / near-median / best
`delta_J_conservative` from the already-recorded summary rows in
`k1_rollouts_612c.json` / `closureAB_rollouts.json`), and FULL-replayed
every one of the 48 with the exact frozen protocol
(`intervention_612.simulate_branch` + `trace_target` + `outcome_metrics`,
`intervention_612b.add_conservative` — same code as the production script,
nothing reimplemented), recording every frame's `split_flag`/`merge_flag`,
population size, and target-heading-fraction trace.

Results (full text preserved in the task record): of 48 replays, 11 had at
least one `split_flag` frame, but only **2** had ≥2 split-flagged frames
(the bar for "not just a single buried advisory tick"):
`612c state_idx=3, actuator=319, stream=6` (flags at t=9, t=22) and
`closure state_idx=2, actuator=270, stream=1` (flags at t=19, t=26, t=31).

### Independent verification (not trusting `split_flag` at face value)

For BOTH multi-flag candidates, raw bird positions were plotted directly
with matplotlib at frames straddling each flagged split — every bird
colored by "in traced members at t and t−1" (blue), "newly in members"
(green), "left members" (orange), actuator in red, everything else grey —
and the images were read and inspected (not just the flag counted):

- `612c s3 a319 r6`: the t=9 flag corresponds to a small, loosely-scattered
  orange smear immediately adjacent to the main blue cluster, not a
  clearly separated second cluster. **This candidate was discarded** — the
  flag fires, but the visual signature is ambiguous/weak, not a convincing
  bifurcation.
- `closure s2 a270 r1` (**used**): at t=18 (pre-flag) the traced population
  is a single compact cluster (45 members). At t=19 (flagged) it visibly
  splits into two SPATIALLY DISTINCT groups — a blue cluster continuing up
  top and an orange (departed) cluster clearly separated below-right — and
  the tracker follows the larger group (25 members), leaving the smaller
  one exterior. This pattern (recombine → re-split) repeats at t=26 and
  t=31, each time with the same clean spatial bifurcation visible in the
  plot. **This is a genuine, visually-confirmed, multi-frame split
  signature**, not a single advisory tick — used as the split exemplar.
  (Plots generated at
  `/tmp/.../scratchpad/plots/splitB_closure_s2_a270_r1.png` during this
  session and re-rendered live in the actual Tab 6 UI via Playwright —
  screenshot at t=40 (protocol t=25, mid-split) shows the same two-cluster
  split directly in the app, not just in the standalone check.)

For a genuine SUCCESS candidate, `ORACLE_DECOMPOSITION.md`'s finding that
individual streams can realize large effects (state-clustered outcome-
oracle mean ≈0.022, ~6.9× random) was used to target the search: state
`s612c_02` has the single largest outcome-oracle value in the whole table
(0.114). Sorting that state's own confirmatory rows by `delta_conservative`
surfaced `candidate=357, stream_idx=6` at **+0.8563** — by far the largest
of any candidate found in this session's scan. Independent verification
(not just trusting the summary number): full per-frame
`frac_at_heading(traced members)` was computed and plotted —

```
t:     0     1     2     3     4     5     6     7     8     9    10 ...
frac:  0.04  0.00  0.00  0.00  0.04  0.04  0.00  0.26  0.23  0.31  0.42 ...
```

— the fraction visibly rises FROM WITHIN the 8-step forcing window (0.00 →
0.26 by t=7, the last forcing step) and continues climbing through release
to 0.93 by the end. A second, fully independent check — the fraction of
**ALL** birds (not just traced members) at the target heading — also rises
monotonically over the run (0.22 → 0.32), confirming the shift is a real
population-level heading change, not an artifact of which birds the
tracker happens to be following. **Used as the success exemplar.** This is
shown explicitly as a genuine large realization, not a reproducible
strategy — no predictor in the programme (kinematic, organizational-role,
or search-selected-best) reliably finds cases like this in advance
(`ORACLE_DECOMPOSITION.md`'s Case C: the effect is real but not explained
by anything tested, including physical contact).

For a **structural "no actuator of the relevant class available"**
failure, `final_translating_flock_closure/data/closureAB_class_availability.json`
was read directly (not re-derived): 5 of 8 closure states
(`sclosure_00/01/02/04/07`) have ZERO `boundary_member` and ZERO
`live_exterior_parent` candidates. `sclosure_00` (state_idx=0) was picked;
its only two available classes are `core_member` and
`near_exterior_non_parent`. Actuator 313 (near-exterior non-parent),
stream 1, was chosen from the already-recorded rollout rows
(`delta_J_conservative=-0.0243`, no split/merge flag) — a clean, honest
"this class of actuator was structurally never available here" case.

For an **ordinary/no-particular-reason failure**, `612c state_idx=6,
actuator=17, stream=6` was picked from the scan pool: no split/merge flag
anywhere in the run, an unremarkable (not kinematic-top, not
organizational-role-sampled) candidate, small negative
`delta_J_conservative=-0.0090` close to this state's typical realization.

The **kinematic-top-but-negative** exemplar from the first pass
(`63201_a266` → renamed `612c01_a266`) was kept — it was already
sanity-checked against the recorded data in the first pass and remains a
legitimate, disclosed finding (`PREDICTOR_VALIDATION.md`'s
top-vs-bottom-quartile reversal) — but its caption was corrected: the
first pass's caption quoted the state's 8-STREAM MEAN
(`delta_J_conservative=-0.0092`) as if it were this single displayed
realization's own outcome. The actually-displayed single stream (r=0) has
its own value, `-0.0037` — both numbers are now shown, labeled separately,
so a viewer cannot confuse a mean-over-8-streams with what is on screen.

### Final 5 exemplars

| key | source / state | actuator (class) | stream | ΔJ_conservative | ΔJ_assoc | event | what it shows |
|---|---|---|---|---|---|---|---|
| `612c02_a357` | `s612c_02_seed63202` | 357 | confirm r=6, seed 14002006 | **+0.8563** | +0.8563 | none | **Genuine strong success.** Largest effect found in the scan; `frac_at_target` rises during the forcing window itself and through release to 0.93 (independently plotted, both traced-member and all-bird fractions). Shown as a real large realization, explicitly NOT a reproducible/predictable strategy. |
| `sclosure02_a270` | `sclosure_02_seed64202` | 270 (`near_exterior_non_parent`) | confirm r=1, seed 40002001 | 0.0000 | +0.0466 | `material_split_flag` (3 flags: t=19,26,31) | **Visually confirmed split** (matplotlib + live UI screenshot both show two spatially distinct clusters at each flagged frame). Illustrates the conservative-scoring quirk: raw ΔJ_assoc is mildly positive, but ΔJ_conservative is forced to exactly 0 by construction for ANY split-flagged trial. |
| `sclosure00_a313` | `sclosure_00_seed64200` | 313 (`near_exterior_non_parent`) | confirm r=1, seed 40000001 | -0.0243 | -0.0243 | none | **Structural failure: no actuator of the relevant class was ever available.** This state has zero boundary-member and zero live-exterior-parent candidates at qualification (`closureAB_class_availability.json`, disclosed in `ORGANIZATIONAL_ROLE_RESULTS.md`). Actuator shown is the best-available class; control still fails. |
| `612c06_a17` | `s612c_06_seed63206` | 17 | confirm r=6, seed 14006006 | -0.0090 | -0.0090 | none | **Ordinary/no-particular-reason failure.** No split flag, unremarkable candidate, near-median outcome for this state. Honest "sometimes nothing distinctive is going on" case. |
| `612c01_a266` | `s612c_01_seed63201` | 266 (kinematic-top) | confirm r=0, seed 14001000 | -0.0037 (this stream) / -0.0092 (8-stream mean, disclosed separately) | -0.0037 | none | **Kinematic-predictor reversal, caution case.** The deployable predictor's own top pick on this state, and it is negative both for this single realization and on average — not "usually right but noisy." |

All five replay-checked exactly against the recorded confirmatory data at
build time (`sanity_check()` in `prep_tab6_translation_v3.py`):

```
[612c02_a357] replay check vs k1_rollouts_612c.json: recorded=0.8563 replayed=0.8563 OK
[sclosure02_a270] replay check vs closureAB_rollouts.json: recorded=0.0000 replayed=0.0000 OK
[sclosure00_a313] replay check vs closureAB_rollouts.json: recorded=-0.0243 replayed=-0.0243 OK
[612c06_a17] replay check vs k1_rollouts_612c.json: recorded=-0.0090 replayed=-0.0090 OK
[612c01_a266] replay check vs k1_rollouts_612c.json: recorded=-0.0037 replayed=-0.0037 OK
```

Physics-seed formulas (quoted from the source stages, not reinvented):
- Closure states: `physics_seed = 40_000_000 + state_idx*1000 + r` (`run_closureAB.py`).
- 612C states: `physics_seed = 14_000_000 + state_idx*1000 + r` (confirm streams,
  `run_confirmatory_612c.py`).

### Scanning (pre-qualification) lead-in

Checked directly in `world_sampling_612c.py` / `world_sampling_closure.py`'s
`try_world`: qualification runs from a fresh `np.random.default_rng(seed)`
draw at t=0, deterministically, for up to `t0` steps before the state
qualifies. `state_manifest_*.json` records both `seed` (the world-sampling
rng seed) and `t0` (the qualification step) for every state, but only
persists `r0`/`z0` AT qualification — not the intervening trajectory.

Since the process is fully deterministic given `seed`, that trajectory is
exactly reconstructible: `scanning_frames()` re-seeds
`np.random.default_rng(state["seed"])`, draws the same initial
`r`/`z`, and steps `mf.step` forward `t0` times using the SAME unmodified
`common_612.make_flock()`. This was bit-exact verified for 3 states before
being trusted (max abs position diff = 0.0, exact z match):

```
closure state2: t0=79  r match: True (max diff 0.0)  z match: True
612c state2:    t0=38  r match: True (max diff 0.0)  z match: True
closure state0: t0=66  r match: True                 z match: True
```

The last 15 steps of this reconstructed trajectory are shown as a
`phase="scanning"` lead-in before the control window, with no target
heading, no actuator, and no material trace (the real qualification
process has none of those either before `t0`) — captioned honestly in the
UI rather than inventing a membership narrative that doesn't exist yet.
All 5 exemplars' `t0` values (79, 38, 66, 119, 30) comfortably exceed 15,
so a full 15-frame lead-in was used uniformly.

### The K=1 / multi-actuator complaint

Confirmed this is not a demo limitation: K=1, d=8-of-32-steps is the
literal frozen confirmatory protocol used throughout Stage 6.12C and the
final closure (see `CONFIRMATORY_PROTOCOL.md`) — the headline finding of
the whole programme is that no static actuator-selection strategy reliably
beats random, and this negative result is the actual science, not a demo
artifact. A K=2 secondary arm DOES exist and IS frozen/validated
(`K2_SECONDARY.md`: top-predicted pair vs. random vs. low-predicted pair,
6 confirmatory streams/pair) but is similarly unreliable (90% CI spans
zero) — reusing it would not change the "control doesn't visibly work"
impression the reviewer flagged, and plumbing a second highlighted
actuator into the existing single-actuator-per-frame schema/rendering was
judged not worth the implementation cost for that reason. Instead, Tab 6's
header caption, its Summary card, and its provenance panel now explicitly
state (a) this tab deliberately shows the frozen K=1 singleton protocol,
(b) a K=2 arm exists and was also found unreliable, and (c) genuine
multi-actuator/adaptive/online control is Tab 5's subject, not this tab's.

## What this set intentionally does NOT do

- It does not cherry-pick only positive outcomes. Two of five realizations
  are failures with different, legible causes (no actuator of the relevant
  class available; ordinary/no particular reason); one is a
  visually-confirmed split with a near-zero conservative outcome; one is a
  genuinely strong positive realization; one is a caution case showing the
  best deployable predictor getting it wrong.
- It does not claim K=1 or the kinematic score are validated/deployable —
  every caption says so explicitly, and the K=1-only choice is now
  explained in-tab, not left implicit.
- It does not substitute a different, better-looking population for the
  traced target at any frame, including in the split exemplar —
  `material_members` at every `t` is exactly
  `tr.history[t].accepted_members` from the live `ForwardMaterialTrace611`
  replay, nothing smoothed or hand-picked.
- It does not fabricate the scanning lead-in — it is a bit-exact replay of
  the actual qualification rng, verified against the recorded r0/z0 before
  being trusted, with no membership/target signal invented for a phase
  where the real system has none.

## Third-pass addition: scanning-phase candidate preview (post-review)

Reviewer feedback on the second pass: the scanning phase itself showed
nothing (`material_members`/`centre` were empty/null throughout, and the
co-moving frame fell back to a static center point as a result) — the
reviewer specifically missed v2's behavior of showing *some* candidate
cluster forming and the co-moving frame tracking it during the
pre-qualification window, without wanting v1 (`LineageTracker611`) itself
back.

The fix reuses the SAME machinery that decides which cluster eventually
gets qualified as the material target — it is not v1 and not a
reimplementation. Both
`stage6_12C_kinematic_contact_confirmation/code/world_sampling_612c.py`'s
`try_world` and `final_translating_flock_closure/code/
world_sampling_closure.py`'s copy of that loop call
`common_612.detect_propose` (== `detect_69.propose`, re-exported unmodified
through `common_612c.py`/`common_closure.py` — verified by reading the
import chain, not assumed) at every pre-qualification step, and feed the
result into a `common_612.ForwardMaterialTrace611` instance (==
`forward_material_trace_611.ForwardMaterialTrace611`, same class used as
the tab's PRIMARY identity layer post-qualification) that starts on the
first proposed candidate and dwells/re-evaluates every step after.

`prep_tab6_translation_v3.py`'s `scanning_frames` now replays this exact
loop (same rolling `z_window` capped at `AFFINITY_WINDOW`, same
`len(z_window) >= 2` gate, same start/step call sequence) alongside the
already bit-exact-verified `mf.step` replay, and records two new
per-scanning-frame fields:

- `candidate_preview`: EVERY cluster `detect_propose` proposes that step
  (list of member-id lists) — chosen over showing only the eventual winner
  because that is the more honest answer to "what is being evaluated";
  typically 9-19 clusters per step across the 5 exemplars' scanning
  windows, sizes from ~12 to ~74 birds.
- `candidate_frontrunner`: the tracker's currently-ACCEPTED (dwelling)
  cluster — whichever candidate is presently on track toward eventual
  qualification. Empty only before the tracker first acquires any
  candidate (did not occur in practice for any of the 5 exemplars' 15-frame
  scanning windows; all had a front-runner from t=0 of the shown window).

`centre` for scanning frames is now the bulk centroid of the front-runner
when one exists, else of the single largest proposed candidate, else
`None` — giving the co-moving frame a live, sensible thing to recenter on
during scanning instead of a static point, mirroring v2's
`interior`-tracks-centre behavior without reintroducing v1.

Rendering (`tab6.js`): front-runner birds get a solid teal fill/ring
(`--candidate-frontrunner`, reusing the existing `--predictive` token,
since "predictive/candidate boundary" is exactly what this is); other
proposed-but-not-front-running candidate birds get a faint dashed teal
treatment (`--candidate-other`). Both are a different hue from `--core`
(blue, confirmed `material_members`) and `--actuator` (red), so
"provisional/under evaluation" is never visually conflated with
"confirmed target" — this distinction is called out explicitly in the
Forward-material-trace panel's scanning-phase copy and in the tab legend.
