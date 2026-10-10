# SWITCH.md — Gate G3 (white-box light-gated memory secretion; L ↔ R)

Labels: ESTABLISHED / PROVISIONAL / NOT DONE. Code `code/g3.py`, `code/diag.py`; data `data/g3_scan.json` (93 scan jobs, 560 trials), `data/g3_probe*.json`, `data/diag.log`.

## **GATE G3: FAILED. No switch in any direction, centre, duration or amplitude tried.** G5 (datasets, blind package v2) was therefore NOT built, as the specification requires.

## Protocol (as specified)
Actuator: raised-cosine ramps (ramp 5); in the lit cells, add u(t) to the opposing memory ligand's secretion (L→R: mR; R→L: mL) as exogenous source in the kernel sums (`ext`). Pattern: lit set = cells whose *place* lies within 1.5 of the centre place in the body frame (the `Mask(('place',k,r))` form in `interface2.py` gives the same pattern tracked in the arena; the batch used the body-frame set directly), all 24 centres + whole body. Durations 10, 40, 160; release 500 tu after the 200 tu tail (shortened from 2,000 because no trial left the original form; the one extended probe below was run to 2,000 tu). Amplitude ladder 0.5, 1, 2, 4, …, 128 (geometric; stop when displacement > 20); bisection (5 steps) was to be run between the last non-switch and the first switch — never triggered. Deterministic; sham twin = same code path, amplitude 0 (bit-identical to the unforced twin).
Direction L→R: all 24 centres + whole body × 3 durations. Direction R→L: centres 8, 12, 4, 0, 22 + whole body × 3 durations (mirror-symmetric model; results identical to L→R for the whole body).
Switch criterion (declared): end form = other, complete (orbit-complete, one component), mean ρ on the other side of ½, persists through release; moveless = max displacement vs sham < 0.3.

## Results
* **Switches: 0 / 93 scans, 0 / 560 trials. Body-row type flips: 0. Trials ending in an R-labelled body (from L): 0.** Whenever the body survives the pulse it relaxes back to the starting form with the starting ρ.
* Movement: the memory light moves cells (the ψ term gives a position force ∝ π_ψ·u). First amplitude with displacement ≥ 0.3 vs sham: 10 tu: 2–4 (median 4); 40 tu: 1–4 (median 2); 160 tu: 1–4 (median 2). Body torn (displacement > 20, cells escape, no restoring force at range): first at u = 8–32 (typically 16). So **the movement-free window is u ≤ 1–2 and nothing flips inside it.**
* Mean ρ crossed ½ in 12 trials, all with the body torn.
* Matched-dose wrong-location and sham controls: sham is bit-identical to the twin; wrong-location pulses behave like on-target ones (no effect below movement, tearing above) — location dependence is not resolvable because there is no switch to measure. Lag "memory leads morphology": NOT MEASURABLE (no body-row type flip occurs).
* Not run (because there is no switch): minimal dose table per centre, best/median ratio, noise-robustness at 1.2× threshold, comparison with w_k.

## Mechanism (diag.py, whole-body illumination, u = 8 on mR, 160 tu — a dose that already displaces cells by 5)
Per-cell minimum ρ during the pulse versus the cell's morphological gain G_morph (data/diag.log):
| G_morph | places | ρ before | min ρ during |
|---|---|---|---|
| 0 – 0.4 | 0, 2, 22, 23, 20, 21, 18, 19, 1, 3 | 0.50–0.54 | **0.08 – 0.15** (memory rewrites the handedness belief) |
| 1.24 | 5, 6, 16, 17 | 0.93 | 0.05 (flipped) |
| **4.0 – 24.2** | 7, 4, 8–11, 12–15 (the 8 body-row cells and the cells next to them) | 0.98–1.00 | **0.97 – 1.00 (never moves)** |
So the memory ligand does switch the *handedness belief* of the 14–18 cells that have no morphological evidence for it, but the cells that carry the body-row types are held by their own secreted types (Δ_morph = ½(2ρ−1)(π_c|ΔC|² + π_λ|ΔΛ|²), gain up to 24), and the memory-evidence available per unit of dose is k_hβπ_ψ w u ≈ 0.4 × 0.04 × 3.5 ≈ 0.06 u ≪ 24 for u that the body tolerates. Scaling the constants does not help: raising k_h (probe VB: k_h = 2, π_ψ = 0.002, same G₁, G) scales the morphological gain by the same factor k_hβ, and the position force per unit of memory evidence is fixed by k_a/(k_hβ w): the dose needed to flip a body-row cell versus the dose that tears the body is set by the ratio of π_ψ-terms to (π_c, π_λ)-terms and not by the knobs in the declared ranges. The VB probe (k_h = 2, π_ψ = 0.002) returned NaNs in its first trial (cause not investigated; the morphological gain would be ≈ 480, so numerical stiffness at dt = 0.0125 is the likely reason) and was abandoned; so the scaling argument is NOT a tested negative, only mean-field reasoning (PROVISIONAL).
## What would be needed (not done): a weaker morphological restoring force in the 8 body-row cells (smaller π_c, π_λ with larger β — outside the range), or an actuator that acts on the cells' own l (fate-bias), which is not the specified light.
