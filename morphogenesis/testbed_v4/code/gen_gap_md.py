import json, os, sys, numpy as np
sys.path.insert(0, '.')
from v5 import *
D = '../data'; g0 = gamma0(); L = []
gaps = {lv: json.load(open(f'{D}/v5_gap_L{lv}.json')) for lv in (0, 1, 2)}
L.append("""# ADAPTIVITY_GAP.md — gate V5 (adaptivity gap, primary variant)

Labels ESTABLISHED / PROVISIONAL / NOT DONE. Code `code/v5.py`, `v4cal.py`, `gen_gap_md.py`; data `data/v5_thr_L{0,1,2}.json` (exact switch thresholds), `v5_chi_L{0,1,2}.json` (exact damage-onset constant χ), `v5_gap_L{0,1,2}.json`, `v5_validate.json`.

## **GATE V5: FAILED. A single fixed (centre, duration, amplitude) policy delivers SWITCH with no damage in 100 % of the 40 dishes at the specified population and at both permitted widenings (gate (a) ≤ 0.85). The per-dish oracle also reaches 100 % (gate (b) ≥ 0.98 holds). STOP, as the spec requires after two widenings. The adaptivity gap does not exist in this model at the declared design.**

## Protocol as run
* 40 dishes per level drawn from `dish.sample_dish(100 … 139)`: κ_g ~ LogUniform and a per-dish damage factor; **level 0** = as specified (κ_g [1.5, 4], factor [1/1.5, 1.5]); **widening 1** = as specified (κ_g [1.2, 5], factor [1/2, 2]); **widening 2** (declared before it was computed) = κ_g [1.1, 7.0], factor [1/3, 3]. The realised ranges of the 40 draws: level 0 κ_g 1.50–3.92, factor 0.68–1.45; level 1 κ_g 1.20–4.86, factor 0.51–1.88; level 2 κ_g 1.10–6.75, factor 0.35–2.72.
* Durations are fixed in time units: 4/g_med, 8/g_med, 16/g_med, 32/g_med = 8.2, 16.3, 32.7, 65.3 tu (g_med = 0.4899, the population median, unchanged by the widenings since √(κ_min κ_max) = 2.449 for all three ranges). Release 20/g of the dish. Discs: middle, limb-side, head-end, tail-end (r = 1.5).
* **Threshold** (per dish, grid point): exact bisection under the frozen SWITCH scoring (state + tail angle within 20 % of that dish's settled target angle + ORGANISM INTACT; deterministic, γ = 0, a → b). **Damage onset u_d**: = χ(κ_g, disc, duration) / (γ_0 · dish factor), where χ = γ u_d is the exact onset (10 CRN seeds, majority failure, 300 tu) computed on a κ_g grid (level 0: 1.5, 2.0, 2.45, 3.2, 4.0 × all 16 grid points = 80 searches; widenings: middle disc only, 7–8 κ_g values × 4 durations) and interpolated in log κ_g. This is a **declared deviation**: damage onset is not searched per dish (640 × 5 evaluations would not fit the budget). It rests on two measured facts: γ enters only through exp(−γ ū) so u_d ∝ 1/γ (V4: χ = 3.68 ± 4 % over γ = 0.5…9), and χ is almost independent of κ_g (χ(κ_g) at the middle disc: 22.6–23.6 / 9.0–9.3 / 3.70 / 2.64 for 4/8/16/32 over g_med from κ_g 1.5 to 4: ≤ 4 % spread; larger only at the tail-end disc, 8/g and 32/g).
* **Widened levels were evaluated on the middle-disc sub-grid only** (4 durations × 40 dishes = 160 thresholds per level). This suffices for the gate: a single policy on that sub-grid already serves 100 % of the dishes, so the best fixed policy over the full grid is ≥ that; the oracle is ≥ that too. The dose spread (c) at the widened levels is therefore the middle-disc spread.
## Results
| level | κ_g range | factor range | best fixed policy (centre, duration, amplitude) | fraction of dishes with SWITCH and no damage | per-dish oracle | dose spread across dishes (oracle's minimum dose; max/min; CV) |
|---|---|---|---|---|---|---|""")
for lv, (kr, fr) in enumerate((((1.5, 4.0), (0.667, 1.5)), ((1.2, 5.0), (0.5, 2.0)), ((1.1, 7.0), (0.333, 3.0)))):
    g = gaps[lv]; p = g['best_fixed_policy']
    L.append(f"| {lv} ({'specified' if lv == 0 else 'widening %d' % lv}) | {kr} | {fr} | {p[0]}, {p[1]}/g_med, amplitude {p[2]:.3f} | **{g['best_fixed_frac']:.2f}** | {g['oracle_frac']:.2f} | {g['dose_min']:.0f}–{g['dose_max']:.0f} (median {g['dose_median']:.0f}); ×{g['dose_spread_ratio']:.2f}; CV {g['dose_cv']:.2f} |")
L.append("\n### Per grid point: threshold range over the 40 dishes and the fraction of dishes whose window (threshold < damage onset) is non-empty")
L.append("| level | disc, duration | threshold min–max (×) | fraction with a window |\n|---|---|---|---|")
for lv in (0, 1, 2):
    for k, v in gaps[lv]['per_condition'].items():
        L.append(f"| {lv} | {k.replace('_', ' ')}/g_med | {v['thr_min']:.3g}–{v['thr_max']:.3g} (×{v['ratio']:.2f}) | {v['frac_window']:.2f} |")
ds0 = dishes(0); ds1 = dishes(1); ds2 = dishes(2)
L.append(f"""
## Why there is no gap (PROVISIONAL, from the numbers above)
1. **At the middle disc the switch threshold barely moves between dishes when the pulse length is fixed in time units**: at 8/g_med = 16.3 tu the threshold is 2.38–2.50 (×1.05) across all 40 dishes at level 0 and 2.31–2.50 at level 2, although g varies ×2.6 (level 0) to ×6.1 (level 2) between dishes. (In units of the dish's own 1/g — v3's convention — it varies ×6 between κ_g 1.5 and 4: SWITCH_V4.md. The spec's fixed-time durations remove most of it. PROVISIONAL explanation: for a pulse long compared with the relaxation of l (≈ 10–20 tu) the threshold is set by the neighbours' ratio signal, f ≈ ½ + O(ratio of lit to dark secretion), which does not depend on g.)
2. **The damage onset of a pulse of given length and disc is, in units of γ·amplitude, the same for every dish** (χ independent of κ_g), so across dishes it moves only through the per-dish factor, by ×2.14 (level 0), ×3.7 (widening 1), ×7.8 (realised in widening 2; nominal ×9).
3. The median-dish window at the middle disc is 2.4–3.0 (V4). At level 0 the spread of damage onset (×2.14) and of threshold (×1.05–1.9) are both smaller than that window ({gaps[0]['per_condition']['middle_8']['ratio']:.2f} and 2.14 vs 2.5): one amplitude between the largest threshold and the smallest onset exists at every duration. At widening 1 it survives at 8/g and 16/g (max threshold / min onset = 0.62 and 0.91) and is lost at 4/g and 32/g (1.10, 1.02). At widening 2 it exists only at 8/g (window fractions 0.93 / 1.00 / 0.88 / 0.85 for 4/8/16/32), but that is enough for a 100 % policy.
4. The head-end and tail-end discs are useless as a policy: no safe window for any dish at the tail end (fraction 0.00 at all four durations), and for the head end only 0.43 of dishes at 32/g_med (level 0). The limb-side disc behaves like the middle disc, with ≈ 35 % higher thresholds.
## Consequences
* The adaptivity-gap premise ("no fixed pulse works across dishes") is **not supported** by the declared v4 design: a fixed middle-disc pulse of ≈ 16 tu and amplitude 2.5 would be a perfectly adequate fixed policy over all three populations. This is a result about the design, not an implementation failure; the gate is reported as failed and no further widening was performed (the spec allows at most two).
* What *would* create a gap (untested; for OPEN_QUESTIONS.md): durations in units of each dish's own 1/g (threshold ×6 across κ_g at 4/g, SWITCH_V4.md); a damage onset that depends on κ_g (χ is flat); a population with a heavier tail in the damage factor than ×9 combined with 8/g; or per-dish differences in disc geometry. A policy that must also *minimise dose* (rather than only succeed) has a spread of ×1.3–1.6 only.
* The data package and live environment were built although V5 failed (their build depends on V0–V4 and V6 only); DATASETS_V4.md says so.
## Validation of the interpolated damage onset (held-out dishes)""")
vp = f'{D}/v5_validate.json'
if os.path.exists(vp):
    v = json.load(open(vp)); err = np.array([r['rel_err'] for r in v if r['rel_err'] is not None])
    L.append("Exact per-dish damage-onset searches (true κ_g, true γ factor) for 8 level-0 dishes (the extremes of κ_g and of the factor plus random ones) at the middle disc, 8/g and 16/g, against the interpolated prediction:\n\n| dish | κ_g | factor | duration | predicted u_d | exact u_d | relative error |\n|---|---|---|---|---|---|---|")
    for r in v: L.append(f"| {r['dish']} | {r['kg']:.2f} | {r['gf']:.2f} | {r['dm']}/g_med | {r['u_d_pred']:.3f} | {('%.3f' % r['u_d_exact']) if r['u_d_exact'] else '-'} | {('%+.1f %%' % (100 * r['rel_err'])) if r['rel_err'] is not None else '-'} |")
    L.append(f"\nRelative error: median {100*np.median(err):+.1f} %, range {100*err.min():+.1f} … {100*err.max():+.1f} % (search resolution 6 % in amplitude: the exact search starts at the predicted amplitude, brackets by factors of 1.4 and bisects to 6 %, so an error of 0 % means the onset lies within 6 % below the prediction and errors below 6 % cannot be resolved — the validation shows the interpolation is accurate to the search resolution, not better). The gate result needs max threshold / min onset < 1 at one grid point only; the margin at 8/g (level 0: 0.48) is far larger than these errors.")
else: L.append("NOT YET AVAILABLE")
open('../ADAPTIVITY_GAP.md', 'w').write("\n".join(L)); print('written', len("\n".join(L)))
