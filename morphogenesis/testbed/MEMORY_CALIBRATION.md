# MEMORY_CALIBRATION.md — T2c body-plan memory, properties P1–P6

**Headline: the designed memory does NOT give a durable, switchable bistability in this testbed. P2 fails (plan B is not a stable adult attractor, even as a stand-alone body), so P3–P6 are NOT DONE. Nothing was forced.**
Code: `code/mem.py`, `code/slow.py`, `code/p2_jacobian.py`, `code/explore/` (mem2.py, mem3.py, slow1.py, slow2.py, bias.py, ps*.py), `code/t2b*.py`; data: `data/p2_jacobian.json`, `data/explore_logs/`.

## Implemented design (as specified)
Two plans over the same 24 slots and 4-type alphabet (A: one-headed, B: two-headed, 8 of 24 = 33 % of slots re-coded in colour AND position; TESTBED_SPEC.md); plan logits `zeta_i ∈ R²`; predictions are plan-mixtures `g_i = Σ_z softmax(zeta_i)_z g_i^(z)` (positions OFF, so field/code/memory channels); a **5th signal (memory ligand)**, kernel κ_m (scanned 0.35–3), secreted by each cell at amplitude `a` (scanned 0.25–4) × its plan-B belief (plan A code 0, plan B code a), sensed through the same field kernel; **coupling knob** = precision π_m of the memory field channel (scanned 0–100); weak prior bias toward A `ζ0 = (b, 0)` with precision π_ζ (b = 1; π_ζ scanned 0.001–1; b scanned −3…1).

## Thresholds declared before measuring
P2: both plans stable (no Jacobian eigenvalue with Re > 1e-6), complete (orbit-complete, all types), max orbit belief > 0.95, visibly distinct. P3: hysteresis interval in π_m. P4: switching rate bound. P5: pulse thresholds by bisection. P6: dependence on coupling.

## Results
**P1 Development from default initial beliefs reaches plan A — NOT MET as specified; MET only for the seeded start.** Near-uniform beliefs: 0/50 (T2a). From the declared seeded start body A is reached 49/50 (K = 1 model). In the K = 2 model, A starts stay A (mean w_B 0.02–0.09 over κ_m, a, π_m, π_ζ scanned).

**P2 Both plans stable adult attractors — FAILS.**
* Plan A (stand-alone): stable, complete, orbit belief 0.984, distance to template 0.03 (`p2_jacobian.json`: no unstable mode beyond numerical zero; slowest rates ≈ 1e-4).
* Plan B (stand-alone K = 1 template, same operating point): **not an attractor** — 0/54 seeded draws assemble over log π_s ∈ {2,3,4} × log π_prior ∈ {−6,−8,−10}; 0/24 at k_a = 1.2; Jacobian at its end state has 176 unstable modes (max Re +0.14). An earlier single-seed run (ps4.py, amplitude-2 gradient, k_a = 1.2) looked stable; it did not survive other seeds. The cause is not understood (16 type-1 cells whose fingerprints differ from each other only through weak field differences and the graded channel; PROVISIONAL).
* In the K = 2 mixture model a B start **decays to plan A** (mean w_B 0.93 → 0.03 within ~100–140 time units for κ_m = 0.35, 1.0; π_m 20 or 100; π_ζ = 0.001, i.e. essentially no prior; `explore_logs/mem_mixture_runs.txt`); at κ_m = 2, a = 1 the plan belief stays (0.90) but the body degrades (belief 0.27).

**P3 Bistability region by continuation of the coupling — NOT DONE (no second state to continue).** Slow-manifold scans (freeze beliefs at uniform plan-logit difference s, relax positions and secretions, read d(ζ_B−ζ_A)/dt; `explore_logs/slow_manifold_g.txt`): g(s) < 0 (drift to A) for every s ≲ 4 at every setting, |g| < 1e-3 for s ≥ 5; the first scan at six (κ_m, a, π_m) shows g(0) between −0.28 and −0.39 regardless of π_m ∈ {0, 1, 20, 100}; larger amplitudes (a = 2–4) give erratic positive spikes (up to +2.5), meaning the fast variables do not relax to a unique state there, not a double well. Biasing toward B (b = −3…−1) breaks the body (distance 3–6) rather than creating a second state.
**P4 durability, P5 switchability (white-box minimal pulse), P6 tunable barrier — NOT DONE** (conditional on P2/P3). The disc-pulse machinery exists (`ext` exogenous secretion in the engine; used for T2d and the CRN test) but no A↔B switch exists to bisect. The T2d chiral pulse scan (CHIRALITY.md) is the only switching experiment performed and it is negative.

## Why (PROVISIONAL analysis — consistent with the data, not proven)
1. Linear mixture predictions + self-consistent own actions ⇒ a continuum of near-zero-error mixed-belief states ("neutral mixture manifold"); sharp states are held only by weak nonlinear field mismatch (the same fact that makes assembly fail from near-uniform beliefs).
2. Mean-field memory barrier: with all cells sharing w, the memory-channel error is ∝ w(1−w)(S_A − S_B)(a_A − a_B), where S = kernel sum over the cell's neighbours in each plan's geometry. The plans differ in 8 of 24 slots only, so S_A − S_B is small for most cells and the memory term cannot create a barrier on the shared cells; it acts as diffusive consensus. The barrier would have to come from the recoded cells' type/field mismatch, and plan A is intrinsically favoured (g(0) ≈ −0.3 with the memory off).
3. Plan B has no intrinsic stability of its own at this design.

## What would be needed (OPEN_QUESTIONS.md)
A B that is a stand-alone attractor; a plan-prediction that is nonlinear in belief (not allowed by the specified linear mixture) or a recoded region large enough that S differs for every cell; or a different relation between plan and the memory ligand (e.g. a memory ligand that is *produced by an explicit cell-autonomous bistable switch* and sensed, rather than inferred).
