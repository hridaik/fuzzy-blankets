# ENGINE_SPEC_V3.md — structure module (v2 G1 point, h removed) + paracrine ratiometric memory module

Code: `code/engine3.py` (model), `code/an3.py`, `code/world3.py` (events + experimenter interface), `code/theory3.py` (mean-field numbers); v2 code (`testbed_v2/code`: `make_template2`, `an2.classify_shape/orbits`, `shape.py`, `par.py`) is imported read-only. Tests: `tests/test_v3.py`. Labels: ESTABLISHED / PROVISIONAL / NOT DONE.

## Model as implemented
**Structure** (per cell: x, c, μ over the 24 places). Template = v2's chiral body L only (positions X*_k, codes C*_k, expected fields Λ*_k; h-independent). s^c_i = c_i; s^λ_i = Σ_j c_j e^{−κ|x_i−x_j|} over alive j incl. j = i (+ structural controls). E_ik = ½[π_c|s^c − C*_k|² + π_λ|s^λ − Λ*_k|²], π_c = e, π_λ = e³, β_E = 4, k_μ = 0.2, k_a = 0.4, κ = 1. dμ_ik = −k_μ[(μ_ik + β_E E_ik) − mean_k'(·)] + σ_μ dW (noise projected on zero-mean); dx_i, dc_i = −k_a ∂/∂(x_i,c_i) Σ_k q_ik E_ik (own variables, own sensations, others fixed; `jax.grad`). **The structure drift and noise never read l, d, e or any memory control** (checked by `test_structure_has_no_h…` and the 20-intervention bit-identity test).
**Memory** (per cell: l, d = (dA, dB), e). Paracrine ratiometric sensing over j ≠ i, alive only, w_ij = exp(−κ_m|x_i − x_j|), κ_m = 1:
 f_i = (A_i + ε/2)/(A_i + B_i + ε), A_i = Σ_j w_ij(dA_j + uA_j) + P_A(x_i) + B_A, B_i likewise with dB, uB, P_B, B_B; ε = 10⁻³; u = light-induced secretion of lit cells; P = memory pipettes (kernel-weighted point sources); B = memory bath. An isolated cell gets f = ½.
 dl = [−2r sinh l + g(2f − 1)]dt + σ_h dW, g = k_hπ_ψ/2 (β_E not applied); ρ = σ(l) = P(state a).
 dd_A = k_d(ρ − d_A)dt + σ_d dW, dd_B = k_d((1 − ρ) − d_B)dt + σ_d dW, k_d = 0.4 (secreted levels drive only the neighbours' sensing; they never enter the structure).
 Reporter: e* = ρ Σ_{k∈S+} q_ik + (1 − ρ) Σ_{k∈S−} q_ik; S± = the 4 body-row places with y ≷ 0; de = k_e(e* − e)dt + σ_e dW, k_e = 0.4. Pure readout, sensed by no cell. State a lights the +y body row (limb side), state b the −y row.
Declared parameters: r = 0.05, g = 0.6 (g/4r = 3), σ_h = 0.4 (H2 pilot), σ_d = σ_e = 0.02, structural noise σ_x = σ_c = σ_μ = 0.02. dt = 0.0125 (RK4 drift + Euler–Maruyama, v1/v2 scheme); Jacobian spectral radius ≈ 96.
Control inputs: structural secretion `ext`, receptor gain `rg`, migration `mig`, structural pipettes/bath (v2 semantics), **memory light** `uM (n,2)`, memory pipettes/bath, alive mask; raised-cosine ramps (`run_ctl`); l kicks as instantaneous state edits (World3). Memory-light ramps are `min(5, dur/4)` in H3 (declared).
Noise: per-cell counter-based streams indexed by (key, absolute step, cell); one normal vector per cell with separate slots for x (2), c (4), μ (24), l, d_A, d_B, e — memory noise never shifts the structural stream (T4 under noise).
Variants: `freeze_structure` (diagnostic, unused in reported results); `place_self_attenuation` (H4b: perception uses only the paracrine part of s^λ and π_c = 0; action unchanged).

## Declared deviations / choices
* **Sham and twin runs use the full-signature control tuple.** With a shorter tuple jax traces a different program and XLA constant-folding changes structural rounding by ~1e−16; bit-identity needs the identical traced program (`zero_ctl` returns the full 11-tuple).
* Orbit definition for place completeness is v2's G1 definition (mirror twins with energy gap < ln9/β_max = 0.55 at the chosen π are one orbit; `an2.orbits`).
* Reporter scoring in H3 (second half of release) — see SWITCH_V3.md.
