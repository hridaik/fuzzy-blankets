# SHAPES.md — gate V1 (alpha = 0, gamma = 0, rho clamped)

Labels: ESTABLISHED / PROVISIONAL / NOT DONE. Code `code/v1.py`, `template4.py`; data `data/v1_complete_th{30,20}.json`, `v1_durable_th{30,20}.json`, `v1_sweep_th{30,20}.json`. Median-coupling dish (g = 0.49; irrelevant when ρ is clamped). Clamped runs freeze l (dl = 0) and use ρ_i = const in the structure. Seeded starts are built in the template of the clamped side (ρ ≥ ½ → a).

## Result: θ = 30° FAILS the completion test (14/16 at each clamp); declared fallback θ = 20° PASSES. θ = 20° is adopted for everything downstream.
| | θ = 30° | θ = 20° |
|---|---|---|
| ρ = 1, 16 seeded starts complete (orbit belief ≥ 0.9, 600 tu) | **14/16** (seeds 5, 12 fail: 2 components / belief 0.84) | **16/16**, min belief 0.961 |
| ρ = 0, 16 seeded starts complete | **14/16** (seeds 5, 12 fail) | **16/16**, min belief 0.954 |
| tail angle at ρ = 1 (complete starts) | +31.91° (sd 0.0) | +21.67° mean over 16 (range 21.4–23.7) |
| tail angle at ρ = 0 | −31.91° | −21.38° in 15/16; **one start (seed 5) is −7.38°** (see below) |
| durability, 5 seeds × 5,000 tu with structural noise, ρ = 1 | 1 component always, fill complete, min belief 0.914, min neighbour Jaccard 0.956; angle 32.08 ± 1.19° | 1 component, fill complete, min belief 0.972, min Jaccard 0.948; angle 21.48 ± 1.15° |
| durability ρ = 0 | min belief 0.909, min Jaccard 0.953; −32.13 ± 1.17° | min belief 0.970, min Jaccard 0.938; −21.56 ± 1.12° |
| 11-value sweep, tail angle vs ρ (start on the clamped side) | −31.91, −25.28, −18.73, −12.48, −6.32, 0, 6.32, 12.48, 18.73, 25.28, 31.91 — **monotone** | −21.38, −17.03, −12.80, −8.64, −4.37, 0, 4.37, 8.64, 12.80, 17.03, 21.38 — **monotone** |
The curve is odd in ρ − ½ and close to linear in (2ρ − 1) (θ = 20°: ρ = 0.9 → 17.03° vs 0.8 × 21.38 = 17.10° linear), as expected from the quadratic structure of E: the ρ-weighted minimum sits at the ρ-weighted target field. Tail angle at ρ = ½ is 0 (to 1e-11): the straight tail. **No hysteresis at θ = 20°**: starting from the opposite side's template (e.g. an a-body at ρ ≤ 0.4) converges to the same angles and is complete at all 11 values (belief ≥ 0.98). At θ = 30° wrong-side starts at ρ ≤ 0.2 end incomplete/defective (`start = a` rows of the θ=30 json), another symptom of why 30° was rejected.
## ORGANISM INTACT bookkeeping and two caveats
* **Completeness is orbit-aware** (v3 definition: mirror-twin places with energy gap < ln 9/4 are one orbit). A strict "every place exactly once by argmax q" cannot be used literally: in healthy noisy bodies the strict test fails in 64–69 % of 1-tu frames (4 runs × 3,000 tu, `code/t_strict.py`) because twin places have near-equal beliefs, while the orbit-aware test fails in 0/12,000 frames. ESTABLISHED.
* **Seed 5 at ρ = 0, θ = 20° is orbit-complete but mis-shaped** (tail angle −7.4° instead of −21.4°, stationary to 6,000 tu): the tail twin places 20/21 are exchanged and the cell at place 21 is doubly claimed (place 20 empty by strict argmax). The orbit-aware completion test and the neighbour Jaccard do not flag it. By the literal gate wording (complete = orbit belief ≥ 0.9) V1 passes 16/16; by shape (angle within 20 % of the settled angle) the count is 16/16 at ρ = 1 and 15/16 at ρ = 0. This is a seeded-start defect of the local minimum, not seen in settled bodies (38/38 healthy settled adults pass the strict test, `t_strict.py`). PROVISIONAL: its frequency from natural starts is unknown.
* Neighbour Jaccard is insensitive to the tail rotation at a 1.6 link radius (a 20° swing changes almost no neighbour pairs): the intact criterion (iv) therefore detects tearing, not shape change.
