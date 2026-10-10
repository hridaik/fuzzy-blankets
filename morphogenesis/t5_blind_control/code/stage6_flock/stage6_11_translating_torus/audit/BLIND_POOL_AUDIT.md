# Blind Exterior Pool Audit — Stage 6.11B (item 4)

Additive comparator. `intervention_api_611.near_exterior` (the true-R
oracle pool, `METHODS_AUDIT_6_11.md` §2's flagged firewall violation) is
preserved UNCHANGED and imported only for side-by-side reproduction below —
never called to build a pool that feeds any Stage 6.11B decision. Script:
`audit/blind_pool_611.py`. Raw output: `audit/blind_pool_611.json`.

## 1. Two blind rules, chosen from computational budget / dev data, not recall

- **`nearest_M_pool`** (PRIMARY): the `M` non-member birds nearest (torus
  distance, positions only) to any candidate member. `M_probe = 20`,
  matching `predictive_boundary_611.M_OBS_GRID`'s own larger value — an
  already-validated design constant reused for consistency, not chosen by
  maximizing recall. `M=12` and `M=30` reported as disclosed sensitivity
  alternatives (same convention as `M_OBS_GRID`).
- **`radius_pool`** (secondary/diagnostic): non-members within `k ×
  local_scale` of any member. Calibrating `k` on uncontrolled development
  data to land near the primary rule's median pool size (20) exposed the
  same brittleness `THINGNESS_GATE_AUDIT.md` found in `local_scale` itself:
  median pool size jumps **0 → 6 → 60.5 → 267.5** as `k` moves **5 → 10 → 20
  → 40** — there is no stable `k` that gives a reasonable, predictable pool
  size, because `local_scale` (≈0.2–0.3 units) is too small a base unit for
  this purpose (the same root cause item 3 diagnosed). The nearest-count
  rule does not inherit this instability and is therefore the recommended
  primary rule, not merely an arbitrary pick.

Neither rule ever receives the simulator's true `R`, FOV rule, or live-edge
graph — both are pure functions of observed positions.

## 2. Recall: `N_exterior → N_pool → N_true_direct_parents_in_pool`

36 snapshots (6 uncontrolled dev-val episodes at a fixed step, plus every
4th control-phase frame from all 5 online seeds — reference-only comparison
against `oracle_B_D`, never fed back into any decision):

| pool rule | mean pool size | mean maximum attainable direct-parent recall |
|---|---|---|
| nearest_M12 | 12.0 | 99.1% |
| **nearest_M20 (primary)** | **20.0** | **100.0%** |
| nearest_M30 | 30.0 | 100.0% |
| oracle `near_exterior`(3R) (reproduction only) | 17.4 | 100.0% |

**The blind pool matches the privileged oracle pool's recall essentially
exactly, at a comparable size.** The `near_exterior`(true R) firewall
violation identified in `METHODS_AUDIT_6_11.md` §2 does not appear to buy
any real recall advantage on this sample — a pool built from positions alone
recovers the same true one-step causal parents. This is a clean, positive
result for the repair: `nearest_M20` is a directly usable, no-compromise
replacement for the primary online pipeline's causal/authority candidate
pool, ready to be substituted in the Part-9 adjudication branches.

## 3. What this does and does not establish

This is a recall/attainability check on a modest snapshot sample (36
snapshots, drawn from uncontrolled dev data and the 5 already-known online
seeds), not a claim that the blind pool matches the oracle pool in every
regime or at every interior size/shape. It also says nothing about
estimation quality once a source is in the pool (that is Part 6-9's
authority-repair question) — only about whether the RIGHT birds are even
available to be selected from.
