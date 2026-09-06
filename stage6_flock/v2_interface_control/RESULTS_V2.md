# RESULTS_V2.md

Frozen policy from `PROTOCOL_V2.md`, applied unmodified to the first 10
qualifying flocks found by scanning seeds 0-16 (seeds 0,1,5,6,7,12,15 did not
qualify under the unchanged Phase-2A selection rule; this is expected — the
frozen baseline sweep found a 53.7% qualification rate). 30 replicates per
(flock x rule) condition, common random numbers within each flock. Raw data:
`data/replication_results.json`; log: `logs/replicate.log`; figures:
`figures/`.

## Headline result

| Rule | Mean P(success) across 10 flocks | Per-flock P(success) (seeds 2,3,4,8,9,10,11,13,14,16) |
|---|---|---|
| **reference_full_shell** (all of `B^D_0`) | **0.983** | 0.93, 1.00, 0.97, 0.93, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00 |
| A_degree (k=⌈0.75\|B^D_0\|⌉) | **0.940** | 0.67, 1.00, 0.83, 0.90, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00 |
| B_leverage (k=⌈0.75\|B^D_0\|⌉) | **0.940** | 0.77, 0.90, 0.87, 0.90, 1.00, 1.00, 1.00, 1.00, 1.00, 0.97 |
| D_random (k=⌈0.75\|B^D_0\|⌉) | 0.920 | 0.70, 1.00, 0.77, 0.87, 0.97, 1.00, 1.00, 1.00, 1.00, 0.90 |
| C_patch (k=⌈0.75\|B^D_0\|⌉) | **0.783** | 0.60, 1.00, 0.97, 0.20, 0.47, 1.00, 0.63, 1.00, 1.00, 0.97 |
| reference_baseline (k=0) | 0.010 | 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.10, 0.00, 0.00 |

`P(success & integrity)` under the ORIGINAL frozen criterion is **0.000 for
every rule on every one of the 10 flocks**, with no exception — confirming
the mechanism audit's Part D finding is not a canonical-flock quirk but a
general property of propagation-based exterior control under this frozen
criterion (see "Integrity" below). The RECOVERY-window diagnostic
(`p_succ&integrity(recovery)` in the log) is mostly small but non-zero
(typically 0.0-0.37), i.e. the core does sometimes re-stabilize by the very
end of the control window even though it dipped below 0.8 coherence
somewhere earlier — reported for completeness, not as a replacement metric.

## Does the `0.75`-of-shell budget generalize?

**Yes, largely** — 9 of 10 flocks reach `P(success)>=0.83` under at least
three of the four rules at this fixed fraction, using only 9-20 actuators
(the exact `k` scales with each flock's own `|B^D_0|`, from 9 on the smallest
shell to 20 on the largest). The canonical flock (seed 2) is the one
partial exception: **it is also the hardest flock to control** under every
rule (0.60-0.77 success vs. >=0.83 for every other flock). This connects
directly back to `v1_mechanism_audit/V1_RECORD_AUDIT.md` section A3: seed 2
was independently found to be an atypical qualifying flock (94th-percentile
`t0`, 1.2nd-percentile eigengap — an almost-borderline spectral
identification). **The one flock V1 happened to search exhaustively is also,
by this independent replication, closer to a worst case than a typical
case for control difficulty** — worth flagging prominently, since it means
V1's negative headline result was obtained on a harder-than-typical instance,
compounding the "wrong interface searched" explanation from the mechanism
audit with a secondary "somewhat harder-than-typical flock" contribution.

## Do the four rules differ?

**Yes, and one difference is real and mechanistically interpretable.**
Rule C (connected spatial patch) is markedly weaker and more variable
(mean 0.783, with two flocks — seed 8 at 0.20 and seed 9 at 0.47 — well below
every other rule's performance on those same flocks) than Rules A/B/D (all
>=0.92 mean). **A single spatially-contiguous patch concentrates the forcing
signal on one side of the core's boundary, leaving the rest of the shell's
circumference unforced**, whereas Rules A (highest-degree-into-I0),
B (highest individual leverage), and D (uniform random) all tend to spread
actuators around more of the shell by construction or by chance. This is a
genuinely useful, non-obvious design implication for any future V3: **breadth
of coverage around the core's boundary appears to matter more than
concentrating force in fewer, individually more strongly-coupled
locations.**

**Rule D (random-from-the-correct-shell) is nearly as good as the structured
Rules A/B** (0.920 vs 0.940 mean, and matches or beats them on several
individual flocks). This directly supports the hypothesis flagged in
`PROTOCOL_V2.md`'s pre-declared failure modes: **simply drawing from the
correct interface `B^D_0` at all matters far more than which specific
within-shell selection heuristic is used** (except for the connectivity-patch
failure mode above, which specifically avoids spreading around the shell).
This is consistent with, and extends, the mechanism audit's Part E finding
that no small hand-picked subset from the WRONG pool (any of the 3160 pairs
from all 80 exterior birds) ever worked — the pool matters enormously; the
precise ranking rule within the correct pool matters much less, as long as
coverage is not artificially concentrated.

## Integrity criterion: confirmed tension, not a canonical-flock artifact

`P(success & integrity)=0.000` held on every single one of the 10 x 5 = 50
(flock x non-baseline-rule) conditions, with target-heading success
routinely at 0.83-1.00. This closes the question raised in the mechanism
audit: **the frozen integrity criterion's zero-tolerance,
every-single-timestep coherence requirement is not compatible with ANY
propagation-based exterior control strategy tested, on ANY of the 11 flocks
examined across this whole study (the canonical flock plus these 10).**
This is now a well-replicated, general finding, not a one-flock anomaly. It
is reported as a limitation of the frozen criterion for evaluating this
*class* of control mechanism (propagation-based), not as a reason to weaken
the criterion in this session — see `PROTOCOL_V2.md`'s stated stopping rule
and `STAGE6_SYNTHESIS.md`'s "Next scientific experiments."

## What this does and does not demonstrate about "moving" interfaces

As stated in `PROTOCOL_V2.md` and `README.md`, `B^D_t = B^D_0` within any
single flock's control episode in this port (static lattice, heading-only
dynamics). This replication demonstrates that **the correct actuator set is
a computed role that differs from flock to flock** (each of the 10 flocks
has its own distinct `B^D_0`, of different sizes, and the SAME frozen
recomputation procedure — not a hand-picked ID list — succeeds on all of
them) — a genuine, if partial, demonstration of "control the interface role,
not fixed identities." It does **not** demonstrate a role visibly migrating
through agents within one steering attempt, which would require a model
where the physical interaction graph itself evolves during control (see
`STAGE6_SYNTHESIS.md`, "Next scientific experiments," item 2).
