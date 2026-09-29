# Stage 6.12C — Predictor Freeze

This document freezes the exact predictor under confirmatory test **before**
any Stage 6.12C confirmatory outcome was viewed. It was written and
committed to before `run_confirmatory_612c.py` was executed on the 10
confirmatory states (seeds 63200-63209).

## What is frozen

**Source path**: `stage6_flock/stage6_12B_contact_persistence/code/intervention_612b.py`,
function `kinematic_contact_scores` (lines 75-97 as of this task's start).

**Provenance note (no apology, just fact)**: `stage6_12B_contact_persistence/`
is an UNTRACKED directory in this repository's git history (confirmed via
`git status` at the start of this task — it appears as `??` alongside
`stage6_12_control_readiness/`). There is therefore no git commit hash that
can be cited for this file. In its place, this document freezes the
function by literal content hash of the file it lives in, computed once,
before this stage's own confirmatory runs:

```
$ sha256sum stage6_flock/stage6_12B_contact_persistence/code/intervention_612b.py
203bf1a584831feedf8f913897e877b0999666428b2c41d74cc0df31dd9f3b2a  stage6_flock/stage6_12B_contact_persistence/code/intervention_612b.py
```

Stage 6.12C's own code (`stage6_12C_kinematic_contact_confirmation/code/`)
imports this function directly from that file path
(`stage6_12B_contact_persistence/code/intervention_612b.py`, via
`common_612c.py`'s `IB` alias) — it is never copied, re-typed, or
re-implemented anywhere in Stage 6.12C. If that source file's content hash
ever changes after this document is written, the predictor used by Stage
6.12C's confirmatory runs is no longer the one described here, and any
result computed after such a change must not be described as testing this
frozen predictor.

## The frozen implementation, quoted verbatim

```python
def kinematic_contact_scores(r_t, z_t, candidates, target_members, L, v, window, R=None):
    """Returns {candidate_id: score}. If R is given, score = count of
    predicted future steps (tau=1..window) where the predicted candidate-
    target distance is <= R, summed over all target members (labelled
    'physics-assisted predicted contact' by the caller). If R is None,
    score = -mean predicted distance over tau and target members (a
    radius-free relative-persistence variant; higher score = closer
    predicted proximity)."""
    cand_arr = np.array(sorted(int(c) for c in candidates))
    tgt_arr = np.array(sorted(int(m) for m in target_members))
    if len(cand_arr) == 0 or len(tgt_arr) == 0:
        return {int(c): 0.0 for c in cand_arr}
    uv = C.UV4
    taus = np.arange(1, window + 1)[:, None, None]           # (window,1,1)
    r_cand_future = r_t[cand_arr][None, :, :] + taus * v * uv[z_t[cand_arr]][None, :, :]   # (window,Ncand,2)
    r_tgt_future = r_t[tgt_arr][None, :, :] + taus * v * uv[z_t[tgt_arr]][None, :, :]       # (window,Ntgt,2)
    delta = C.torus_delta(r_cand_future[:, :, None, :], r_tgt_future[:, None, :, :], L)     # (window,Ncand,Ntgt,2)
    dist = np.sqrt((delta ** 2).sum(-1))                                                     # (window,Ncand,Ntgt)
    if R is not None:
        score = (dist <= R).sum(axis=(0, 2)).astype(float)
    else:
        score = -dist.mean(axis=(0, 2))
    return {int(cand_arr[i]): float(score[i]) for i in range(len(cand_arr))}
```

## Frozen variant selected for Stage 6.12C

**Only the physics-assisted variant, `R=mf.R` (`R_PRIMARY=0.9`), is used.**
The `R=None` radius-free fallback is EXPLICITLY NOT used anywhere in Stage
6.12C — Stage 6.12B's own analysis (`CONTACT_PREDICTOR_ANALYSIS.md`) found
it performs much worse (overall ρ≈-0.08 vs +0.23 for the physics-assisted
variant), and the reconnaissance that scoped this task confirmed this
conclusion should be trusted rather than re-derived. Every reference to
"the kinematic predictor," "C_hat_kin," or "the frozen predictor" in Stage
6.12C's documents means this `R=mf.R` call, never the fallback.

## Frozen constants and call convention for Stage 6.12C

- `R = mf.R = R_PRIMARY = 0.9` (true interaction radius, physics-assisted).
- `v = mf.v = V_PRIMARY = 0.28` (known constant bird speed).
- `L = mf.L = L_BOX = 24.0` (torus size).
- `window = d = 8` for the K=1 primary and K=2 secondary predictor scores
  (matches the primary d=8 forcing horizon — the predictor's own horizon
  parameter is set equal to the forcing duration it is meant to inform,
  exactly as in Stage 6.12B).
- Motion model: straight-line, constant-velocity extrapolation along the
  candidate's/target member's CURRENT discrete cardinal heading (`z_t`),
  using `UV4` unit vectors — no re-planning, no acceleration, no social
  interaction terms. This is a deliberately simple, deployable
  approximation, not a re-simulation.
- Aggregation over a set S (used for the K=2 pair-ranking rule): `C_hat_S =
  sum_{j in S} C_hat_j`, i.e. plain summation of individual scores — the
  same rule Stage 6.12B froze and used (`CONTACT_PREDICTOR_ANALYSIS.md`
  header). No interaction/overlap discount between candidates in a set.
- Target membership (`target_members`): the material-trace-accepted
  membership at t0 (`state["interior0"]`), identical convention to Stage
  6.12B.
- Candidate pool: the primary position-only nearest-20 exterior pool
  (`pool20`, frozen at world-qualification time), never the physics-assisted
  oracle pool.

## What was NOT changed and will NOT be changed after seeing confirmatory data

Formula, weights, horizon-vs-d coupling, interaction radius, motion
assumption (straight-line constant-velocity along current heading), and
set-aggregation rule (plain sum) are frozen as of this document, written
before `run_confirmatory_612c.py` was executed on the 10 confirmatory
states. If any bug or degenerate behavior in this predictor is discovered
while running Stage 6.12C, the finding is documented and the run is
stopped for review — the predictor itself is not silently patched and
re-run on the same states.

## Confirmatory status

`run_confirmatory_612c.py` (a long background job, ~5h estimated) was
launched before this specific document was typed to disk, but the
predictor CODE it calls (`kinematic_contact_scores`, quoted above) was
never modified, viewed-and-tuned, or touched after any Stage 6.12C outcome
existed — it is byte-identical to the pre-existing, already-hashed Stage
6.12B implementation and was never edited by this task. No Stage 6.12C
confirmatory result (candidate ranking, ΔJ, correlation, or L_pred) had
been read or analyzed at the time this freeze document was written; only
a 1-state pilot (disjoint seed range 63000-63099, excluded from
inference) had been inspected, to benchmark runtime per the process
brief — pilot results were not used to alter this predictor in any way.
