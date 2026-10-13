# DAMAGE.md — gate V4 (light damage: γ_0 calibration and the safe window)

Labels ESTABLISHED / PROVISIONAL / NOT DONE. Code `code/v4.py`, `v4cal.py`, `v4run.py`; data `data/v4_gamma_grid.json`, `v4_gamma_verify.json`, `v4_window.json`, `gamma0.json`. Primary variant (φ_max 0.4, α = 4.759e-3), median dish (κ_g 2.449, g 0.4899, γ factor 1).

## Mechanism (ENGINE_SPEC_V4.md §4)
π_c,i, π_λ,i ← × exp(−γ ū_i), dū_i/dt = (u_i − ū_i)/10, u_i = amplitude of the light covering cell i. A lit cell's restoring force and its place-evidence both shrink; its place logits μ relax toward uniform, and when the light ends and ū decays (τ_rec = 10) it re-selects a place from a field that the shape change has also altered.
## Definitions (frozen before measuring)
Damage trial: noisy (σ_h 0.4, structure 0.02), 100 tu burn-in, memory-secretion light (a→b) on a disc, followed by 300 tu; FAIL = ORGANISM INTACT fails at any 1-tu frame from light-on to 300 tu after light-off (one component; orbit-complete fill; mean Jaccard ≥ τ_J = 0.9332; no cell lost). **Damage onset u_d** = smallest amplitude with ≥ 5 failures in 10 CRN seeds (sequential early stop at 5 failures / 6 survivors; geometric bracket factor 1.4 then bisection to 6 % in amplitude). Mode at the first failing frame: *extrusion* (a singleton component), *split* (>1 components, none a singleton), *wrong place* (connected, fill incomplete), *drift* (connected and complete, Jaccard below τ_J only).
## γ_0 calibration
Target: u_d = 2.5 × the switch-threshold amplitude of the same condition (middle disc, 16/g = 32.7 tu; threshold 1.1875 under the frozen scoring) = **2.969**.
Damage depends on γ and u only through γū (exp(−γū) enters nothing else except Δ at second order), so u_d ∝ 1/γ. Measured on a γ grid with the exact onset search:
| γ | 0.5 | 1 | 1.5 | 2 | 3 | 4 | 6 | 9 |
|---|---|---|---|---|---|---|---|---|
| u_d | 7.355 | 3.677 | 2.557 | 1.839 | 1.226 | 0.919 | 0.588 | 0.392 |
| χ = γ u_d | 3.677 | 3.677 | 3.835 | 3.677 | 3.677 | 3.677 | 3.526 | 3.526 |

χ = 3.53–3.84 (mean 3.66; spread ±4 %, i.e. within the 6 % search tolerance plus noise): the scaling is exact to that level. Onset is sharp: at onset 5/5 seeds fail, one step (≈ 10 %) below 0/6.
γ_0 = χ/2.969 → **γ_0 = 1.239** (`data/gamma0.json`). Direct verification at γ_0: u_d = **3.025** (bracket 2.90 survives (2/8 fail) … 3.025 fails 5/5) vs target 2.969: **+1.9 %**, inside the 6 % tolerance. ESTABLISHED. (Per-dish γ = γ_0 × the dish factor ∈ [1/1.5, 1.5].)
## Safe window at the median dish (a→b, primary variant, discs r = 1.5)
Switch threshold amplitude (frozen scoring), damage-onset amplitude, ratio u_d/threshold; "safe window" = amplitudes in [threshold, u_d).
| disc | duration | lit cells | threshold | damage onset u_d | u_d / threshold | window? | modes at 1.5 × u_d (10 seeds; fail fraction) |
|---|---|---|---|---|---|---|---|
| middle | 4/g = 8.2 tu | 6 | 7.62 | 18.3 | 2.40 | yes | {'wrong_place': 9, 'drift': 1} (1.0) |
| middle | 8/g = 16.3 tu | 6 | 2.5 | 7.4 | 2.96 | yes | {'wrong_place': 10} (1.0) |
| middle | 16/g = 32.7 tu | 6 | 1.19 | 3.1 | 2.61 | yes | {'wrong_place': 10} (1.0) |
| middle | 32/g = 65.3 tu | 6 | 0.812 | 2.12 | 2.61 | yes | {'wrong_place': 10} (1.0) |
| tail_end | 4/g = 8.2 tu | 4 | 104 | 30.4 | 0.29 | **no** | {'wrong_place': 7, 'drift': 3} (1.0) |
| tail_end | 8/g = 16.3 tu | 4 | 28 | 11.5 | 0.41 | **no** | {'wrong_place': 9, 'drift': 1} (1.0) |
| tail_end | 16/g = 32.7 tu | 4 | 10 | 2.58 | 0.26 | **no** | {'drift': 6, 'wrong_place': 4} (1.0) |
| tail_end | 32/g = 65.3 tu | 4 | 4.5 | 1.37 | 0.31 | **no** | {'drift': 6} (0.6) |

**Findings.**
* At the middle disc the window is open at every duration with a ratio 2.4–3.0 (target 2.5 at 16/g by construction; 4/g: 2.4, 8/g: 3.0, 32/g: 2.6). Both thresholds fall with duration (7.6 → 0.81 for the switch, 18 → 2.1 for damage): long gentle pulses and short bright pulses are both safe, a bright pulse at the *same duration but* > u_d is not.
* At the tail-end disc there is **no safe window at the median dish at any duration**: damage sets in at 0.26–0.41 of the amplitude needed to switch. The same pulse that is a clean switch at the middle disc (dose 233) is destructive at the tail tip, because 4 lit cells there must be driven 8–9× harder (their neighbours are mostly dark: low connectivity) so ū, hence the loss of restoring force, is 8–9× larger for the same effect on memory.
* The ratio is non-monotone in duration at the tail end (0.29, 0.41, 0.26, 0.31); the 8/g point is the least bad (28 vs 11.5).
* Damage onset γ-scaling means the whole window moves with γ: the window ratio u_d/threshold at a dish is χ(κ_g, disc, duration)/(γ_0 γ-factor · threshold(κ_g, disc, duration)); it differs between dishes through both factors (V5).
## Damage modes (first failing frame at 1.5 × u_d, 10 seeds per grid point = 80 runs)
Counts over the 8 grid points: {'wrong_place': 59, 'drift': 17} (wrong place 59, drift 17, **extrusion 0, split 0**). Modes among the failing trials of the onset searches: {'wrong_place': 164, 'drift': 98}. The failure is place re-selection of the lit cells (a wrong place by argmax q while the cluster stays connected) and, at the tail end and long durations, a persistent shape deformation (Jaccard below τ_J, fill intact). In no run was a cell lost from the cluster or the cluster split within the 300-tu window: PROVISIONAL explanation: the restoring force returns within ≈ τ_rec = 10 tu of the light ending, before a cell can diffuse out of the 1.6 link radius. NOT DONE: modes beyond 300 tu; other lights (structural secretion, receptor gain, migration) at their own damage onset are only exercised in the data package (u_i is the amplitude of whichever light covers the cell).