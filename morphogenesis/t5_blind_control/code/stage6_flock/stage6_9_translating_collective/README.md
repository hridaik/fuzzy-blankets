# Stage 6.9 — translating-collective pilot

Additive continuation of `stage6_flock/`. **Nothing in Stages 6–6.8 is
modified, re-run or restated by this stage.** Stage 6.8's inference modules
(`louvain.py`, `probing.py`, `predictive_boundary_68.py`, `observer.py`) are
imported read-only.

## The question

> **Can a collective retain functional identity in a translating frame while
> its material membership changes?**

This is tested, not assumed — **and at this model's specified interaction scale
the answer is no**: the feasibility gate fails 0/40 and the stage stops before
any steering experiment. See `RESULTS_6_9.md`.

The interesting regime would have been the conjunction
`R_M` decreasing substantially **while** `R_F` stays high — the physical bird
identities are replaced but the spatially organized collective persists in its
own moving frame. Groups that translate while keeping their members
(`R_M ≈ 1`) are reported as **moving material identity**, and the
constituent-replacement result is not claimed for them.

## What was and was not added

**Kept unchanged:** the discrete four-state headings, the active-inference
heading update (the same precomputed tables, the same policy posterior, the
same two draws per bird per step), the Stage 6.8 FOV rule, and β/ρ/ω at their
frozen Stage 6–6.8 values.

**Added:** continuous positions on a periodic torus, partners within a radius
`R`, and `r_i(t+1) = r_i(t) + v·d_i(t+1) (mod L)`.

**Not added:** no attraction, repulsion, centering or collision term was
invented, and no traveling wave was manufactured on the lattice. The model's
existing collision-avoidance physics (`flock_sim.model.SLOT_OVERRIDES`) is
reused by assigning each continuous neighbour to the Moore slot whose octant it
falls in — the only new modelling decision in the stage, and it adds **no free
parameter**.

## Reading order

1. `PLAN.md` — scope, written after the Stage 6.8 gate and before any number.
2. `PROTOCOL_6_9.md` — every threshold, with provenance
   (`configs/protocol_6_9.yaml` + `.sha256`).
3. `logs/translation_gate_criteria_predeclared.txt` — the feasibility gate's
   five criteria, frozen before the gate ran.
4. `RESULTS_6_9.md` — what was found.
5. `figures/fig_6_9_G_gate_failure.png` — the gate outcome and its diagnosis.
6. `figures/translating_identity.html` — the three-panel visualization:
   three synchronized panels (world frame · material lineage · co-moving
   frame). Open it directly in a browser; it needs no server. It is a separate
   file rather than a tab in `interactive_demo/`, because that belongs to
   earlier stages and this stage adds files rather than editing them.

## The firewall

Stage 6.8's rule, plus one addition: inference code may not see **the
simulator's true centre trajectory**. The translating frame is estimated from
observed positions and headings — centroid displacement, then cross-correlation
refinement. Enforced by `tests/test_no_topology_leakage_69.py`, which also
asserts that a rigid translation leaves `D_deform < 0.05` while the unaligned
world-frame distance is more than 5× larger, i.e. that removing translation is
doing real work.

## Layout

```
code/     moving_flock (simulator) · identity_69, detect_69 (inference-side)
          intervention_api_69 (black-box probe) · runners · figures · viz export
configs/  protocol_6_9.yaml + sha256
data/     translation_gate, boundary_69, oracle_reveal_69, guidance, viz bundle
figures/  Fig. 6.9-1 .. 6.9-6 (PNG + PDF) and translating_identity.html
logs/     run logs + the gate pre-declaration
tests/    16 tests: firewall, translation-estimation, simulator correctness
```

## Running

```
cd stage6_flock/stage6_9_translating_collective
python -m pytest tests/ -q                 # 16 tests

cd code
python run_translation_gate.py             # the hard gate -- uncontrolled only
                                           # -> FAILS at specification (0/40)
python make_figures_69.py fig_gate fig1 fig2 fig3 fig4
python export_viz_69.py                    # the three-panel visualization

# NOT RUN -- the gate is a hard stop (task brief 33). The scripts exist and are
# specified, but no result from them is reported:
#   run_boundary_69.py, run_oracle_reveal_69.py, run_guidance.py
```

Order matters: no steering experiment may run before the feasibility gate is
evaluated, and `run_oracle_reveal_69.py` reads the frozen boundary results
without modifying them.
