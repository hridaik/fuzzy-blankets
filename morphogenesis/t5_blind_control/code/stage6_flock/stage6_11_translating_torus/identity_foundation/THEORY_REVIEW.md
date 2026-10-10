# THEORY_REVIEW.md — theory acceptance gate record

Per the mandate: "provide an internal independent check of normalization,
dimensions, counterexamples, event consistency and duplicate invariance...
Otherwise create an adversarial review as a separate pass and state it was
not an independent reviewer." **Disclosure, stated plainly: this was NOT a
truly external independent reviewer.** It was a fresh `general-purpose`
agent instance with no inherited conversation context, briefed cold on the
three documents and told to find counterexamples — a genuine attempt at an
adversarial, disinterested read, but run inside the same session and by
the same underlying model as the documents it reviewed, not a separate
tool or a different reasoning system. Its full findings are preserved
below, unedited in substance, followed by this session's resolution of
each.

## Review scope and method

Reviewer read `CLAIMS_LEDGER.md` (as settled background, not re-litigated),
`IDENTITY_MODEL.md`, and `MATHEMATICAL_CHECKS.md` in full, cold, and was
asked to check: normalization, dimensional/type consistency, counterexamples
to identifiability claims, event consistency (mutual exclusivity/
exhaustiveness of §7's event table), duplicate invariance under
near-duplicates, the wait-vs-associate decision rule's derivation,
authority-by-assertion, and cross-document consistency. Told explicitly not
to fix anything, not to re-litigate `CLAIMS_LEDGER.md`, and not to nitpick
prose/citations.

## Findings and resolution

| # | severity (reviewer's tag) | finding | resolution |
|---|---|---|---|
| 1 | CONFIRMED-ISSUE | Wait-vs-associate threshold (§9) was `\lambda_{wait}/(\lambda_{wait}+\lambda_{FA})` — the numerator/ratio sense inverted relative to the correct Bayes-risk break-even point. Reviewer gave a full re-derivation and a numeric monotonicity counterexample (`\lambda_{FA}=1,\lambda_{wait}=10` gave threshold 0.91 under the old formula, demanding MORE caution when waiting was expensive — backwards). | **Fixed.** Independently re-derived from the loss table this session (see the numeric check run below), confirmed the reviewer's direction is correct: `p^* = \lambda_{FA}/(\lambda_{FA}+\lambda_{wait})`. `IDENTITY_MODEL.md` §9 now states the corrected formula with the full derivation and the monotonicity sanity check inline, so a future reader can re-verify without re-deriving from scratch. |
| 2 | CONFIRMED-ISSUE | §7's "Background recruitment" row referenced "individuation loss (next row)" but the actual next row was detector over-segmentation — the concept `MATHEMATICAL_CHECKS.md` Case 6 relies on had no matching row in `IDENTITY_MODEL.md` at all. | **Fixed.** §7's event table redesigned as an explicit 8-row ordered decision procedure; "Individuation loss" is now its own numbered row (row 2) with a precise precondition (exterior contrast collapse, distinct from component-count issues) and effect (a precursor warning that converts to termination after a declared patience constant, not instantaneous death). `MATHEMATICAL_CHECKS.md` Case 6 updated to cite the correct row number. |
| 3 | CONFIRMED-ISSUE | §7 had no first-class "Birth" row, contradicting §5's own requirement that births compete in the same normalization as every other event; this also undercut Honest Guarantee #4 in §9. | **Fixed.** Birth is now row 7 of the redesigned table, with its own precondition (unclaimed by any existing label, likelihood exceeds the birth-prior penalty) and effect. This also resolved finding #4 below in the same edit (see next row). |
| 4 | LIKELY-ISSUE | §7/§8 tension: an undefined "loose retention/shape floor" meant the same far-displacement scenario could route to either "missed/ambiguous observation" or "destruction + distant lookalike" depending on an unstated shape-vs-position reading, with no tiebreak given. | **Fixed, and simplified.** The redesigned row 6 makes the missed-vs-terminated decision on TRANSPORT-CONSISTENCY (reachable set) ALONE, never shape, with an explicit elapsed-time patience threshold (`\tau_{\text{missing,max}}`) separating the two. "Destruction + distant lookalike" is no longer a separate mechanism at all — it is now row 6 termination followed by an ordinary row 7 birth, with phenotype similarity demoted to a purely descriptive `possible_lookalike_of` annotation that never affects any probability or creates a parent edge. This one change resolved both finding #3 (births now first-class) and finding #4 (no more floor ambiguity) simultaneously. `MATHEMATICAL_CHECKS.md` Case 8 rewritten to match. |
| 5 | CONFIRMED-ISSUE | Duplicate coalescing (§5) was specified only for EXACT member-set identity, but `CLAIMS_LEDGER.md` item D1 (settled background) already establishes the real detector has ≤2% (1–2 bird) disagreement on reruns of the same physical candidate — meaning near-duplicates, which will occur routinely, would NOT be coalesced under the literal rule, reintroducing a softened double-counting defect. | **Fixed.** §5 now specifies tolerance-based (Jaccard `>= 0.9`, Phase-2-calibrated) coalescing with union-of-members and explicit provenance, chosen to comfortably clear the measured ≤2% noise band. `MATHEMATICAL_CHECKS.md`'s Case 2 duplicate-invariance check is now explicitly required at both exact (`J=1`) and near-duplicate (`J≈0.9–0.99`) settings in Phase 2, not just the exact case. |
| 6 | CONFIRMED-ISSUE | `S_\ell` (§3) had no declared space, a wrong cross-reference ("§9's contract" — §9 is the no-jump-guarantees section, not the measurement contract, which is §10), and an incoherent noise model (a single continuous stochastic process was implied to perturb both a continuous covariance AND a discrete component count together). | **Fixed.** §3 now defines `S_\ell` as ONLY the continuous covariance-like matrix `\Sigma_\ell` (the actual latent, noise-propagated state, per §8), with component count and other morphology diagnostics explicitly demoted to derived, recomputed-each-step observation-side quantities (§10, cross-reference corrected) — never a second state variable with its own noise term. |
| 7 | LIKELY-ISSUE | Case 3b's "irreducibly ambiguous" framing overclaimed: the ambiguity there arises because the §4 mixture's OWN choice to use only aggregate per-label parameters discards per-bird history that is, in this constructed scenario, in principle informative — a modeling choice, not a fundamental data limit like Case 10's true bird-level mirror symmetry. | **Fixed.** Case 3b's writeup now explicitly distinguishes "not resolved by this model's chosen simplification" from Case 10's stronger "the data itself does not contain the information," with Case 10's own setup strengthened to stipulate individual-bird-level (not just aggregate-parameter) symmetry so it genuinely earns the stronger claim. The identifiability summary table's row for 3b reworded to match. |
| 8 | MINOR | "Continuation" and "Background recruitment" rows were not disjoint as stated (a growing, heading-consistent continuation satisfied both). | **Resolved as part of fix #2/#3's table redesign** — recruitment is now explicitly a growth sub-case of row 1 ("Continuation"), not a separate competing row, removing the false appearance of a second category. |
| 9 | MINOR | The detector-over-segmentation row lacked a bold event name (cosmetic, tied to #2's broken reference). | **Fixed** as part of the table redesign — now "**Detector over-segmentation**," row 3. |
| 10 | LIKELY-ISSUE (flagged open, not asserted wrong) | How per-label marginal fan-outs (§3) relate to the claimed single joint `p_t(Z_t,G_t)` (§5) for inherently cross-label events (merge/split/detector-merger) was never made explicit — e.g., that A's "merges with B" mass, B's "merges with A" mass, and child C's existence probability must agree. | **Addressed with an explicit invariant, not a full proof.** §7 now states this consistency requirement directly (the three marginals are readouts of the same joint hypothesis mass) and requires it be checked by a unit test comparing the three marginals to floating-point tolerance on every synthetic merger/split scenario — an implementation-time verification obligation, not asserted as automatically true by construction alone. |
| 11 | NON-ISSUE-CHECKED | Mixture weight `\pi_\ell = e_\ell m_\ell/N` initially looked like it conflated existence uncertainty with per-bird assignment, but survives as a correct marginal-density formula regardless of inter-member correlation structure. | No change — reviewer confirmed this is fine. |
| 12 | NON-ISSUE-CHECKED | Normalization discipline separating exact small-scene enumeration from real-scale bounded/truncated enumeration with disclosed unaccounted mass. | No change — reviewer confirmed this is fine and is exactly the discipline the mandate asked for. |
| 13 | (rolled into #3) | Authority-by-assertion check: mostly clean; the one flagged instance (Honest Guarantee #4 in §9, undercut by the missing Birth row) is resolved by fix #3/#4 above. | Resolved as part of #3/#4. |

## Independent verification performed this session (not merely trusting the reviewer's derivation)

Before editing anything, this session independently re-derived the
wait-vs-associate threshold from the four-cell loss table
(`E[\text{associate}]=(1-p)\lambda_{FA}$, $E[\text{wait}]=p\lambda_{wait}$)
and ran a numeric monotonicity table over `\lambda_{FA},\lambda_{wait} \in
\{1,5,10\}` confirming the corrected formula (`\lambda_{FA}/(\lambda_{FA}+
\lambda_{wait})`) is the one satisfying "threshold increases in
`\lambda_{FA}`, decreases in `\lambda_{wait}`," and that the document's
prior formula satisfied neither — see the numeric output captured in this
session's tool history. This was not accepted on the reviewer's authority
alone.

## Verdict after fixes

The reviewer's overall verdict on the pre-fix documents was "fails as-is;
pass-with-fixes, not implementation-ready," with three non-cosmetic
findings (#1, #2, #3) and two likely issues (#4, #5) requiring correction,
plus a real but more minor gap (#6) and a scope-of-claim overreach (#7).
All seven are now fixed as described above, plus the two minor items (#8,
#9) resolved as a side effect, and the one open-but-not-necessarily-wrong
item (#10) closed with an explicit, checkable invariant rather than left
implicit. `check_report_completeness.py` re-run clean after all edits (one
pre-existing false-positive, already reviewed and explained in
`CLAIMS_LEDGER.md`'s own history, not a new issue). `MATHEMATICAL_CHECKS.md`
and `IDENTITY_MODEL.md` are internally consistent with each other as of
this revision (cross-checked section-by-section during the fix pass, not
merely asserted).

**This does not constitute re-review by a second independent pass** — the
fixes above were applied by the same session that requested the review,
not verified by a further adversarial pass. If a stricter gate is wanted
before Phase 2 implementation begins, a second, fresh adversarial pass
specifically re-checking these seven fixed sections (not the whole
document again) would be the proportionate next step, flagged here as an
option rather than performed unprompted.
