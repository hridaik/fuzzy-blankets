# IDENTITY_MODEL — a principled multi-object identity instrument for the translating collective

Analytical specification, written before any new tracker code. Everything
in `CLAIMS_LEDGER.md` is treated as established background, not
re-derived. `lineage_611.LineageTracker611` (v1, production) and
`audit/lineage_v2_611.py` (v2, comparator, never validated on the real
flock per the mandate) are both frozen inputs to be superseded by a new,
independently-specified model — not patched.

## 0. What problem this document is actually solving

The physical system (`moving_flock_611.MovingFlock611`) is a population of
`N=400` point agents on a torus, each with a position `r_i(t) \in [0,L)^2`
and a categorical heading `z_i(t) \in \{0,1,2,3\}` (the `UV4` lattice),
updated by an active-inference policy that only sees FOV-restricted,
radius-`R` neighbours. Nothing about "the collective" is a labeled
variable anywhere in that simulator — organizational identity is entirely
an inference the observer imposes on a raw agent-level trajectory. The
task is to build the inference that does this well: detect a
self-organizing pattern, track its organizational identity while its
membership and interfaces change, quantify the resulting uncertainty
honestly, and expose enough of that uncertainty that a future controller
cannot be fooled by it. Section C of `CLAIMS_LEDGER.md` is the concrete
evidence that the existing instrument (v1) fails this in a specific,
now-understood way (argmax-instability over a branch tree, not the
mechanism originally guessed) and that the existing repair (v2) is
*evidence about the failure*, not a validated replacement.

## 1. Literature grounding — what is reused, what is proposed

Read directly (abstracts/introductions fetched and reviewed in this
session, not assumed from memory of the field) or established general
background as noted:

1. **García-Fernández, Svensson, Morelande, "Multiple Target Tracking
   Based on Sets of Trajectories"** (IEEE TAES 2020; arXiv:1605.08163).
   Core move this document reuses: **the random object is a trajectory
   (or, for genealogy, a tree of trajectories), not a per-time-step
   state.** A full Bayesian treatment characterizes the posterior over
   the *whole history* given all data up to now, not just over the
   current-time marginal — "characterise the distribution of the
   trajectories given the measurements," with births/deaths handled by
   RFS cardinality and a conjugate family of multitrajectory densities
   for tractable recursion. **What this fixes in the inherited code:**
   `LineageTracker611.Hypothesis.records` already stores a growing history
   per branch, but `dominant_interior()` reads out only the *current*
   MAP branch's *current* member set — genealogy and present state are
   conflated by construction (one `hid` per branch). §4 below adopts the
   sets-of-trajectories discipline explicitly: identity is a trajectory
   (or tree) random variable; the "current interior" is a *marginal
   readout* of that trajectory posterior, never the primitive itself.

2. **Beard, B.-T. Vo, B.-N. Vo, "Bayesian Multi-Target Tracking With
   Merged Measurements Using Labelled Random Finite Sets"** (IEEE TSP
   2015, DOI 10.1109/TSP.2015.2393843). Core move reused: **a single
   observed cluster can be the merged measurement of more than one
   still-distinct target**, modeled explicitly (a merged-measurement
   likelihood over subsets of the label set) rather than by forcing a
   single detection-to-track association. **What this fixes:** this is
   exactly the "detector merger vs. real merger" distinction the mandate
   requires (§6 below) — `detect_69.propose`'s Louvain communities are
   candidate *measurements*, and a single returned community must be
   allowed to be the merged observation of two objects that have not
   actually merged, symmetrically with one true object being detected as
   two components.

3. **García-Fernández, Svensson, "Tracking Multiple Spawning Targets
   Using Poisson Multi-Bernoulli Mixtures on Sets of Tree Trajectories"**
   (IEEE TSP 2022; arXiv:2111.05620). Core move reused: **genealogy is
   represented as a tree attached to one trajectory random variable**
   (a "tree trajectory" holds "all trajectory information of a target and
   its descendants... each branch has trajectory information of a target
   or one of its descendants and its genealogy"), approximated by
   KL-minimizing multi-Bernoulli branches for tractability. **What this
   fixes:** `LineageTracker611`'s `hid`-per-branch scheme already
   *resembles* a tree, but treats every branch as a **competing
   hypothesis for present identity** (they sum to 1 and argmax picks one),
   not as **genealogy of one accepted object** — the tree-trajectory
   framing this document adopts (§7) keeps genealogy as metadata attached
   to *accepted* split/merge events, never as silently-competing mass for
   "what is the interior right now."

4. **Yang, Liu, et al., "Augmented LRFS-based Filter: Holistic Tracking of
   Group Objects"** (arXiv:2403.13562; Signal Processing). Core move
   reused: **each element of the random finite set carries kinetic state
   AND group-membership information jointly**, propagated by a labeled
   multi-Bernoulli filter — group identity is a first-class label
   alongside kinematic state, not a downstream clustering of point
   estimates. **What this fixes:** the existing pipeline computes
   candidate detection (Louvain on positions+heading-agreement) and
   identity tracking (`LineageTracker611`) as two separate stages with no
   shared uncertainty representation; this document's state definition
   (§3) is deliberately closer to this augmented-LRFS idea — one object
   state carries existence, kinematics, extent, AND membership together,
   consumed jointly rather than pipelined.

5. **García-Fernández, Ristic, Svensson, Sun (or the paper's actual
   author list), "A Time-Weighted Metric for Sets of Trajectories to
   Assess Multi-Object Tracking Algorithms"** (arXiv:2110.13444). Core
   move reused: **evaluation of a trajectory-set estimate against ground
   truth is itself an assignment problem** with a base per-time
   localization/existence cost plus track-switch penalties, computable
   either by exact multi-dimensional assignment or a polynomial LP
   relaxation, with a *time-weighting* on top so different applications
   can weight recent vs. distant errors differently. **What this uses,
   later, not now:** Phase 2's validation protocol (a separate document,
   `VALIDATION_PROTOCOL.md`) will use this metric family — decomposed
   into localization error, false/missed tracks, and identity
   switches — as its primary scoring rule, rather than inventing an ad
   hoc "jump count."

**What is explicitly NOT done:** no full PMBM/GLMB/tree-trajectory
software package is implemented. The five papers above justify *why* the
state, likelihood, and event structure below are shaped the way they are
(trajectory-as-primitive, merged measurements as first-class,
tree-structured genealogy, joint kinematic+membership state, assignment-
based evaluation) — they are cited as the reason a design choice is
principled, not as a library to import. Everything below is a
self-specified model in this codebase's own notation, explicitly derived
from and cross-checked against that literature, not an unexplained
transplant of a point-object filter onto group data.

## 2. Four layers (item 1A)

```
Physical observations  Y_t = { (i, r_i(t), h_i(t)) : i = 1..N }, plus a record of issued interventions u_{0:t-1}.
        │  (Louvain + a position/heading field-based alternative, §5)
        ▼
Candidate descriptions  C_t = { c^(1)_t, ..., c^(K_t)_t },  c^(k)_t \subseteq {1..N}, at a DECLARED observation scale.
        │  (this document's joint recursion, §4)
        ▼
Identity                Z_t = { (\ell, existence_\ell, state_\ell, genealogy_\ell) }, persistent labels \ell.
        │  (a controller binds to ONE \ell, never to "whichever candidate has the most mass")
        ▼
Control                 task(\ell*) for one selected, already-observed label \ell*.
```

A candidate `c^(k)_t` is a **measurement**, in the same sense a merged
blob is a measurement in Beard/Vo/Vo — it is neither a true object nor an
independent piece of evidence. Two candidates derived from overlapping
member sets of the same underlying birds (e.g. a size-38 and a size-33
Louvain community that share 30 members) are correlated measurements of
the same underlying configuration, not two independent observations —
this is precisely the defect `LINEAGE_FORENSICS_6_11.md` §2 documents as
"duplicate hypotheses inflate reported certainty," traced one layer
upstream: the duplication enters at the *candidate* layer (Louvain
returning near-identical communities across adjacent steps, or a
detector's own re-run instability, `INVARIANCE_AND_TRANSFER_6_11.md` §1.2)
and is compounded, not created, by the identity layer failing to
coalesce present-states before normalizing (already diagnosed and
partially repaired by v2, `LINEAGE_V2_METHOD_AND_VALIDATION.md` §1).

## 3. The random object and its state (item 1B)

Given `Y_{0:t}`, maintain a **joint** distribution over the set of
currently-existing labeled objects and their states and genealogy —
`p_t(Z_t, G_t)` — not a simplex over "which one candidate is the
population" (the inherited v1 defect: `Hypothesis.prob` sums to 1 *within
one lineage tree*, and `dominant_interior()` treats the whole system as if
there could only ever be one live thing worth reporting). Distinct,
simultaneously-real objects are different labels in the SAME joint state,
each with its own existence probability — mass in one object's existence
is not mass "taken from" another's.

For label `\ell`, the state carries:

- `e_\ell \in \{0,1\}` — existence.
- `c_\ell \in [0,L)^2` — center (torus-valued).
- `v_\ell \in \mathbb{R}^2` — bulk velocity (torus-tangent; see §7's
  transition model).
- `S_\ell` — spatial extent/shape: a continuous covariance-like `2x2`
  matrix `\Sigma_\ell` (the actual latent state component, evolving under
  its own process noise, §8), never asserted as "the true shape," only as
  an observed-scale-dependent description. **Not part of `S_\ell`'s own
  stochastic state:** component count / anisotropy / compactness
  diagnostics (§10's contract — corrected from an earlier, wrong "§9"
  cross-reference) are DERIVED fresh each step from `\ell`'s current
  member set at the declared morphology scale; they are observation-side
  diagnostics of `\ell`'s current extent, never a second, separately
  noise-propagated state variable. (A continuous covariance and a
  discrete component count cannot coherently share one stochastic update
  process — an earlier draft implied they could by bundling both into one
  noisy "spatial extent/shape" quantity; corrected here by keeping only
  `\Sigma_\ell` as latent state and always recomputing component count
  from it rather than perturbing it directly.)
- `m_\ell \in \mathbb{R}_{\ge 0}` — mass (member count, or a soft
  membership-weighted count under §6's overlap semantics).
- `\pi_\ell` — a heading distribution over the 4-state `UV4` lattice (the
  "co-moving phenotype" the collective's own members currently share).
- `w_i^\ell \in [0,1]` — **unconditional** membership probability for
  agent `i`: `P(i \in \ell \text{ and } \ell \text{ exists} \mid
  Y_{0:t})`. Unconditional, per item 1H's decision-theory requirement —
  never `P(i \in \ell \mid \ell \text{ exists})`, which would silently
  discard the "maybe it's dead" branch of uncertainty before membership is
  even asked about.

Exposed for every label, every step (this is the API contract §9's
metrics build on):

1. `e_\ell` (existence probability).
2. a distribution over position/shape/membership alternatives for THAT
   object (i.e. **the live-hypothesis fan-out is per-label**, not a
   single tree-wide simplex — this is the direct fix to v1's structural
   error of normalizing all branches of one tree against each other as if
   they were mutually exclusive explanations of "the one interior").
3. `w_i^\ell` for every agent `i` (not just current members — a
   just-departed agent keeps nonzero `w_i^\ell` for some decay window,
   §7).
4. `P(\text{missed/unresolved observation})` vs. `P(\text{terminated})` —
   kept as **two different quantities**, per item 1B's explicit
   instruction. A step where `c_\ell`'s expected candidate is simply not
   returned by the detector (occlusion-analogue: a temporary Louvain
   miss) must inflate `\sigma_{c_\ell}`/`\sigma_{S_\ell}` and hold
   `e_\ell` roughly steady, not collapse `e_\ell \to 0`.
5. Lineage/event probabilities and provenance (§7).

## 4. The observation model (item 1C)

**Baseline, stated and justified, not silently assumed calibrated.** A
marked spatial mixture, conditional on the observed population size `N`:

```
f(r, h | Z_t) = pi_0 f_0(r,h) + sum_\ell pi_\ell f_\ell(r,h; theta_\ell),      sum_\ell pi_\ell + pi_0 = 1, pi >= 0.
```

`f_0` is a diffuse "unassigned population" background component (birds
not currently claimed by any tracked object — necessary because, per
`THINGNESS_GATE_AUDIT.md` and `LINEAGE_FORENSICS_6_11.md`, the tracked
interior is routinely a *minority* of N and the rest of the population is
not garbage, it is unmodeled-as-a-distinct-object background). For the
primary, single-scale clump scope (§6 fixes the scope explicitly): each
`f_\ell(r,h;\theta_\ell)` is a **wrapped elliptical spatial density**
(torus-wrapped bivariate normal, parameterized by `c_\ell`, a
2x2 shape/orientation matrix) **times a categorical heading distribution**
`\pi_\ell` over the 4 `UV4` states, i.e. `f_\ell(r,h) =
\text{WrapNormal}(r; c_\ell, \Sigma_\ell) \cdot \pi_\ell(h)`. This is an
interpretable initial family, not a claim that real starling-like flocks
are elliptical Gaussians — it is the null model against which §9's
morphology diagnostics (anisotropy, component persistence) test for
misspecification.

**Per-bird conditional independence, and what it does and does not
assume.** Given the mixture component assignment, `f` factorizes over
birds: `f(Y_t | Z_t) = \prod_i f_{\ell(i)}(r_i, h_i)`. **This is a
conditional-independence assumption in the observation model, not an
assertion that the physical birds move independently** — the physical
correlation between birds (their headings actually depend on each other
through `MovingFlock611.compute_G`'s live-edge sums) is modeled through
the *shared* component parameters `(c_\ell, \Sigma_\ell, \pi_\ell)`, which
every member of `\ell` shares, exactly the same sense in which a Gaussian
mixture models correlated cluster members through shared cluster
parameters rather than through explicit pairwise coupling. **This is a
real approximation and is expected to be misspecified** in a specific,
checkable way: real correlated flocking dynamics induce more
same-component-heading agreement locally (within a few `R`) than a flat
categorical `\pi_\ell` shared uniformly across the whole spatial extent of
`\ell` would predict, exactly the phenomenon `predictive_boundary_611`'s
relational (bird-pairwise, not component-level) model already captures far
better (train logloss 0.34-0.36 vs. a uniform baseline of 1.386,
`RESULTS_6_11.md` §4) than a component-mean heading ever could. **This
model is therefore explicitly NOT proposed as the predictive model** — it
is the *identity/segmentation* likelihood only, evaluated by whether it
recovers the right existence/membership/event structure (§10's Bpred
role stays separate, per `RESULTS_6_11B.md`'s architecture note, reused
here rather than re-derived: `B^pred`, `B^{D,1}`, `B^{C,\tau}` remain
siblings of the identity layer, not replaced by it).

**Misspecification test, to be run in Phase 2, not asserted here:**
compare (a) the mixture's own held-out heading log-loss for members of
`\ell`, against (b) `predictive_boundary_611`'s relational model's
log-loss for the same members. If (b) beats (a) by a wide,
significant margin (the online-loop numbers above suggest it will), that
quantifies exactly how much correlated structure the identity mixture's
conditional-independence assumption is leaving on the table — reported,
not hidden, and not a reason to abandon the mixture as an identity model
(existence/segmentation and one-step heading prediction are different
objects, exactly `RESULTS_6_11.md` §6's own finding that `B^pred` and
`B_D` have Jaccard 0.034 — barely related).

**Why not a bare heuristic score softmax.** `LineageTracker611`'s own
`score = 0.6*dice + 0.4*R_F` softmax (temperature 4) is exactly the
practice item 1C prohibits: an unnormalized combination of two ad hoc
similarity measures, exponentiated and renormalized, presented
(`METHODS_AUDIT_6_11.md` §1.2) as "the entire probability distribution
over lineage continuation." It is not derived from any stated likelihood
times prior; its "probabilities" are not calibrated (confirmed
uncalibrated by v2's own author, `LINEAGE_V2_METHOD_AND_VALIDATION.md`
§1: v1's scores are explicitly "heuristic weights, never claimed
calibrated"). This document's model produces an actual likelihood
`f(Y_t|Z_t)` from the stated mixture, from which posterior branch weights
in §5's recursion follow as a genuine (if approximately-computed, per §5's
own disclosed pruning) Bayesian update — not a separately-invented
softmax rule bolted onto a separately-invented matching score.

## 5. Joint Bayesian/event recursion (item 1D)

```
p_t(Z_t, G_t) \propto  L(Y_t | Z_t, G_t) \cdot \int T(Z_t, G_t | Z_{t-1}, G_{t-1}, u_{t-1}) \, p_{t-1}(Z_{t-1}, G_{t-1}) \, d(Z_{t-1}, G_{t-1})
```

`G_t` is the **event/genealogy history** — which labels are births,
deaths, splits, merges, continuations, since `t=0` — never the internal
softmax/branch score of any one candidate-matching heuristic. `u_{t-1}`
(an issued intervention, if any) enters ONLY the physical prediction term
`T`; the desired task outcome never enters `L` or `T` — this is the
existing firewall discipline (`tests/test_no_topology_leakage_611.py`)
extended to a new failure mode the AST-based test cannot see (per
`METHODS_AUDIT_6_11.md` §2's own finding that content-leakage, not just
import-leakage, is the real risk): **the identity recursion's likelihood
and transition kernel must never receive `target_heading`, `frac_at_target`,
or any quantity computed from them.** This is checked, not merely
declared, by the same style of runtime seal `test_no_topology_leakage_611.py`
already uses, extended with a check for these specific identifiers.

**Global normalization over competing explanations.** At each step, the
transition-and-likelihood update must be normalized over the full set of
mutually exclusive global explanations for the *change* between
`C_{t-1}`-conditioned identity and the new observations: continuation, one
or more births, one or more deaths, missed detections, detector
over/undersegmentation of one true object, detector merger of two true
objects, and actual splits/mergers (§6-7 define these precisely). **A
local per-hypothesis branch softmax that guarantees every parent survives
whenever at least one candidate clears a retention floor — v1's exact
defect, `METHODS_AUDIT_6_11.md` §3 — is exactly what this normalization
must NOT reduce to.** The fix is not "add a bigger death probability
floor" (a threshold tweak); it is that "no acceptable transition" must be
a first-class member of the same event set that "continue to candidate
`k`" is a member of, competing for the SAME probability mass under the
SAME normalization, so that when every event's likelihood is bad, "none
of the above, hold as unresolved" can legitimately win. §8 (event
semantics) enumerates this event set exhaustively; §11 (honest no-jump
guarantees) states the resulting architectural guarantee precisely.

**Exact enumeration vs. documented approximation.** For a *small* scene
(a handful of candidates, one or two lineages), all compatible
event/association hypotheses are enumerated exactly — this is the
literal reference computation `MATHEMATICAL_CHECKS.md`'s tiny examples
use to validate any larger-scale approximation against. At the real
scale (up to ~13 simultaneous Louvain candidates per step, per the seed
500 t=61 worked example in `METHODS_AUDIT_6_11.md` §4), full enumeration
of all subset-partition event hypotheses is combinatorially infeasible
every step; the approximation adopted is: **(a)** coalesce candidates
into a bounded number of live "object update" possibilities per label
using the same gating logic as `LineageTracker611` (a candidate must
clear a *disclosed, recalibrated-if-necessary* retention/shape/transport
floor before it is even considered a competing hypothesis for that
label's continuation — this bounds the branching factor exactly as v1's
own `RETENTION_MIN` does, but the floor's role changes from "the only
gate to survival" to "the only gate to being enumerated as a candidate
event, with death/unresolved still competing against every enumerated
candidate on equal likelihood footing"), and **(b)** duplicate
present-states are coalesced into ONE entry before normalization (v2's
already-validated fix, `LINEAGE_V2_METHOD_AND_VALIDATION.md` §1,
reused rather than re-derived) so that Louvain's own re-run instability
(`INVARIANCE_AND_TRANSFER_6_11.md` §1.2, ≤2% membership disagreement
under relabeling) cannot manufacture extra probability mass by returning
the same physical candidate under two different `hid`s. **Coalescing is
by TOLERANCE, not exact set identity — corrected from an earlier draft
that only coalesced literally-identical member sets.** Since the cited
detector instability is itself ≤2% (1–2 birds), an exact-identity rule
would fail to coalesce almost every real near-duplicate pair, silently
reintroducing a softened version of the double-counting defect this
mechanism exists to close. The rule: two candidates coalesce if their
Jaccard similarity exceeds a declared threshold (`J >= 0.9`, a Phase-2
calibrated constant, not asserted here — chosen to comfortably clear the
measured ≤2% detector noise band while not merging genuinely distinct
same-scale candidates), and the coalesced entry's member set is their
UNION, carrying a provenance tag recording both source candidates and the
disagreement — never silently picking one source's set and discarding the
other's. Duplicate-invariance (§9(5), `MATHEMATICAL_CHECKS.md` Case 2)
is checked at BOTH exact duplication (`J=1`) and near-duplication
(`J\approx0.9`–`0.99`, synthetically constructed by dropping 1–2 birds from
an otherwise-identical candidate) in Phase 2 — passing only the exact case
is not sufficient evidence this mechanism works at the real detector's
actual noise level. **What must be
reported, per item 1D's instruction not to claim omitted mass is zero:**
at every step, the total probability mass assigned to "enumerated
event, some candidate" vs. "no acceptable candidate, hold as unresolved"
vs. `1 - (\text{sum of the two above})` (the un-enumerated remainder,
i.e. events this approximation did not even construct — e.g. a real
split into 3 pieces when only 2-way splits are checked). This third
bucket must be tracked and shown to be small (not assumed small) at the
scales this program actually runs, exactly analogous to a pruning-error
diagnostic in any beam-search-based filter.

**Marginalization discipline.** Two enumerated events with identical
resulting member sets are marginalized together for *present-state*
reporting (this is what "coalesce duplicates" means, formally: sum their
posterior mass) **only if they are also indistinguishable in ancestry,
velocity, phenotype memory, and one-step-ahead predictive distribution**
— ancestor-distinguishable duplicates (e.g. one path says "continuation of
label A," another says "label A died and label B, coincidentally
identical in current membership, was born this instant") are marginalized
for the *current marginal* `p(\text{members}, t)` but their full
trajectory/genealogy record is kept separately and never discarded, per
item 1D's explicit instruction. This is a stronger requirement than v2's
current "same current member set -> merge" rule
(`LINEAGE_V2_METHOD_AND_VALIDATION.md` §1's identity-unit row) — v2's rule
is adopted as the *present-state marginal* computation, but this document
requires the genealogy record survive underneath it, which v2's
`genealogy: [(parent_lid, contributed_prob), ...]` field already provides
the hook for and this program will use rather than re-invent.

## 6. Overlap semantics (item 1E)

Four cases, kept distinct in every downstream computation:

1. **Overlapping alternative proposals for ONE object** — e.g. Louvain
   returns a size-38 and a size-33 candidate sharing 30 members this
   step, both plausible readings of the same underlying configuration.
   These compete as alternative *hypotheses* for one label's current
   state (§3 item 2's per-label fan-out), never as two separate objects.
2. **Two objects occupying overlapping spatial regions, possibly
   different headings** — two real, distinct labels whose spatial
   extents (`S_\ell`) overlap. Handled by the mixture's own component
   structure: `f_\ell` and `f_{\ell'}` can have overlapping support; a
   bird physically located in the overlap is NOT automatically ambiguous
   — its heading likelihood under each component still discriminates
   membership if the two components' `\pi_\ell` differ (e.g. two crossing
   streams with different bulk headings). If the two components' `\pi`
   ALSO coincide in the overlap region, membership for birds there is
   genuinely ambiguous — reported as soft `w_i^\ell \approx w_i^{\ell'}
   \approx 0.5`, not resolved by an arbitrary tie-break.
3. **True shared functional membership** — a bird that is genuinely,
   simultaneously, functionally part of two organizations (not modeled in
   the primary single-scale mixture, §4's declared scope: each hypothesis
   assigns one latent group per bird). If a future pass adds this, it
   requires a **factorial/multilabel likelihood** (`f(Y_t|Z_t) = \prod_i
   f_{\text{joint membership of }i}(r_i,h_i)`, summing over the power set
   of labels `i` could belong to, or a declared sparse subset thereof) —
   explicitly NOT two independent single-membership filters run
   side-by-side, which would double-count the same bird's evidence for
   both labels' existence and inflate both posteriors. Not built in this
   pass; flagged so a future implementer does not silently violate this.
4. **Parent/child or coarse/fine descriptions at different scales** — the
   exact phenomenon `THINGNESS_GATE_AUDIT.md` diagnosed (`local_scale`
   giving 13-24 fragments of the SAME candidate that the detector's own
   3.3-unit cutoff sees as one component). This is not an identity
   question at all — it is a **declared-scale** question (§9): "is this
   one object" is only well-posed relative to a stated connectivity
   scale, and different scales are allowed to give different, both
   individually-correct, answers. The identity model commits to ONE
   declared primary scale (§9) for its own component-count/shape
   diagnostics, reports what that scale is on every output, and treats a
   different scale's disagreement as a *different question answered*, not
   a contradiction to resolve.

**Spatial overlap alone is never a merger** (case 2 without a `\pi`
collapse is not an event at all); **a detector returning one community
for what are, at a finer scale, two distinct co-located objects is not
necessarily a true merger either** — this is the Beard/Vo/Vo merged-
measurement case, formalized in §7 as a *measurement-model* event
(detector under-resolution), disjoint from the *identity-model* event
"actual merger" (§7's own entry). Both events can produce an identical
`C_t` (one candidate where there were two objects), so distinguishing them
requires evidence beyond the current step's candidate list alone — the
recursion's own transition-model prior (are two nearby, still-distinct
labels' predicted centers converging faster than physically plausible, or
is a merger event actually consistent with both labels' own recent
kinematics?) plus a post-hoc check once (if ever) the two candidates
re-separate. An observation-segmentation ambiguity of this kind is
allowed to remain genuinely unresolved for some steps; forcing an early
call is exactly the discipline item 1F prohibits.

## 7. Event and identity semantics (item 1F)

**Revision note.** An adversarial review of an earlier draft of this table
found three real defects, fixed here rather than patched in place: (1) no
first-class "birth" event existed, contradicting §5's own requirement that
births compete in the same normalization as every other event; (2) the
"missed/ambiguous observation" and "destruction + distant lookalike" rows
overlapped on an undefined "loose retention/shape floor," so the same
scenario could be routed to either row depending on an unstated
implementation choice; (3) "individuation loss" was referenced from the
"background recruitment" row as "next row" but no row matched that
description. All three are resolved below by a single change: the
missed-vs-terminated decision is now made **only** on the transport-
consistency (reachable-set, position-only) check, never on shape, and a
"lookalike" is demoted from its own bespoke mechanism to an ordinary birth
that happens to be shape-annotated — which simultaneously gives births
their own first-class row.

Enumerated event types, each with a precise pre-condition and a precise
effect on `(Z_t, G_t)`. The pre-conditions are evaluated in the STATED
ORDER for each existing or candidate label — this is a decision procedure,
not an unordered list, precisely so that the same scenario cannot satisfy
two rows with different effects:

| step | event | pre-condition | effect |
|---|---|---|---|
| 1 | **Continuation** (incl. growth via recruitment, contraction) | for existing label `\ell`: at least one enumerated candidate clears BOTH the transport-consistency floor (§8's `d_transport`, position/velocity only) AND the likelihood floor under `\ell`'s predicted `(c,\Sigma,\pi)` | `\ell` persists; `m_\ell`, `\Sigma_\ell` updated. Growth via background recruitment is NOT a separate competing event — it is this row, with the additional (diagnostic-only, non-gating) note that recruited members' recent heading history is consistent with having been drawn toward `\ell`'s own preference field, distinguishing healthy growth from row 2 below |
| 2 | **Individuation loss** (a candidate exists and clears row 1, but shows this specific warning sign) | candidate clears row 1's floors, AND is growing, AND its exterior contrast `D` (§10) has collapsed toward the population-wide background level relative to `\ell`'s own recent baseline (reusing the `CONTRAST_DROP_FRAC`-style check `lineage_611.py` already computes, recalibrated in Phase 2, not asserted here) | `\ell` persists but is flagged `status=individuation_loss`; if this status holds for `>= K` consecutive steps (a disclosed, Phase-2-calibrated patience constant, analogous to `lineage_611.py`'s existing `DISSOLVE_AFTER_INDIVIDUATION_STEPS=3`), `\ell` is terminated via row 6 (death) — individuation loss is a precursor warning, not an instantaneous death, and not a component-count check (that is row 3, a different, scale-mismatch phenomenon) |
| 3 | **Detector over-segmentation** (one true object proposed as ≥2 candidates) | `\ell`'s single best explanation is better served by treating ≥2 of this step's proposed candidates as ONE observation of `\ell` than by treating any one of them alone | `\ell` persists as ONE label; the enumeration for `\ell` this step considers the union of the ≥2 candidates as one candidate event, not ≥2 competing births |
| 4 | **Detector merger** (two still-distinct labels' candidates coincide in one returned community) | Beard/Vo/Vo merged-measurement case: the SAME returned candidate is evaluated as a joint observation of BOTH `\ell` and `\ell'`'s predicted states, not forced to pick one | both `\ell`, `\ell'` persist, each retaining separate `w_i^\ell`, `w_i^{\ell'}` for the shared members; resolved (if ever) by later re-separation, never forced this step |
| 5 | **Actual split** / **Actual merger** | split: the SAME label's continuation likelihood is BETTER explained by two candidates each independently transport-consistent with `\ell`'s own kinematics, corroborated over `>1` step. Merger: two distinct labels' predicted states both explain the SAME single surviving candidate substantially better jointly than either alone, corroborated over `>1` step | split: parent `\ell` ends (`terminated_by_split`), two new labels `\ell_1,\ell_2` begin, `G_t` records `parent=\ell` for both. Merger: both parents end, one child begins, `G_t` records `parents={\ell,\ell'}` |
| 6 | **Missed/ambiguous observation** vs. **termination (death)** | Evaluated by TRANSPORT-CONSISTENCY ALONE, never shape: does ANY proposed candidate this step fall within `\ell`'s reachable set (§8, position/velocity process-noise envelope since `\ell`'s last confirmed observation)? If **no** candidate is in-reach: if elapsed time since `\ell`'s last confirmed observation is `<= \tau_{\text{missing,max}}` (a declared, Phase-2-calibrated patience constant), this is a MISS; if it EXCEEDS `\tau_{\text{missing,max}}`, `\ell` is TERMINATED | Miss: `\ell` persists, no membership update, `\sigma_{c_\ell}`,`\sigma_{\Sigma_\ell}` inflate per transition noise (§8), `e_\ell` unchanged. Termination: `\ell` recorded as `terminated_by_timeout`, no parent edge to anything |
| 7 | **Birth** | a proposed candidate this step is not claimed by any existing label under rows 1–6 (i.e. it clears no label's transport-consistency floor) AND its own likelihood under a fresh single-component `f_\ell$ exceeds the birth-prior penalty (§5's mixture-order discipline) | a new label begins, `e_\ell \to 1`, no parent edge in `G_t`. **If** a label was terminated by row 6 within a short lookback window AND this new birth's phenotype `\phi`/shape closely resembles the terminated label's own last state, the birth record carries an explicit, PURELY DESCRIPTIVE `possible_lookalike_of` annotation — this NEVER creates a parent edge, NEVER merges the two labels' identities, and never changes either label's own probability; it is a pointer for a human/analyst reading `G_t`, nothing else. (This replaces an earlier, separate "destruction + distant lookalike" mechanism — Case 8 in `MATHEMATICAL_CHECKS.md` is now an instance of row 6 termination followed by an annotated row 7 birth, not a bespoke event type, which is also what gives births the first-class, competing-event status §5 requires and an earlier draft of this table lacked.) |
| 8 | **Unresolved / genuinely ambiguous** | two or more of rows 1–7 have comparable posterior mass for the same candidate/label and neither dominates by a predeclared margin | `Z_t` reports BOTH (or all) live alternatives explicitly, each with its own probability; no single point estimate is asserted as *the* answer this step |

**Cross-label consistency (the mandate's item 10 concern, made explicit).**
§3's per-label fan-out is a MARGINAL readout of the one joint enumeration
in §5 — rows 4 and 5 above are inherently joint (they involve two labels'
states at once), so "the probability `\ell` merges with `\ell'`" read off
`\ell`'s own exposed fan-out, "`\ell'` merges with `\ell`" read off
`\ell'`'s, and the resulting child's existence probability are three
marginals of the SAME underlying joint hypothesis mass, not three
independently-computed numbers that could drift apart. This is an
invariant the implementation must check (e.g. a unit test asserting these
three marginals agree to floating-point tolerance on every synthetic
merger/split scenario in `MATHEMATICAL_CHECKS.md`), not merely hoped for
by construction.

**For the strict preserve-the-same-object control task** (Phase 4, not
built in this pass): a confirmed split or merger **ends** the original
label's success claim outright — the controller may not silently retarget
onto whichever child is target-favorable. An explicitly different
"descendant-family" task (does *some* descendant of the original object
end up at the target) is a DIFFERENT, separately-labeled task, never
silently substituted for the first.

## 8. Motion and phenotype continuity (item 1G)

Two separate quantities, both modeled, neither conflated:

- **Positional/kinematic continuity**, torus-aware:
  `c_{t+1} = c_t \oplus_L (v_t \cdot dt) + \eta_c`, `v_{t+1} = v_t +
  \eta_v`, where `\oplus_L` is torus-wrapped addition and `\eta_c,\eta_v`
  are learned-variance process noise terms (fit from uncontrolled
  replay, not assumed). Shape/size (`S_\ell`, `m_\ell`) get their OWN,
  separate deformation/growth noise term — a translating collective is
  allowed to deform (elongate along its direction of travel, e.g.) without
  that deformation being read as a positional discontinuity, and
  conversely a rigid-shape translation is allowed without crediting it as
  "no motion happened."
- **Phenotype continuity**: `\pi_{t+1} = (1-\gamma)\pi_t + \gamma\,
  \hat\pi_{\text{obs}} + \eta_\pi`, a slowly-adapting heading-distribution
  memory (`\gamma` small, fit not asserted) — this is deliberately
  DIFFERENT from position: a translating object's own bulk heading is
  expected to be highly persistent from one step to the next (`UV4`
  headings only take 4 values and physical turning is metabolically
  costly in the underlying active-inference model), so `\pi_\ell`
  changing sharply in one step is itself mild evidence of a
  possibly-different underlying object, usable as one input to the
  transport-consistency check below — never sufficient alone (a
  controller-INTENDED 90° turn must be representable as a normal,
  high-likelihood transition under `T`, not an identity failure; see next
  paragraph).

**The four things item 1G asks to be kept separate, made explicit:**

1. **Material overlap** — `|prev \cap cand| / |prev|` (v1's own
   `R_retain`, reused unchanged as one input, not the whole story).
2. **Translated phenotype similarity** — `f_\ell`'s shape/pattern match
   AFTER re-centering on the candidate's own centroid (`identity_69`'s
   existing `R_F`, translation-invariant by construction and confirmed so,
   `INVARIANCE_AND_TRANSFER_6_11.md` §1.1) — "does it look like the same
   kind of thing," independent of where it is.
3. **Displacement likelihood** (`d_transport`) — does the OBSERVED
   displacement between `prev`'s centroid and `cand`'s centroid fall
   within what `\ell`'s own recent velocity/process-noise model (item
   1 above) would predict, INDEPENDENT of shape match. This is v2's
   already-validated fix for exactly the failure mode a shape-only check
   misses (`LINEAGE_V2_METHOD_AND_VALIDATION.md` §2's own worked
   counter-example: two same-shaped Gaussian blobs at opposite corners of
   the box scored `R_F=0.79` on shape alone, purely because shape doesn't
   see location) — reused here as the FORMAL displacement-likelihood term
   in `T`, not an ad hoc bolt-on gate.
4. **Slow phenotype change** — the `\gamma`-filtered `\pi_\ell` above,
   scored by its OWN likelihood, separate from (3)'s positional term.
5. **Controller-requested heading changes** — enter `T` as a KNOWN
   physical input (§5's `u_{t-1}` term, in the *physical prediction* only,
   never in the identity-decision likelihood's own reward) precisely so
   that a 90° turn the controller itself commanded is a HIGH-likelihood,
   not a low-likelihood, transition — a real turn under sustained forcing
   must never be scored as evidence of identity failure merely because
   heading changed; the transition model already expects it once `u_{t-1}`
   is known.

**Explicit non-assumption:** nothing here assumes a pattern's own
propagation speed is bounded by any individual agent's speed `v` (the
`MovingFlock611` per-step displacement bound) — `\eta_v`'s variance is
fit from OBSERVED collective bulk-velocity variability (a wave-like
pattern can, in principle, propagate faster or slower than its
constituent agents move), and an observed displacement far outside that
fit is reported as `\ell`'s state going into the **unresolved** event
bucket (§7), not silently accepted as "still `\ell`, just moving fast" nor
silently rejected as "must be a different object."

## 9. Honest no-jump guarantees (item 1H)

**Architectural guarantees, proven from the recursion's structure, not
claimed as universal identifiability:**

1. **A task stays attached to its selected label `\ell*`.** The control
   layer (§2's diagram) reads only `Z_t[\ell*]`; it has no code path that
   substitutes a different label, however probable, for `\ell*`. (This is
   a controller-contract property, formalized fully in Phase 4; stated
   here because it constrains what the identity layer must expose: `Z_t`
   must always be able to answer "what is `\ell*`'s own current state and
   confidence," even when `\ell*` is NOT the global-MAP label — the exact
   capability v1's `dominant_interior()` = `argmax_h prob` lacks, since it
   only ever reports the argmax across ALL labels/branches, never a named
   label's own marginal.)
2. **A different, independent object cannot acquire the task by winning
   global MAP.** Directly follows from (1) plus §3's joint-state design:
   there is no step in this recursion where "which label is currently most
   probable, system-wide" is read out AS `\ell*`'s identity. This is the
   precise fix to `LINEAGE_FORENSICS_6_11.md` §1.1's mechanism (a
   fully-independent thread, sharing zero members, overtook the displayed
   MAP) — under this design that overtake can still happen to `Z_t`'s
   own global-MAP bookkeeping (some other label may indeed become more
   probable than `\ell*`), but it has no path to *becoming* `\ell*`,
   because `\ell*` is a fixed label identity, not a rank.
3. **An asserted continuation must be an allowed edge in the event/motion
   model.** By construction (§7's table + §8's `d_transport` term): no
   event outside the enumerated set can be asserted, and "continuation"
   specifically requires clearing the transport-consistency check, not
   material overlap alone — this is the direct fix to
   `METHODS_AUDIT_6_11.md` §3's no-death-state defect (an unguarded
   material-overlap floor was previously sufficient by itself).
4. **No acceptable association produces unresolved/dead status, never
   forced replacement.** Directly by §5's normalization requirement:
   "no acceptable transition" is a first-class competing event, so when
   every enumerated candidate's likelihood is poor, that bucket can
   legitimately win instead of the least-bad candidate being forced
   through, unlike v1's unconditional branch-softmax.
5. **Duplicating a proposal cannot manufacture extra probability.**
   Directly by §5's coalescing-before-normalization step (v2's fix,
   reused) — two candidates with the same physical membership contribute
   ONE likelihood evaluation's worth of mass, not two.

**The honest limitation, stated, not hidden:** two objects with
symmetric, statistically-indistinguishable observation histories (same
shape, same phenotype, same distance from a third reference point, e.g.
two identical flocks approaching a crossing from mirror-symmetric
directions) produce an irreducibly ambiguous identity under ANY
observation model that only sees `(r,h)` — no amount of better inference
recovers information the data does not contain. In this case the correct
output is the **unresolved/multi-hypothesis** state (§7's last row) held
openly, with control abstaining on identity-sensitive decisions for
`\ell*` while it is in that state (§13's decision rule handles exactly
this): the posterior is NEVER collapsed to a point estimate that averages
the two symmetric modes into an invented, non-existent "between" flock —
doing so would report a spatial location and shape that no real object
ever occupied.

**Decision rule for wait-vs-associate**, stated once, used by both the
identity layer's own MAP readouts (for display) and, later, by the
control layer's release/hold policy: given a declared loss
`\lambda_{FA}` (cost of a false association) and `\lambda_{wait}` (cost of
one more step of unresolved waiting), associate to a candidate only if
its **unconditional** posterior mass (§3's `w_i^\ell`/label-existence
mass, never mass conditioned on "given `\ell` survives") exceeds
`\lambda_{FA} / (\lambda_{FA} + \lambda_{wait})`; otherwise remain
unresolved. **Derivation, stated explicitly (an adversarial review of an
earlier draft of this document caught this formula written with the
numerator and the ratio's sense inverted — corrected here, re-derived from
scratch rather than patched by inspection):** let `p` be the unconditional
probability the candidate is correct. `E[\text{loss} \mid
\text{associate}] = (1-p)\lambda_{FA}`; `E[\text{loss} \mid \text{wait}] =
p\,\lambda_{wait}` (the other two loss cells — associating correctly, or
waiting when the candidate was in fact wrong — are 0 by construction).
Associate iff `(1-p)\lambda_{FA} \le p\,\lambda_{wait}`, i.e. iff `p \ge
\lambda_{FA}/(\lambda_{FA}+\lambda_{wait})`. **Sanity check the formula
must satisfy, and does:** the threshold must be *increasing* in
`\lambda_{FA}` (a costlier false association demands more confidence
before acting) and *decreasing* in `\lambda_{wait}` (costlier waiting
justifies acting on less confidence) — `\lambda_{FA}/(\lambda_{FA}+
\lambda_{wait})` satisfies both; the earlier, inverted formula satisfied
neither (it would have made a system associate LESS readily precisely
when waiting was expensive). Conditioning on survival first — asking
"given the object is alive, which candidate is it" before asking "is it
alive at all" — is exactly how v1's structure hides the death/unresolved
branch (its branch-softmax normalizes ONLY over the surviving/viable
candidates, per `METHODS_AUDIT_6_11.md` §1.2 step 5): this rule is stated
over the FULL unconditional state space specifically to block that
failure mode by construction. Calibration of this rule (is the resulting
decision threshold actually reliable at the declared losses) is a Phase 2
validation question, not asserted here.

## 10. Spatial measurement contract (item 1I) — summary, full detail in `MEASUREMENT_CONTRACT.md`

Four scales, kept textually and numerically distinct, all observable and
independent of the true simulator `R`:

- **Detection scale**: `detect_69`'s own affinity kernel
  (`SIGMA=1.1`, `KERNEL_CUTOFF=3.3`) — the scale at which the CANDIDATE
  proposal mechanism decides two birds are "close enough to co-occur."
- **Field-smoothing scale**: `identity_69.field`'s own kernel width, used
  for the co-moving-field shape comparison — a SEPARATE, already-existing
  scale, not re-derived here.
- **Morphology scale**: the connectivity radius used for `n_components`,
  compactness, and other shape diagnostics. `THINGNESS_GATE_AUDIT.md`
  §3-4 is decisive evidence that `geometry_611.local_scale`
  (≈0.2-0.3 units, ~10-17x smaller than the detection scale) is the WRONG
  choice for this purpose — not because it is inaccurate at what it
  measures (a genuine, much finer nearest-neighbour spacing), but because
  it answers a different question (individuation-band width) than
  "is this candidate spatially coherent as the thing the detector proposed
  it as." This program's morphology scale is the detection scale itself
  (§9's proposed-but-not-adopted fix from that audit, ADOPTED here after
  the diagnosis, with its own calibration run in Phase 2 — a genuine
  measurement-model correction, versioned as such per the mandate's
  requirement that such changes be validated independently of control
  outcomes, never as a threshold loosened because examples were failing).
- **Exterior/periphery sampling scale**: `nearest_M20` (position-only,
  `BLIND_POOL_AUDIT.md`'s validated primary rule, reused unchanged — it
  already matches the oracle-radius pool's causal-parent recall
  essentially exactly on the sampled snapshots) for any exterior-contrast
  or actuator-candidate sampling this program needs. The `radius_pool`
  alternative is NOT reused, per that same audit's finding that its
  `local_scale`-derived radius is numerically unstable (median pool size
  jumping 0->6->60.5->267.5 across a 5-40 multiplier sweep) — the same
  root cause as the morphology-scale defect above, evidence that
  `local_scale` itself is simply the wrong base unit for anything except
  the fine-grained individuation-band purpose it was originally built for.

**Missingness contract.** An absent exterior/periphery sample (no
non-member bird found within the periphery radius of any member) is
reported as **unavailable evidence** (`D = \text{NaN}`/`None`, explicit
"not measured" flag), never as `D=1.0` — `THINGNESS_GATE_AUDIT.md` §3's
single most important correction: the inherited `geometry_611.
local_exterior_contrast` function's trivial fallback (`return 1.0` on an
empty periphery) manufactured a false "perfectly distinct periphery"
reading in the overwhelming majority of real cases, and this was silently
treated as corroborating evidence in `LINEAGE_FORENSICS_6_11.md` before
being retracted. Every metric in this program's contract returns
`(value, validity_flag, effective_sample_size, estimation_timestamp,
uncertainty_if_available)` — never a bare number.

**G and L**, canonical meanings frozen here (per the mandate's
instruction that earlier stages used different definitions and this must
stop): `G` = the predictive-boundary generalization gap this program's
identity layer would need to certify a candidate's periphery as
predictively screened (reusing `predictive_boundary_611`'s own existing,
already-validated `certify` procedure and `\delta`-tolerance convention,
`RESULTS_6_11.md` §4 / `BPRED_RECERTIFICATION.md`, never recomputed with a
new definition); `L` = the corresponding held-out log-loss the boundary
achieves. Both are allowed to be `None`/stale (this program's control
layer, §2's diagram, already treats them as siblings computed on their
own cadence, not blocking identity) — a missing `G`/`L` is never defaulted
to a value that would make a gate pass, exactly `thingness_611.
passes_gate`'s own existing (correct) convention, reused unchanged.

## 11. Relationship to the existing code, stated plainly

- `identity_69.field`/`estimate_translation`/`similarity` (shape
  comparison after re-centering) — REUSED, confirmed translation-invariant
  (`INVARIANCE_AND_TRANSFER_6_11.md` §1.1), as ONE input to §8's
  transport-consistency check, never the whole check.
- `geometry_611.torus_delta`/`torus_distance_matrix`/`connected_components`
  — REUSED verbatim (correct, torus-aware, verified,
  `THINGNESS_GATE_AUDIT.md` §3's own finding that the algorithm is fine
  and only the radius fed to it was wrong).
- `geometry_611.local_scale` — REUSED for its ORIGINAL, narrower purpose
  (individuation-band width around a candidate's own boundary, if that
  specific diagnostic is still wanted) but NOT reused as the morphology
  scale (§10) or the exterior-pool radius (superseded by `nearest_M20`,
  per `BLIND_POOL_AUDIT.md`).
- `lineage_611.LineageTracker611` (v1) — SUPERSEDED. Its `RETENTION_MIN`
  gate, `dice`/`R_F` blended score, and softmax-branching mechanics are
  the diagnosed defect (§5), not a component to import.
- `audit/lineage_v2_611.py` (v2) — PARTIALLY REUSED, explicitly as
  evidence and as a source of two validated sub-fixes (present-state
  coalescing before normalization; transport-consistency as a distinct
  quantity from shape similarity), NOT as a validated tracker in its own
  right — it never reached its own qualification criterion on any of the
  5 real seeds (`LINEAGE_V2_METHOD_AND_VALIDATION.md` §4.2), and the
  mandate is explicit that this must not be treated as ground truth.
- `detect_69.propose` (Louvain candidate detection) — REUSED as the
  primary candidate-proposal mechanism, WITH the mandate's required
  second, non-Louvain proposal baseline (a position/heading field-based
  method, e.g. thresholded kernel-density-plus-heading-agreement
  connected components, avoiding Louvain's own node-order-dependent
  optimizer entirely) run in parallel so detector-specific artifacts
  (`INVARIANCE_AND_TRANSFER_6_11.md` §1.2's ≤2% permutation
  non-invariance) are visible as a comparison, not baked into every
  downstream number by construction.
- `predictive_boundary_611`, `probing_611`, `control_authority_611`,
  `intervention_api_611` — REUSED, UNCHANGED, as the sibling `B^pred`,
  `B^{D,1}`, `B^{C,\tau}` interfaces (`RESULTS_6_11B.md`'s architecture
  diagram, adopted here verbatim) — this identity model does not replace
  or subsume them; it replaces only the identity/lineage layer they all
  currently sit downstream of via the SAME privileged `near_exterior`
  pool (§10 replaces that pool with `nearest_M20` for any NEW exterior
  sampling this program does, but does not edit those existing modules).

## 12. What Phase 1 (this document + `MATHEMATICAL_CHECKS.md`) does NOT settle

- Whether the wrapped-elliptical-Gaussian mixture (§4) is an adequate
  identity likelihood at the primary regime's actual densities, or
  whether its conditional-independence misspecification is large enough
  to distort existence/event inference (not just heading prediction,
  where it is already known to be a weaker model than the relational
  predictor) — a Phase 2 calibration question.
- Whether the detection-scale morphology contract (§10) actually produces
  a usable, non-degenerate spatial-integrity gate at the primary regime,
  the way `THINGNESS_GATE_AUDIT.md` §4 speculates but explicitly does not
  validate ("a proposal, not a threshold change... not calibrated, tested
  against control outcome, or applied to any decision").
- Whether the transport-consistency check (§8) correctly separates every
  one of the mandate's required tiny examples (complete constituent
  turnover under continuous translation vs. an unrelated spatial jump) —
  checked in `MATHEMATICAL_CHECKS.md`, not here.

These are exactly the questions `MATHEMATICAL_CHECKS.md` (analytical/tiny-
scene checks) and, subsequently, Phase 2's synthetic + real-replay
validation protocol exist to answer — not to be asserted resolved by this
document.
