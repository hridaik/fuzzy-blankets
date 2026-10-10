# V1_RECORD_AUDIT.md — cleaning and closing the V1 record

This document audits every specific claim named in the task brief against the
raw saved data and scripts in `../data/protocol_v1/`, `../data/baseline_v1/`,
and `../RESULTS_V1.md` / `../PROTOCOL_V1.md`. **No `protocol_v1` file or data
artifact is modified or deleted.** Corrections are recorded here, additively.

## A1. Documentation inconsistencies

### A1.1 "25 vs 28 passing tests"

Checked directly: `pytest tests/ -q` (run fresh in this session) reports
**28 passed**, matching `RESULTS_V1.md` section 4 ("28 passing tests... 28
tests, `pytest tests/ -q`") but contradicting the same file's section 1,
which says "(25 passing unit/validation tests...)". `PORT_VALIDATION.md`
section 2 also says "All 25 tests pass" but lists checks 1-18 with only 4
test files (`test_lattice.py`, `test_model.py`, `test_spectral.py`,
`test_active_inference.py`) — **`tests/test_rotation.py` (added later, for
the heading-encoding-bug fix documented in `PROTOCOL_V1.md` section 1a) is
not mentioned in `PORT_VALIDATION.md`'s file list at all.**

**Resolution**: 28 is correct and current. 25 was the count *before*
`test_rotation.py` was added (the encoding-bug fix happened after the initial
25-test validation pass, and 3 rotation tests were added alongside it:
`25 + 3 = 28`, consistent with the file list). `RESULTS_V1.md` section 1's
"25 passing" is stale — it was not updated after `test_rotation.py` was
added, even though section 4 of the same file was. This is a copy-paste
staleness bug, not a factual dispute. **Corrected count: 28**, everywhere in
this audit and in `MECHANISM_AUDIT_RESULTS.md`. `RESULTS_V1.md` itself is left
untouched (frozen record); this is the additive correction.

### A1.2 "Monotonically shrinking increments"

`RESULTS_V1.md` section 3.3 explicitly gives the increments from the greedy
`k=2..6` escalation: **+0.046, +0.059, +0.020, +0.008** (`k=2→3, 3→4, 4→5,
5→6`). `+0.059 > +0.046`, so the sequence is **not monotonically
decreasing** — it goes up, then down, down, down. The surrounding sentence
in section 3.3 ("shrinks monotonically") is numerically contradicted by the
very numbers it cites two sentences earlier. This is exactly the
inconsistency flagged in the task brief.

**Corrected statement**: *The increment per additional actuator is not
monotonic — it rises from `k=2→3` (+0.046) to `k=3→4` (+0.059), then falls
for the remaining two steps (+0.020, +0.008). Only the last two steps show
clear diminishing returns; the first two steps do not. The qualitative
conclusion (saturating well below the 0.8 threshold, `P(success)=0`
throughout) is unaffected by this correction — only the word
"monotonically" was wrong.* This is corrected here rather than editing
`RESULTS_V1.md` in place.

### A1.3 "Saturation" from the greedy top-10 trajectory

`RESULTS_V1.md` section 3.4 says the response "saturat[es] well below the 0.8
threshold." Taken alone this could be read as a claim about the *global*
actuator-response landscape. It is not: the greedy search in section 3.3 was
restricted to a 10-bird shortlist chosen by single-actuator response ranking,
which (per this audit's Part B/C, see `MECHANISM_AUDIT_RESULTS.md`) turned
out to be a poor proxy for the bird set that actually matters mechanistically
(the 12-bird dynamical shell `B^D_0`). **This audit's Part D shows that
forcing the *complete, correctly-identified* interface (`B^D_0`, 12 birds —
overlapping the greedy shortlist in only 4 of 6 members) reaches
`P(success)=0.96`, not a saturating ~0.28.** The "saturation" in
`RESULTS_V1.md` section 3.3-3.4 was real *for the specific 10-bird candidate
pool searched*, not a property of the actuator-response landscape in
general. `RESULTS_V1.md`'s own hedge in section 3 ("not a global
impossibility proof") already anticipated this, but section 3.4's prose
("cannot retarget... within the search performed") should be read
strictly as scoped to that search, not generalized. No V1 text is edited;
this is the clarification.

### A1.4 Distinguishing exhaustive k=1 / restricted k=2 / greedy k=3-6

`RESULTS_V1.md` section 3.3 already labels these correctly in its subsection
headers and prose ("exhaustive over all 45 pairs within the top-10... greedy,
same shortlist"). The one place this distinction blurs is section 3.4's use
of "sparse control... cannot retarget," which does not re-state the
non-exhaustiveness inline. Re-stated here for clarity, without editing V1:

- `k=1`: **exhaustive** over all 80 non-interior birds (`P(success)=0` for
  all 80 — a complete result, not a search artifact).
- `k=2`: **exhaustive only within a top-10-by-response shortlist** (45 of the
  `C(80,2)=3160` possible pairs). **This audit's Part E ran the full 3160-pair
  sweep** (`data/pair_synergy.json`); see `MECHANISM_AUDIT_RESULTS.md` Part E
  — the negative `k=2` finding is confirmed and generalizes (best pair over
  all 3160: `R_ij=0.160`, still zero pairs meeting `P(success)>=0.5`), closing
  the gap `RESULTS_V1.md` itself flagged ("not exhaustive beyond k=2").
- `k=3..6`: **greedy, same 10-bird shortlist** — never described as a minimum
  in `RESULTS_V1.md` (already correctly hedged as "smallest found under the
  stated procedure... never as a global minimum" in `PROTOCOL_V1.md` section
  7). No correction needed here; V1's own hedging was already accurate on this
  specific point.

No instance of "minimum" being misapplied to a non-exhaustive multi-actuator
result was found in `RESULTS_V1.md` or `PROTOCOL_V1.md` — both files already
use "smallest found under the stated procedure" language. **This specific
correctness bar (A1, bullet: "Do not use 'minimum'...") is therefore
already met**; flagged as verified-clean rather than corrected.

## A2. Heading-protocol provenance

Verified directly from `PROTOCOL_V1.md` section 1a and `PORT_VALIDATION.md`
section 3a, cross-checked against the actual data files:

1. **Baseline spontaneous target-attainment was recomputed after the fix**:
   `data/baseline_v1/baseline_rows.json` (161 qualifying rows) uses
   `rotate_cw(h0)` throughout (confirmed by inspecting
   `python/analysis/baseline_characterization.py` line 90:
   `h_star = rotate_cw(h0)`); the pre-fix run is preserved separately at
   `data/baseline_v1_buggy_naive_hstar_DO_NOT_USE/baseline_rows.json` and was
   never used for any threshold. **Confirmed.**
2. **`T_u=20` remained selected using the corrected target**: `PROTOCOL_V1.md`
   section 4 explicitly states the pre/post-fix `T_u=20` value was
   numerically unchanged at reported precision (`0.066` both times) and shows
   the full post-fix table. **Confirmed** — re-derived independently in this
   audit is unnecessary since the frozen table already documents both values.
3. **All Phase 4-onward data were regenerated post-fix**: `data/protocol_v1/`
   contains only post-fix `canonical_snapshot.npz` /
   `canonical_snapshot_meta.json` (t0=41, h0=2, h_star=0/up — the geometric
   `rotate_cw` value, not the naive `(h0+1)%4=3` value); the pre-fix canonical
   snapshot is preserved separately at
   `data/protocol_v1_pre_rotation_fix/canonical_snapshot.npz`. `phase4_5_response_map.json`,
   `phase5_k2_search.json`, `phase5_greedy_k.json`, `phase6_replication_partial.json`
   all load `h_star` from the post-fix `canonical_snapshot_meta.json`/response-map
   file — none reference the pre-fix directory. **Confirmed: no Phase 4+ artifact
   was generated under the buggy target.**

**Naming transparency**: per the task brief's instruction, this audit names
the corrected protocol explicitly as **`PROTOCOL_V1a`** — the frozen document
`PROTOCOL_V1.md` already *is* PROTOCOL_V1a in substance (it documents the
correction inline, in section 1a, applied before any actuator search), but it
was never given a distinct version label. This audit adopts **`PROTOCOL_V1a`**
as the correct name for the protocol actually used to produce every result in
`RESULTS_V1.md`, to make explicit that a real, substantive definitional change
(not a cosmetic one) occurred between the initial freeze
(hash `cd5cf384...`) and the version actually executed
(hash `8b2882f21f9f1079afbef440c76ce5fd9319e9a0d58f53c5e968e3771e698f10`).
This mechanism audit and V2 are therefore built on **PROTOCOL_V1a**, not on
the never-executed original `PROTOCOL_V1` freeze.

## A3. Canonical-flock representativeness (quantified)

Recomputed from `data/baseline_v1/baseline_rows.json`'s 161 qualifying seeds,
re-running each seed's simulation to its own `t0` (deterministic, bit-identical
reproduction) to obtain `lambda2` and boundary size `|B_0^F|`, which the
frozen baseline file did not record
(`code/baseline_spectral_recompute.py` -> `data/canonical_representativeness.json`):

| Quantity | Canonical (seed 2) | Population median (n=161) | Canonical percentile rank |
|---|---|---|---|
| `t0` | 41 | 8.0 | **94.4th** (very late) |
| `\|I0\|` | 20 | 20.0 | 100.0th (tied at the population max — structural, see PROTOCOL_V1.md section 2's "near-tautological size" caveat, not a distinguishing feature) |
| `\|B_0^F\|` (boundary size) | 2 | 3.0 | **49.7th — i.e. approximately MEDIAN, not unusual** |
| `C_{I0}` (coherence) | 1.0 | 1.0 | 100.0th (tied at max — most qualifying flocks have coherence 1.0, not distinguishing) |
| `lambda_2` | 12.47 | 20.56 | 24.2nd (below-median connectivity) |
| `lambda_3 - lambda_2` (eigengap) | 1.39 | 9.73 | **1.2nd — essentially the smallest eigengap in the entire qualifying population** |

**This corrects `RESULTS_V1.md` section 5's vague claim** ("unusually small
spectral boundary (2 nodes)... small-sample caveat"): **the boundary size of 2
is NOT atypical** — it sits almost exactly at the population median (49.7th
percentile). What *is* genuinely atypical about the canonical flock is (a) its
very late `t0` (94th percentile — it took far longer than most qualifying
flocks to stabilize) and (b) its **razor-thin eigengap** (1.2nd percentile —
among the 161 qualifying flocks, essentially the least-stable spectral
identification that still cleared the frozen `eigengap_min=1.0` bar). The
"small n=2 boundary, therefore underpowered" framing in `RESULTS_V1.md`
section 5 picked the wrong reason: the real caveat is that **the canonical
flock's spectral decomposition is a borderline case of the selection rule
itself** (it barely qualifies at all), not that its boundary happens to have
few members (many typical flocks also have small boundaries — median 3).
This distinction matters directly for interpreting Part C/D of the mechanism
audit: a low eigengap generally correlates with a less numerically stable
Fiedler vector, which is exactly the caveat `METHODS_AUDIT.md` section 10 and
`PROTOCOL_V1.md` section 1 already warn about for degenerate cases — the
canonical flock is close to (though not at) that regime, which should
temper how strongly the specific *size* of `B^F_0` observed here (n=2) is
generalized. See `MECHANISM_AUDIT_RESULTS.md` Part C for the multi-flock
ensemble check that follows up on this directly.

## A4. Port-verification closure attempt

- **GNU Octave installability, checked this session**: `apt-cache policy
  octave` shows a candidate package (`8.4.0-1build5`) is available, but
  `sudo -n apt-get install -y octave` failed — **"sudo: a password is
  required"** — no non-interactive privilege-escalation path exists in this
  sandbox. MATLAB was not checked further (no license/environment available;
  same conclusion as `PORT_VALIDATION.md` section 0). **The Octave/MATLAB gap
  persists**, confirmed freshly rather than assumed carried-over.
- **Deterministic cross-language fixture produced**
  (`code/cross_language_fixture.py` ->
  `data/cross_language_fixture.json`, `code/octave_fixture/run_fixture.m`):
  - **Part 1** (single-bird decision step): bird 44 (1-based MATLAB index 45)
    on the standard `nn=100` lattice, with a fully specified own-heading and
    all 8 neighbor headings, default `ModelParams`. Gives the exact expected
    `G` row, policy-posterior row, and — using two explicit, named uniform
    draws (`u1=0.37`, `u2=0.81`) substituted into the same
    `find(rand<cumsum(P),1)` rule the upstream code uses — the exact expected
    sampled action (`1`, "down") and next heading (`1`, "down"). A
    collaborator with MATLAB/SPM12 access can hand-drive
    `active_inference_bird_control.m` with these substituted draws and diff
    the outputs directly.
  - **Part 2** (Fiedler pipeline): a small hand-specified `nn=9` (3x3 lattice),
    `TW=3` heading-history tensor, with exact expected adjacency, Laplacian,
    first three eigenvalues (`lambda1=~0, lambda2=0.330, lambda3=4.058`), and
    core/boundary partition. An Octave harness
    (`code/octave_fixture/run_fixture.m`) is included that calls the verbatim
    upstream `getMarkovBlanketOfFlock.m` directly and diffs its adjacency
    output against the fixture — this part does **not** require SPM12 (only
    Part 1 does), so it is the more immediately runnable half of the fixture
    for a collaborator without a full active-inference toolbox install.
  - **Remaining uncertainty, stated plainly**: neither part has actually been
    executed against the released MATLAB code in this or any prior session.
    All "expected" values are Python-port outputs, cross-checked only against
    the port's own 28 deterministic/algebraic unit tests (which test
    structural properties like column-stochasticity, not literal agreement
    with a MATLAB run). This is a real, still-open validation gap — it does
    not block the mechanism audit or V2 (per the task brief), but it means
    the numeric fixture values above should be understood as "what the
    audited Python port computes," not yet as "independently confirmed
    against the original MATLAB implementation."

## Summary of this file's status

Every specific claim named in the task brief's Part A was checked against
raw data/scripts, not asserted from memory. Three real documentation bugs
were found and corrected (A1.1 stale test count, A1.2 "monotonic" claim,
A1.3 overgeneralized "saturation" language) and one real quantitative gap was
closed (A3, boundary-size representativeness). No `protocol_v1` file or
`data/protocol_v1*` artifact was modified, deleted, or rerun with different
parameters. `PROTOCOL_V1.md`'s frozen thresholds are used unchanged
throughout the rest of this mechanism audit and V2.
