# ENGINE_SPEC_V2.md — testbed v2 generative model (categorical place identity + collective handedness memory)

Code: `code/engine2.py` (model, JAX float64 CPU), `code/an2.py` (shape/orbit analysis), `code/world2.py` (events), `code/interface2.py` (experimenter interface), `code/g2cfg.py` (declared constants). Labels: ESTABLISHED / PROVISIONAL / NOT DONE.

## 1. Model as implemented (the task specification, verbatim in structure)
Cells i, places k = 1..24, handedness h ∈ {L,R}. Template: place positions X*_k and L codes from v1's chiral body (`templates.make_body('chiral')`); mirror map m(k) = place at (x,−y) (bijection and involution, asserted in `make_template2`); C*_k(R) = C*_{m(k)}(L); memory codes D*(L) = (1,0), D*(R) = (0,1); w_k = Σ_j exp(−κ_m|X*_k − X*_j|); Λ*_k(h) = Σ_j C*_j(h) exp(−κ|X*_k − X*_j|); Ψ*_k(h) = w_k D*(h). κ = κ_m = 1.
State per cell: x (2), c (4), d (2), μ (24), l (1). q = softmax(μ), ρ = sigmoid(l).
Sensations (sums over ALIVE j, self term with kernel 1; v1's pipette/bath terms and the exogenous `ext` are added to the kernel sums and multiplied by (1+receptor gain)): s^c = c_i, s^d = d_i, s^λ, s^ψ.
E_ik(h) = ½[π_c|s^c − C*_k(h)|² + π_λ|s^λ − Λ*_k(h)|² + π_d|s^d − D*(h)|² + π_ψ|s^ψ − Ψ*_k(h)|²].
Dynamics (Itô): (1) dμ = −k_μ[(μ + β_E Ē) − mean_k(μ + β_E Ē)]dt + σ_μ dW (noise projected on the zero-mean subspace: only centred logits matter; this changes nothing about q); (2) dl = [−2r sinh l + k_h β_E Δ]dt + σ_h dW; (3) dx, dc, dd = −k_a ∂A_i/∂(x_i, c_i, d_i) dt + σ dW, with A_i = Σ_h P(h) Σ_k q_ik E_ik(h) taken with q and ρ held fixed and with the other cells' states held fixed (own-variable, own-sensation restriction, `jax.grad`, as in v1).
Integrator: RK4 drift + Euler–Maruyama additive noise, counter-based per-cell noise streams indexed by (key, absolute step, cell) (v1's CRN scheme, vector extended to 2+4+2+24+1 components). Developmental factor τ: hook present (`Params2.tau`), unused (adult).
Control inputs (extension of v1's): `ext` (6 ligands, the last two are the memory ligands), receptor gain `rg` (6), migration gain `mig`, fate-bias drive `fb` (on μ; available, not used), pipette sources, bath, alive mask, raised-cosine ramps (`run_ctl`).

## 2. Declared constants
π_c = π_λ = e² was the starting point; **chosen G1 operating point: β_E = 4, k_μ = 0.2, π_c = e, π_λ = e³** (ratio knob; see CATEGORICAL.md). k_a = 0.4, κ = κ_m = 1. Noise σ_x = σ_c = σ_d = σ_μ = 0.02, σ_h = 1.0 (chosen in G2). dt = 0.0125 (spectral radius of the Jacobian ≈ 96 at the G1 point, dt·ρ = 1.2 < 1.5).
Memory parameters (chosen after the isolated-cell diagnosis, MEMORY.md): π_d = 0.01, π_ψ = 0.04, r = 0.10, k_h = 0.1. First choice from the spec's design rule (π_d = 0.02, π_ψ = 0.10, r = 0.05) failed G2(b).

## 3. Deviations and additions (declared)
* **Orbit definitions.** "Orbit" belief needs a definition because mirror-twin places are nearly indistinguishable: at the exact template state the energy gap between twin places is 0.002–0.37 for the head/tail pairs. G1: a mirror pair is one orbit when both symmetric gaps are < ln9/β_max = 0.55 (at the chosen π). G2+: every mirror pair whose codes are identical in both forms (non-body-row places) is one orbit, because at ρ = ½ the form swap maps the pair onto itself. Body-row places are always singletons.
* **Isolated-cell gain.** The spec's G₁ = k_hβ(π_d + π_ψ) assumes w = 1. A cell that believes it holds place k expects Ψ* = w_k D* (w_k ∈ [2.6, 4.9]) but senses only its own secretion; its d_i settles at the amplified level a = (π_d + π_ψ w_k)/(π_d + π_ψ) and its effective gain is G_iso(k) = k_hβ(π_d + π_ψ w_k)²/(π_d + π_ψ) (MEMORY.md; verified).
* Noise on μ is projected on zero-mean (above).
* `fix_rho` option freezes handedness (G0/G1). `psi_scale` multiplies π_ψ (G2d).

## 4. Tests
`tests/test_v2.py` (G0 + CRN + sham + events), plus v1's tests copied in `tests/` (v1 tests are not modified).
