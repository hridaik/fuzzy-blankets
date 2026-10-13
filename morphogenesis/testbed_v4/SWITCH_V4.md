# SWITCH_V4.md — gate V3 (memory-secretion light switches state AND shape; γ = 0)

Labels ESTABLISHED / PROVISIONAL / NOT DONE. Code `code/v3sw.py` (driver), `lib4.py` (`switch_trial`, `score_switch`, `bisect_switch`), `v3an.py` (analysis); data `data/v3_prelim.json` (τ_J not yet applied; used only for τ_J calibration), `v3_final.json` (frozen scoring), `v3_noise.json`, `v3_analysis.json`.

## Protocol (frozen before scoring; COMPUTE_PLAN.md)
Actuator: light-gated memory secretion u_B (a→b) or u_A (b→a) on lit cells, raised-cosine ramp min(5, dur/4). Lit set = cells whose place lies within 1.5 of a centre point in the undeformed template: **middle** (template centroid, 6 cells), **limb_side** (centroid x, y = +1.5, 5 cells), **head_end** (head tip, 4 cells), **tail_end** (tail tip, 4 cells), **whole** body (24). Names are TRUE (hidden). Durations 4/g and 16/g of the dish's own g; release 20/g after the light; amplitude ladder 0.25·2^k then 5 bisections. γ = 0 here (damage is V4).
**SWITCH** = all of: (1) mean ρ on the other side of ½ throughout the second half of the release; (2) the mean tail angle over the last 1/10 of the release has the sign of, and lies within 20 % of, **the settled tail angle of the target state in that dish** (declared interpretation of "the target template's angle": the nominal ±20° is unreachable by construction because the settled shape is ∝ 2ρ*−1 with ρ* = 0.78–0.94 depending on κ_g); (3) ORGANISM INTACT throughout (one component, orbit-complete fill, mean neighbour Jaccard ≥ τ_J = 0.9332, frozen from natural and clean-switch runs, `data/intact_threshold.json`; no cell lost or added). Dose = threshold amplitude × duration × lit cells.
τ_J: the first calibration (1st percentile of single frames) gave 0.9826 and was **rejected** because ~1 % of ordinary natural frames fail it, so any 330-tu test would false-alarm; the frozen statistic is the minimum over a 330-tu window of the mean Jaccard (576 natural windows from 32 population runs × 6,000 tu, 1-tu frames): P1 = 0.9332. Clean switch runs (120) never lose a neighbour (Jaccard 1.0), so τ_J is set by natural fluctuation.

## Results (deterministic bisection; 180 conditions = 5 patterns × 2 durations × 2 directions × 3 variants × 3 dishes)
**A threshold exists in 180/180 conditions.** The prediction "switchable whenever φ_max < 1" is **confirmed** for φ_max ∈ {0, 0.4, 0.8} at all three dishes (per-cell φ_k ≤ 0.8 g_min/g ≤ 0.8·0.3/0.3 = 0.8 at the weakest dish, κ_g = 1.5). It is not tested at φ ≥ 1.
### Minimal dose (amplitude × duration × lit cells), a→b; b→a within 5 % (limb_side differs by up to 5 %: chirality), primary variant φ0.4
| dish κ_g (g) | dur | middle | limb_side | head_end | tail_end | whole |
|---|---|---|---|---|---|---|
| 1.50 (0.30) | 4/g (13.3 tu) | 270 (thr 3.38, 6 cells) | 317 (thr 4.75, 5 cells); b→a 325 | 1120 (thr 21, 4 cells) | 1813 (thr 34, 4 cells) | 350 (thr 1.09, 24 cells) |
| 1.50 (0.30) | 16/g (53.3 tu) | 200 (thr 0.625, 6 cells) | 221 (thr 0.828, 5 cells); b→a 229 | 453 (thr 2.12, 4 cells) | 800 (thr 3.75, 4 cells) | 270 (thr 0.211, 24 cells) |
| 2.45 (0.49) | 4/g (8.2 tu) | 374 (thr 7.62, 6 cells) | 439 (thr 10.8, 5 cells); b→a 459 | 1927 (thr 59, 4 cells) | 3397 (thr 104, 4 cells) | 465 (thr 2.38, 24 cells) |
| 2.45 (0.49) | 16/g (32.7 tu) | 233 (thr 1.19, 6 cells) | 260 (thr 1.59, 5 cells); b→a 265 | 621 (thr 4.75, 4 cells) | 1306 (thr 10, 4 cells) | 306 (thr 0.391, 24 cells) |
| 4.00 (0.80) | 4/g (5.0 tu) | 645 (thr 21.5, 6 cells) | 750 (thr 30, 5 cells); b→a 800 | 4320 (thr 216, 4 cells) | 6880 (thr 344, 4 cells) | 795 (thr 6.62, 24 cells) |
| 4.00 (0.80) | 16/g (20.0 tu) | 240 (thr 2, 6 cells) | 269 (thr 2.69, 5 cells); b→a 281 | 880 (thr 11, 4 cells) | 1760 (thr 22, 4 cells) | 315 (thr 0.656, 24 cells) |

### Effect of the dial on the threshold amplitude (median dish, middle disc and whole body, ratio to φ0)
* middle, 4/g: φ0.4 ×1.034, φ0.8 ×1.153
* middle, 16/g: φ0.4 ×1.056, φ0.8 ×1.194
* whole, 4/g: φ0.4 ×1.086, φ0.8 ×1.257
* whole, 16/g: φ0.4 ×1.087, φ0.8 ×1.239

### Noise (CRN, σ_h 0.4 + structural 0.02, 100 tu burn-in, amplitude 1.2 × deterministic threshold, 6 seeds per condition; 1,080 trials)
| group | trials | SWITCH (all criteria) | memory state ok | shape ok | ORGANISM INTACT |
|---|---|---|---|---|---|
| phi0, 4/g | 180 | 51 | 169 | 51 | 178 |
| phi0, 16/g | 180 | 93 | 179 | 94 | 178 |
| phi04, 4/g | 180 | 67 | 173 | 67 | 178 |
| phi04, 16/g | 180 | 99 | 180 | 100 | 175 |
| phi08, 4/g | 180 | 81 | 173 | 81 | 172 |
| phi08, 16/g | 180 | 140 | 180 | 144 | 172 |
| κ_g = 1.50 | 360 | 62 | 337 | 62 | 347 |
| κ_g = 2.45 | 360 | 219 | 360 | 220 | 355 |
| κ_g = 4.00 | 360 | 250 | 357 | 255 | 351 |
| middle | 216 | 113 | 211 | 113 | 213 |
| limb_side | 216 | 107 | 212 | 111 | 206 |
| head_end | 216 | 83 | 213 | 85 | 207 |
| tail_end | 216 | 117 | 206 | 117 | 214 |
| whole | 216 | 111 | 212 | 111 | 213 |

Sham twins (amplitude 0, same code path and noise): 360 runs, 0 switch, 0 not intact.

Lag (tail-angle sign flip minus mean-ρ crossing), φ0.4 thresholds, all 60 conditions: median 5.88 tu, range -8.00 … 24.50
Max transient neighbour loss (1 − min Jaccard) over all 180 thresholds: 0.0129

## Which cells flip first, and φ_k (primary variant, median dish, whole-body light, 16/g)
Per-cell crossing time of ρ_i through ½ vs φ_k = αβ_E D_k/g: **Spearman +0.99** (4/g: +0.89): the cells with the smallest feedback (head places 0–3, φ_k ≈ 0) flip first; the cells at the hinge (places 14, 15, φ_k = 0.245 at this dish; 10/11, 16/17) flip last. The feedback *resists* the switch in proportion to φ_k, as the sign of the dial implies (it stabilises the current shape). For local lights the first cells to flip are lit, high-connectivity ones (Spearman of crossing time with the connectivity W: −0.4 … −0.7 for middle/limb_side; first places 10, 11, 14, 15, 13, 7), and for head_end/tail_end lights the lit tip cells (0–3, 20–23). In the φ = 0 variant the same W ordering holds without any φ effect.
## Lag between the mean-ρ crossing and the tail-angle sign flip
The tail angle flips sign **after** the mean-ρ crossing for whole-body and tip lights (median +6 tu over all φ0.4 conditions; whole body 14–15 tu: the cells at the hinge still hold the old shape) and **before** it for local lights near the hinge (down to −8 tu at middle/16/g: the hinge-adjacent cells flip first and the tail turns while the mean is still on the old side). Range over the 60 φ0.4 conditions: −8 … +24.5 tu. Shape relaxation after ρ crosses is therefore not a fixed lag; it is set by which cells flipped.
## Transient neighbour loss
Maximum over all 180 thresholds: **1.3 %** of neighbour pairs (min mean Jaccard 0.987); at 2× threshold 0 %. The switch is a rotation of the tail about the hinge with essentially no tearing at the 1.6 link radius; no cell lost; one component in all deterministic trials. (Contrast the damage runs of V4.)
## Dial cost
The feedback raises the threshold amplitude by ×1.03–1.09 (φ0.4) and ×1.15–1.26 (φ0.8) relative to φ0 at the median dish (see list above); dose spreads are dominated by location (tail-end 7–11× the middle disc at 4/g) and by κ_g (4/g: middle 270 → 645 from κ_g 1.5 to 4; at 16/g it is nearly constant, 200–240).
Not done: persistence of the switched state beyond the 20/g release (follows from V2 durability); b→a was bisected for all conditions; a→b and b→a thresholds are identical except the limb_side disc (≤ 5 % difference, the chiral template is not mirror-symmetric in its codes).
