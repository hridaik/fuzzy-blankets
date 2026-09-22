# Identity validation hardening (Task A)

Frozen rule under test throughout: `B_max_jaccard(min_jaccard=0.30)`. **Not
retuned anywhere in this document.** The purpose of everything below is to
test that frozen value harder than Step 2's own calibration did, not to
select a better one.

## 1. Why Step 2's FPR=0% understated the real risk

Step 2's calibration (`material_identity_step2_20260921/identity_rule_spec.md`)
paired candidates from **different episodes** as its negative class — an
easy adversarial case, since two different random initial conditions are
unlikely to produce coincidentally-overlapping bird-ID sets at all (indeed,
139,655–152,924 of ~143k–157k same-*episode* pairs checked below have
*zero* overlap purely from ID-labelling — cross-episode pairs would have
been even more trivially separable). The real risk the task asked about is
a distractor **co-present in the same episode, same transition**: another
flock, a spatially nearby group, a fragment of the same physical cluster
proposed as a separate candidate by the detector.

## 2. Data splits

| split | source | episodes (seeds) | role |
|---|---|---|---|
| dev / already-used-for-calibration | `observational_corpus_611__val.npz` | 236–247 (12) | the exact corpus that selected Jaccard≥0.30; re-analyzed here with a harder negative construction only |
| untouched validation | `observational_corpus_611__test.npz` | 248–259 (12) | **genuine natural holdout** — already existed on disk (generated when the unrelated predictive-model corpus was built) but never read by any Step-1/Step-2 identity script before this pass; disjoint by episode from dev and from control seeds 500–504 |

Both splits are the real, unmodified `detect_69.propose` detector run over
the real, unmodified primary-regime simulator trajectories — no new
simulation was needed; the untouched-validation file was simply unused
until now.

## 3. Same-frame hard-negative results (spec §5.1)

For every candidate `c` (≥5 members) at every `(episode, t)`, its own
best-Jaccard match at `t+1` is the "presumed continuation"; **every other**
candidate at `t+1` in the same episode is a hard negative against `c`.
Categorized transparently, not asserted as ground truth:

| category | dev (n=143,164) | untouched validation (n=156,978) |
|---|---|---|
| zero_overlap ("obvious unrelated") | 139,655 (97.55%) | 152,924 (97.42%) |
| nonzero_below_threshold ("material-related, correctly rejected") | 3,381 (2.36%) | 3,886 (2.48%) |
| **AT_OR_ABOVE_THRESHOLD** (rule would wrongly accept, if offered alone) | **128 (0.089%)** | **168 (0.107%)** |

**This is not zero.** Step 2's cross-episode-only FPR=0.0% does not survive
contact with same-world hard negatives — a small but real, non-zero
false-accept rate (~0.09–0.11%) exists, consistent across both the
already-seen dev split and the genuinely untouched validation split (same
order of magnitude, same direction — the rule was not overfit to the dev
split in a way validation would expose).

### 3a. Stratified by target size

| size bucket | dev fraction at/above threshold | validation fraction at/above threshold |
|---|---|---|
| small (<20) | 0.0042% (1/24,096) | 0.0% (0/29,693) |
| medium (20–49) | 0.139% (102/73,296) | 0.152% (134/88,017) |
| large (≥50) | 0.055% (25/45,772) | 0.087% (34/39,268) |

Risk concentrates in medium-sized targets, not large or small ones —
medium targets have enough members to accumulate a substantial-looking
overlap by chance/structure, but not so many that a partial-overlap
fragment is diluted below threshold.

### 3b. Stratified by spatial proximity (corrected methodology, see below)

Both centroids compared at the **same instant** (`t+1`): the true
continuation's centroid vs. the distractor candidate's centroid, both at
`t+1` (torus-aware circular mean, `torus_delta`-consistent). "Nearby" =
within 2.5× the episode's local nearest-neighbour spacing
(`geometry_611.local_scale`, the same observer-side density scale used
elsewhere in this stage — never the true interaction radius).

| proximity | dev fraction at/above threshold | validation fraction at/above threshold |
|---|---|---|
| spatially_nearby | 2.70% (2/74) | 0.0% (0/164) |
| spatially_far | 0.088% (126/143,090) | 0.107% (168/156,814) |

**Caveat, disclosed not smoothed over**: an earlier draft of this analysis
measured "nearby" using the t-frame target's own position one step
*earlier*, which conflated ordinary one-step flock translation with
genuine spatial adjacency and produced a spuriously higher nearby-risk
estimate. The number above is the corrected, same-instant comparison. Even
so, only 74/164 same-episode candidate pairs across ~143k–157k total
qualify as "spatially nearby" at all under this (deliberately tight,
nearest-neighbour-scale) threshold — most flagged hard negatives are
spatially far from the true continuation despite sharing material, which
is explained in §3c.

### 3c. Most at-or-above-threshold hard negatives are nested sub-fragments, not independent flocks

Of the 128 (dev) / 168 (validation) at-or-above-threshold hits, 69.5%
(dev) / 64.3% (validation) have `R_new≈1.0` — i.e. the "distractor" is a
**strict subset** of the presumed continuation itself (the detector
proposes both a full cluster and one of its own sub-cliques as separate
candidates at the same step, a known property of clustering-based
proposal generators, not evidence of an independent physical flock). This
is a materially less dangerous failure mode than a genuinely unrelated
flock scoring above threshold: accepting a nested sub-fragment as
"continuation" would under-count the target's membership, not switch
identity to a different organizational entity. The remaining ~30–36% of
hits are genuine partial-overlap, non-subset cases — these are the ones
that matter for the identity question, and they are rare (39/143,164 ≈
0.027% dev; 60/156,978 ≈ 0.038% validation) but not absent.

**Bottom line**: the frozen rule is not perfectly zero-risk against
same-world hard negatives, but the realistic risk (genuine non-subset
false-accepts) is on the order of 0.03–0.04% of same-frame candidate
pairs, an order of magnitude below even the already-small raw
at-or-above-threshold rate, consistent between an already-seen split and a
genuinely untouched one.

## 4. Episode-level sequential trace audit (spec §5.3)

3 seed targets per episode (largest 3 candidates at `t=5`, skipping early
detector warm-up), forward-traced to episode end (`t=180`, i.e. up to 176
steps).

| metric | dev (36 traces) | untouched validation (36 traces) |
|---|---|---|
| final status: continuing | 32 (88.9%) | 29 (80.6%) |
| final status: dead | 4 (11.1%) | 7 (19.4%) |
| mean duration reached (of 176 possible) | 161.0 | 157.3 |
| mean cumulative turnover (1 − Jaccard(start, end)) | 0.678 | 0.758 |
| total split flags | 20 | 20 |
| total merge flags | 6 | 6 |
| total unresolved steps | 18 | 38 |
| total recovered gaps | 4 | 10 |
| max single gap length | 3 (= horizon) | 3 (= horizon) |
| traces with an ambiguous-accept margin event | 11/36 | 13/36 |
| smallest observed accept margin | 0.036 | 0.034 |

No independent ground-truth lineage exists for these uncontrolled
episodes, so "erroneous transfer" is not scored against an oracle (per
spec §5.1's explicit instruction not to invent one). What IS reported: the
rule's own structural guarantee (a step can only be accepted if it clears
the gate against the immediately-preceding target, so it cannot silently
switch onto a below-threshold candidate) holds by construction in every
one of the 72 traces; the risk signal instead is the **accept margin** —
in 11–13 of 72 traces, at some step more than one candidate cleared the
gate simultaneously, with margins as small as 0.034–0.036 between the
winner and the runner-up. This is a real ambiguity signal (small margins
mean a slightly different threshold or detector run could have chosen
differently) but is not, by itself, evidence of a wrong choice — the
winner in every such case was still chosen by the material tie-break
(largest absolute retained count), never by heading or outcome.

Traces that die do so exclusively via the missed-detection horizon (a
target's population becomes too fragmented/dispersed for detect_69 to
propose any ≥5-member candidate clearing the gate for >3 consecutive
steps) — none die via an explicit "switch to something else" event, since
that transition is structurally impossible for this rule.

## 5. Hard synthetic tests H–O (spec §5.4)

Re-running Step 2's A–G suite unmodified alongside 8 new tests:

| test | result |
|---|---|
| A–F (Step 2, unmodified) | all PASS |
| G. Merge (Step 2, unmodified) | FAIL, disclosed (pre-existing, known Jaccard-dilution limitation — not patched here either) |
| H. Two flocks passing near, one persistently co-present and larger | PASS — never switches onto the distractor |
| I. Same-size, zero-overlap replacement | PASS — correctly `unresolved`, not `continuing` |
| J. Gradual turnover with a persistent same-size distractor at every step | PASS — behaves identically to the distractor-free case |
| K. Partial merge/dilution (target 100% retained inside a 6× larger candidate) | **EXPECTED-FAIL, disclosed** — same Jaccard-dilution limitation as test G, confirmed not a one-off artifact of G's specific numbers (goes `unresolved`, not `continuing+merge_flag`) |
| L. Two-way split, both daughters persist with independent turnover | PASS — `split_flag` fires once at the split; the followed daughter shows ordinary `continuing` status throughout, undisturbed by the unfollowed daughter's continued presence |
| M. Split then re-merger | PASS — `split_flag` at the split, `merge_flag` on re-fusion (the followed daughter is a small fraction of the recombined candidate) — the diagnostic merge flag behaves as documented |
| N. Temporary detector over-segmentation (one physical group split into 2 fragments for 3 steps, then re-fused) | PASS — `split_flag` fires only at the *first* fragmentation transition (the moment of genuine ambiguity), correctly does not re-fire every step once locked onto one fragment, and the re-fusion step is recognized as `continuing` |
| O. Repeated missed detections at the exact recovery-horizon boundary | PASS, both sub-cases — recovers correctly at exactly horizon+1 steps; dies correctly on a 4th consecutive miss when horizon=3 |

**14/15 pass; the one failure (K) is the same disclosed, structural
limitation already known from test G — not a new defect, and confirmed
stable across a different size ratio (6× vs. 5×).**

## 6. What this changes about confidence in the frozen rule

Nothing here reverses Step 2's choice to freeze Jaccard≥0.30, and nothing
here was used to retune it. What changes is precision about its failure
mode: it is **not** literally zero-false-accept-rate against same-world
hard negatives (Step 2's cross-episode calibration could not see this);
the realistic non-subset false-accept rate is small (~0.03–0.04% of
same-frame candidate pairs) but non-zero, concentrated in medium-sized
targets, and does not depend on spatial proximity in the way one might
naively expect (most hits are spatially far but materially structural —
nested sub-fragments — rather than nearby-but-independent flocks). The
known merge-dilution blind spot (test G, reconfirmed by test K) remains
the rule's most significant disclosed limitation, and fails safe
(`unresolved`, not false continuation).
