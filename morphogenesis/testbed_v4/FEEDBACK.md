# FEEDBACK.md — gate V2 (coupled memory, body-feedback dial; median dish κ_g = 2.449, g = 0.4899, θ = 20°)

Code `code/v2.py`, `theory4.py`; data `data/v2_theory.json`, `v2_lstar.json`, `v2_bath.json`, `v2_dur.json`, `v2_isolated.json`. Labels ESTABLISHED / PROVISIONAL / NOT DONE.

## (a) Calibration (computed from the templates)
θ = 20°: D_k = ½π_λ|Λ*_k(a) − Λ*_k(b)|²: nonzero only near the hinge — max **6.304** at places 14, 15 (last body row), 5.46 at 16/17 (first tail row), 3.03 at 10/11, 1.22 at 18/19, 0.93 at 12/13; 0.00–0.3 at the head and the far tail; mean 1.470. α = φ_max g_min/(β_E max D) with g_min = 0.3: **α = 0 / 4.759e-3 / 9.518e-3** for φ_max = 0 / 0.4 (PRIMARY) / 0.8. At the median dish the per-cell φ_k = αβ_E D_k/g has max 0.245 (φ_max 0.4) and 0.49 (0.8) (φ_max itself is reached only at g_min); mean-field φ̄ = αβ_E D̄/g = **0.057 / 0.114**, **g_eff = g(1+φ̄) = 0.4899 / 0.5179 / 0.5459**.
## (b) Two stable states, l* (settled, deterministic, 1,500 tu)
| variant | predicted 2 arccosh√(g_eff/4r) | measured mean l (a; b is the mirror) | spread over cells (sd; min–max) |
|---|---|---|---|
| φ0 | 2.0370 | **2.0365** | 1e−4; 2.036–2.037 |
| φ0.4 | 2.1085 | **2.1049** (0.2 %) | 0.079; 2.043–2.277 |
| φ0.8 | 2.1752 | **2.1634** (0.5 %) | 0.148; 2.048–2.482 |
Both states are stable in all variants (durability below). The mean-field value uses the mean D; the spread is the feedback's heterogeneity: cells at the hinge (large D_k) sit at larger l (up to 2.48), head/tail cells at the φ0 value. ESTABLISHED.
## (c) Bath sweep (quasi-static, 80 tu per step, 0 → +1.2 → 0 → −1.2 → 0 from state a; B ligand-B bath) vs the 1-D prediction dl/dt = −2r sinh l + g(2f − 1) + αβ_E D̄ tanh(l/2), f = Wρ/(W+B), W = mean 2.859
| variant | predicted B_c | measured up-jump (between) | return to B = 0 | negative-side jump |
|---|---|---|---|---|
| φ0 | 0.513 | 0.500–0.525 | stays switched (ρ̄ = 0.115) | −0.500…−0.525, back to ρ̄ = 0.885 |
| φ0.4 | 0.589 | 0.575–0.600 | stays switched (0.109) | −0.575…−0.600 |
| φ0.8 | 0.670 | 0.625–0.650 (4 % below) | stays switched (0.104) | −0.625…−0.650 |
Hysteresis loop in all three; the critical bath rises with φ (0.513 → 0.589 → 0.670), as predicted. **No variant is locked**: the prediction says a bath can switch whenever φ̄ < 1 (the large-B drive is −g + c·tanh(l/2), negative while c < g); here φ̄ ≤ 0.114 and even the largest per-cell φ_k ≤ 0.49, so the lock condition (φ ≥ 1) is never approached. The lock itself is NOT DONE (it would need φ_max ≈ 4–9, outside the declared variants).
## (d) Durability, 10 seeds × 10,000 tu per state per variant (σ_h = 0.4, structural noise 0.02)
**0 spontaneous switches in 60 runs** (600,000 body-tu). mean ρ stays within 0.771–0.912 (a) / 0.089–0.228 (b); one component and complete (orbit) fill in every 10-tu frame; min belief 0.976; min mean neighbour Jaccard 0.936–0.947; mean tail angle ±15.0 / ±16.1 / ±16.9° for φ = 0 / 0.4 / 0.8 (sd 1.3° — noise lowers the mean angle below the deterministic ±16.4/±17.1: ⟨2ρ−1⟩ is smaller under σ_h). ORGANISM INTACT pieces (ii)–(iv) hold throughout (τ_J applied post hoc: min Jaccard ≥ 0.936 vs τ_J = 0.9332). ESTABLISHED.
## (e) Isolated cell (single alive cell, N = 1, l(0) = 0.4)
φ0: forgetting rate **0.1000** (2r = 0.1), l∞ = 8e−10. **For α > 0 the prediction "2r, unaffected by α up to a tiny self-field term" FAILS**: the rate is **0.162 (φ_max 0.4)** and **0.330 (0.8)** and the cell is driven to a **biased fixed point l∞ = −1.37 / −2.11**. Cause (checked from the formula, PROVISIONAL numerically): a lone cell senses only its own code, so its field s^λ is far from the template; Δ_i = Σ q(E_b − E_a) = π_λ(Λ_a−Λ_b)·(s^λ − ½(Λ_a+Λ_b)) is then a large, l-independent constant, and αβ_E Δ_i is not small (an isolated cell is an extreme case: bodies and fragments with ≥ 1 neighbour keep s^λ near the template). Consequence: a cell that is extruded far from the body and an isolated cell carry a state decided by their own misfit, not by 2r forgetting (V6 extrusion reports what happens at 8 units).
