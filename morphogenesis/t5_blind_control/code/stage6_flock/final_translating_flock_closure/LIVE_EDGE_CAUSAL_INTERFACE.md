# Closure B — True FOV-Gated Directed Causal Interface

## Question

Does the simulator's actual directed live-interaction structure
(`live_edges`) explain intervention effect better than the geometric
proximity metric (`mech_cumulative_contact_edges`) used throughout Stage
6.12/6.12B/6.12C — which `CONTACT_METRIC_AUDIT.md` established is
undirected and field-of-view-free?

Uses the SAME Closure-A rollouts (no separate campaign), per the task
spec.

## `live_edges` semantics (verified from source, not re-derived)

`stage6_9_translating_collective/code/moving_flock.py:92-101` (inherited
unmodified by `MovingFlock611`):

```python
def live_edges(self, r, z):
    d = self.displacements(r)           # d[i,j] = r_j - r_i, torus minimum image
    D = np.sqrt((d ** 2).sum(-1))
    near = D <= self.R
    vis = (d * UV4[z][:, None, :]).sum(-1) >= 0.0   # receiver's OWN forward half-plane
    recv, src = np.nonzero(near & vis)
    return recv, src, d[recv, src]
```

An edge `src -> recv` means bird `src` is a live source of influence into
bird `recv`'s next-heading computation: `D(src,recv) <= R` AND `src` lies
in `recv`'s own forward half-plane (`(r_src - r_recv)·heading_recv >= 0`).
Directed and asymmetric — `recv`'s visibility of `src` does NOT imply the
reverse. This is materially different from `mech_cumulative_contact_edges`
(`D<=R` only, undirected, no FOV term), which is what every prior stage's
"contact" analyses actually tested.

## Persisted diagnostics (per rollout, all 8 forcing steps)

Recorded in `data/closureAB_rollouts.json` for every actuator: cumulative
actuator→target live edges, cumulative target→actuator reverse edges,
per-step reciprocity, number of unique target members directly
influenced, duration/fraction of forcing steps with ≥1 live edge into the
target, plus the old geometric `mech_cumulative_contact_edges` and
`mech_direct_contacts_t0` for direct comparison — see
`code/live_edge_utils.py::per_step_live_diagnostics`.

## Minimal temporal reachability

`code/live_edge_utils.py::temporal_reachability`: starting at the
actuator at forcing onset, using the REALIZED forced trajectory's own
directed `live_edges` at each of the first 3 forcing steps (one hop
allowed per real simulator step — information cannot travel faster than
the simulator's own update), computes the number/fraction of target
members reachable within ≤1, ≤2, ≤3 temporal hops. Not used to select
actuators; diagnostic only.

## Results

### Q1: Does class C (live exterior parent) outperform class D (near exterior non-parent)?

**No.** Mean diff (C−D) = +0.0031, 90% state-clustered CI [−0.0097,
+0.0160] (n=3 co-occurring states), spans zero. Per-state diffs are mixed
sign: `+0.0263, −0.0122, −0.0047`. This is the same result reported in
`ORGANIZATIONAL_ROLE_RESULTS.md`'s `live_parent_vs_near_nonparent`
comparison (identical computation).

### Q2: Does directed live access relate more strongly to ΔJ than geometric contact?

**No — the two are statistically indistinguishable, and both are weak.**
Per-state Spearman ρ between each candidate feature and
`ΔJ_conservative` (8 states, all candidate actuators in that state):

| feature | mean ρ across states | 90% CI |
|---|---|---|
| geometric contact (mech_cumulative_contact_edges) | −0.107 | [−0.302, +0.096] |
| live directed access (cumulative actuator→target live edges) | −0.118 | [−0.270, +0.036] |
| temporal reachability (≤3-hop fraction) | −0.090 | [−0.293, +0.115] |

All three CIs span zero and overlap heavily with each other; the point
estimates are all small and, if anything, slightly negative (more contact
of any kind very weakly associated with WORSE outcome, not better — not
interpreted as a real effect given the CI width). Per-state correlations
themselves swing from strongly negative (−0.60 at `sclosure_02`) to
strongly positive (+0.52 at `sclosure_07`), i.e. there is no consistent
association of either sign at the state level for any of the three
features. Directed live access does NOT show a consistently stronger
(or even a discernibly different) relationship with intervention effect
than plain geometric contact in this sample.

### Q3: Do multi-hop temporal paths explain high-effect exterior interventions that lack direct live access?

**No.** The ≤3-hop temporal-reachability association (mean ρ −0.090, CI
[−0.293, +0.115]) is no stronger, and no more consistent in sign, than
either single-step measure above. Multi-hop relay access does not explain
additional variance in intervention effect beyond what geometric contact
or direct live access already fail to explain.

## Distance-match diagnostic (class C vs D)

Class C (live exterior parent) candidates are, by construction (they must
be within `R=0.9` AND the target's own FOV to register a live edge at
all), much closer to the target than class D: mean nearest-target
distance 0.274 (class C, n=20) vs 2.251 (class D, n=96) — an
almost-9x difference. This residual mismatch is expected and disclosed
rather than propensity-matched (per the task spec's explicit instruction
not to attempt complicated matching); it means Q1's null result is, if
anything, a CONSERVATIVE test in class C's favor — class C actuators are
much closer to the target on average and still show no advantage over the
more-distant class D.

## Interpretation

Per the task spec, these are the only three questions asked of this
closure; no further feature mining was performed. See
`ORGANIZATIONAL_ROLE_RESULTS.md` for the class-level effect-size
comparison this section's Q1 draws on, and `figures/
closureB_geometric_vs_directed.png` for the visual summary.
