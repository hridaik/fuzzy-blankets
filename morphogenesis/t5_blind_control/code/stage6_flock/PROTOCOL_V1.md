# PROTOCOL_V1.md — Frozen experimental protocol for Experiment 1

**SHA-256 of `configs/protocol_v1.yaml` at current freeze**:
`8b2882f21f9f1079afbef440c76ce5fd9319e9a0d58f53c5e968e3771e698f10`
(supersedes an earlier freeze, hash `cd5cf384...`, corrected per section 1a below
— the earlier hash is retained here only for the audit trail, not as an
alternative valid protocol.)

This file is frozen. Everything below was decided using **only** the uncontrolled
baseline ensemble in `data/baseline_v1/baseline_rows.json` (300 replicates, seeds
0-299, `nn=100, nt=60`, produced by
`python/analysis/baseline_characterization.py`). No control/intervention code
had been run when the *thresholds* below (eigengap, coherence, size, `T_u`,
success/integrity criteria) were fixed. Any later change to those thresholds is
a `protocol_v2`, not an edit to this file. Section 1a documents one exception:
a pure *definitional/encoding* correction (what counts as "the adjacent cardinal
heading"), applied uniformly and discovered via Phase 3A control diagnostics —
before, not after, the sparse-actuator search (Phase 4/5) — and applied to
recompute the same already-frozen thresholds, not to relax them.

## 1a. Encoding-bug correction (applied before Phase 4/5, after Phase 3A)

The upstream heading-state order is `{0:up, 1:down, 2:left, 3:right}` (from
`buildA`'s `uv` table — see METHODS_AUDIT.md section 2). This order is **not** a
rotational cycle: `up->down` and `left->right` are 180-degree flips, while
`down->left` and `right->up` are genuine 90-degree turns. The task's
"adjacent cardinal heading" (`h_star`) was initially computed as naive
`(h0+1) mod 4` index arithmetic, which is only a genuine 90-degree turn for 2 of
the 4 possible `h0` values and is a 180-degree flip for the other 2 (`h0=0` and
`h0=2`).

**This was caught, not assumed**: the canonical snapshot's `h0=2` (left) is one
of the affected cases. Running Phase 3A's positive/negative controls with the
naive `h_star=3` (right — actually the *opposite* of left) produced an
anomalous 32% spontaneous ("no control") success rate for the very case the
aggregate baseline sweep had characterized at ~7% for `T_u=20`. That mismatch
was investigated immediately (per the task brief's "unexpected results should
first trigger deterministic unit checks" instruction) rather than proceeding —
`tests/test_rotation.py` confirms geometrically that `(h+1)%4` is neither the
clockwise nor counter-clockwise 90-degree rotation. The fix
(`flock_sim.model.ROT_CW`/`ROT_CCW`, derived directly from the `uv` unit
vectors, convention: clockwise) was applied uniformly to
`baseline_characterization.py` and `canonical_snapshot.py`, and **both were
re-run from scratch before any actuator/control experiment (Phase 4/5) was
written or run.** The pre-fix baseline run is preserved, not deleted, under
`data/baseline_v1_buggy_naive_hstar_DO_NOT_USE/` for audit purposes. The
corrected canonical `h_star = rotate_cw(2) = 0` (up), not 3 (right). The
`t0`/`I0`/`h0` identification itself is unaffected by this fix (it never
depended on `h_star`) — confirmed identical (`t0=41, |I0|=20, h0=2`) before and
after.

Post-fix Phase 3A results (50 replicates each, from the canonical `t0` state,
common random numbers):

| Arm | mean H*(t0+Tu) | P(success) | P(success & integrity) | mean H*(t0+Tu+Tr) release |
|---|---|---|---|---|
| No control (baseline) | 0.000 | 0.000 | 0.000 | 0.000 |
| Positive control (force entire `I0`) | 1.000 | 1.000 | 1.000 | 0.594 |
| Negative control (single Chebyshev-farthest non-interior bird, bird 0) | 0.000 | 0.000 | 0.000 | 0.000 |

This is now internally consistent (Gate D passes): the baseline spontaneously
never reaches the target within `T_u=20` for this exact initial condition
(consistent with the aggregate ~7% rate over a different population of
qualifying snapshots), direct full-core forcing trivially succeeds, and a
single distant bird has no measurable effect — confirming the intervention
hook does what it is supposed to do before any sparse-actuator search begins.
One further genuine finding worth flagging: even under full-core forcing,
`mean H*` at release (`t0+Tu+Tr`) drops to 0.594 — i.e. **on average
40% of the forced core reverts away from the target heading within `Tr=20`
steps of releasing control, even in the strongest possible (whole-core) forcing
condition.** This is reported as-is; no persistence threshold has been loosened
to accommodate it (the frozen `persistence_threshold_Hstar=0.5` in section 5
still applies, and 0.594 clears it only barely).

## 1. A real, load-bearing finding from the baseline sweep

Before fixing thresholds, the baseline run surfaced a genuine phenomenon (see
PORT_VALIDATION.md section 3): once this flock reaches full polarization
(all 100 birds sharing one heading — which happens reliably by `t~15-25` and is
essentially an absorbing state given `precB=15`), the heading-agreement graph
over any `TW`-step window becomes a complete, uniformly-weighted graph. Its
Laplacian is exactly `TW*(N*I - J)`, whose spectrum is `{0, TW*N, TW*N, ...}` —
i.e. `lambda2 = lambda3` **exactly**, an unbounded degenerate eigenspace, at
full consensus. The Fiedler-based macro-agent identification is therefore only
meaningful during the **transient** alignment phase, not the eventual steady
state. This directly motivated requiring a minimum eigengap in the selection
rule below (methodological trap #6 in the task brief, encountered as a real
phenomenon rather than a hypothetical).

## 2. Selection rule (Phase 2A), frozen

A candidate interior `I_t^F` (either `core1_nodes` or `core2_nodes` from the
Fiedler classification, whichever qualifies) at time `t` qualifies iff, at `t`,
`t+1`, and `t+2` (a 3-step stability window):
- `eigengap(t) = lambda3(t) - lambda2(t) >= 1.0`
- `10 <= |I_t^F| <= 30`
- `coherence(I_t^F, t) >= 0.90`
- consecutive-step Jaccard overlap of the qualifying side `>= 0.6`

`t0` = the first `t >= TW-1 = 4` (search bound `t < 57`, i.e. `nt_search - 3`)
satisfying all four conditions simultaneously. `TW=5` throughout (upstream
default). **Baseline characterization of this exact rule** (300 replicates):
found a qualifying `t0` in 161/300 runs (53.7%); among those, `t0` median = 8
(mean 13.4, range 4-57), `|I0|` median = 20 (mean 19.6, range 13-20 — consistent
with the top/bottom-20%-of-100 mechanism, see the "near-tautological size"
caveat in section 5), eigengap median = 9.73 (min among qualifiers 1.12),
coherence mean = 0.976 (min 0.900).

Note `|I_0|` sizes cluster tightly near 20 largely *because* `core1`/`core2` are
defined by fixed percentiles of a 100-node population — this is a structural
property of the classification method, not a discovery about flock size, and is
flagged accordingly (methodological trap #8, extended from boundary size to
core size).

## 3. Canonical snapshot (Phase 2B), frozen

Rule: **the smallest seed (from 0) for which the Section 2 rule finds a
qualifying `t0` within `nt_search=60`.** Seeds 0 and 1 did not qualify; **seed 2
is the first that does** (`t0=41`, `|I0|=20`, `h0=2` (left), `eigengap=1.39`,
`coherence=1.0`). This was read off mechanically from the already-computed
baseline sweep, not selected by inspecting which snapshot "looks nice."

`h* = (h0 + 1) mod 4 = 3` (right).

The canonical run is re-executed to `nt_total=100` (rather than 60) purely so
there is room for `T_u + T_r` after a `t0` that happened to land at 41 — this is
a logistics decision (simulation length), not a threshold, and does not touch
success/integrity criteria. Because the simulator's RNG stream is deterministic
and strictly sequential given a fixed seed, the `t<=60` portion of the `nt=100`
run is bit-identical to the `nt=60` baseline run that discovered `t0`; re-running
does not change `t0`, `I0`, or `h0`.

## 4. Task-nontriviality check and horizon choice (Phase 2C / methodological trap #4), frozen

Spontaneous (uncontrolled) attainment of `H*(t0+T_u) >= 0.8` among the 161
qualifying baseline replicates:

(Numbers below are post rotation-bug-fix, section 1a; the fix left `T_u=20`'s
chosen value numerically unchanged at this precision, `0.066` before and
after — the other horizons shifted slightly.)

| `T_u` | n (replicates with data) | mean `H*` | P(`H*>=0.8`) |
|---|---|---|---|
| 10 | 157 | 0.065 | 0.013 |
| 20 | 151 | 0.129 | 0.066 |
| 30 | 146 | 0.173 | 0.110 |
| 40 | 123 | 0.202 | 0.154 |

**`T_u = 20` is chosen**: spontaneous success is low (6.6%) — the task is
non-trivial — while still long enough to plausibly allow a sparse external
signal to propagate across a ~20-bird interior on a 10x10 lattice (an
interior this size typically spans several lattice hops; `T_u=10` risks being
too short for any external influence to physically propagate, independent of
whether the true effect is real). `T_u=40` was rejected because spontaneous
success climbs to ~19%, uncomfortably close to muddying causal attribution.
`T_r = 20` (post-release observation window) is set equal to `T_u` by default;
this was not itself swept against baseline data (documented as a plain default,
not a data-driven choice, for honesty).

## 5. Success / integrity / persistence criteria, frozen

- **Task success**: `H*(t0+T_u) >= 0.8` (fraction of frozen-core birds `I0` at
  the target heading `h*` at the end of the control window).
- **Integrity during control**: `C_{I0}(t) >= 0.8` for every `t` in
  `[t0, t0+T_u]` (the frozen core must not itself fragment/decohere while being
  steered).
- **Integrity, spectral lineage**: `R_I(t0+T_u) >= 0.5` (at least half of `I0`
  still recognized as the current spectral interior, sign-aligned to `I0` via
  the upstream `align_to_reference` rule, in a trailing `TW=5` window ending at
  `t0+T_u`).
- **Persistence after release**: `H*(t0+T_u+T_r) >= 0.5` — deliberately a
  *weaker* bar than the task-success threshold, because its purpose is only to
  distinguish "reverted immediately" from "at least partially self-sustained,"
  not to demand the same standard as active control.

## 6. Probabilistic success and replicate counts, frozen

`P(success)` and `P(success AND integrity)` are estimated from repeated
stochastic evolutions starting from the exact canonical `t0` state (same `I0`,
same actuator set, same forced pulse), varying only the downstream RNG seed.
Development/search uses **50** replicates per candidate actuator set. The final
canonical comparison targets the brief's requested **200+**; if compute/time
budget in this environment forces fewer, the actual count used is logged
per-run in `RESULTS_V1.md` together with the reason — never silently reported as
if it were 200+. Acceptance threshold for the actuator search:
`P(success) >= p_min = 0.5` (frozen now, before any actuator is tested).

## 7. Actuator search procedure, frozen

`k=1`: exhaustive over all `nn - |I0| = 80` non-interior birds (50 replicates
each). If no single bird reaches `P(success) >= 0.5`, take the top-10 birds by
empirical response magnitude from the Phase 4 response map and exhaustively test
all pairs among them; if still no success, greedy search for `k>2`. Any
non-exhaustive result is reported as "smallest found under the stated
procedure," never as a global minimum.

## 8. What is explicitly NOT frozen / left to later phases

The exact set of birds probed in the Phase 4 response map (all 80 non-interior
birds, at `response_map_replicates=30`, reduced from the 200+ target purely for
compute time — the full 80-bird x 200-replicate sweep would be ~15,000
independent 20-step simulations, decided against given this session's time
budget) and the specific greedy/pairwise search path if `k=1` fails are
determined by the data as they arrive, per the brief's own instructions (Phase
4/5A are explicitly meant to be exploratory search, not pre-registered
outcomes).
