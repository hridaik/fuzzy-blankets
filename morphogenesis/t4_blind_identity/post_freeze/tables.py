"""Reporting only: markdown tables for EVENTS_AND_PAIRS.md from the pairs JSON files."""
import json, numpy as np
rng = np.random.default_rng(1)
out = []
def f(x): return '%.2f' % x[0]
for tag, p in (('development', 'results_dev/pairs_dev.json'), ('held-out', 'results_heldout/pairs_heldout.json')):
    d = json.load(open(p))
    out.append(f'\n### Per opaque condition and arm - {tag} (O1; founders; proportions, dish-cluster bootstrap CIs in the JSON)\n')
    out.append('| condition | arm | founders | V | V_cons | C1 persist/change/break | C2 persist/change/break | C3 persist/change/break |\n|---|---|---|---|---|---|---|---|')
    for k, v in d['by_condition']['O1'].items():
        c, a = k.split('|')
        out.append(f"| {c} | {a} | {v['n_organisms']} | {f(v['V'])} | {f(v['V_conservative'])} | " + ' | '.join('/'.join(f(v[f'C{l}_{x}']) for x in ('persist', 'change', 'break')) for l in (1, 2, 3)) + ' |')
    out.append('\nDissociation of (C1/C2/C3) among treated/device founders (O1): ' + '; '.join(f'{k}: {n}' for k, n in d['dissociation']['O1'].items()))
    tr = d['triplets']
    out.append(f'\n### Paired differences treated - twin and sham - twin ({tag}; {len(tr)} triplets, pooled; cluster = triplet group)\n')
    out.append('| level | quantity | treated - twin [95 % CI] | sham - twin [95 % CI] |\n|---|---|---|---|')
    for lv in ('O1', 'O2', 'O3b'):
        for q, lab in (('V', 'V (founder fraction)'), ('Vc', 'V_conservative'), ('minJ', 'min Jaccard to initial members'), ('max_shape', 'max shape deviation'), ('max_pattern', 'max pattern deviation'), ('n_state_changes', 'state-change detections')):
            a = np.array([v[lv]['paired_treated_minus_twin'][q] for v in tr.values()]); b = np.array([v[lv]['paired_sham_minus_twin'][q] for v in tr.values()])
            def ci(x): bs = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(2000)]; return '%.2f [%.2f, %.2f]' % (x.mean(), np.quantile(bs, .025), np.quantile(bs, .975))
            out.append(f'| {lv} | {lab} | {ci(a)} | {ci(b)} |')
    m = [v[lv]['sham_matches_twin'] for v in tr.values() for lv in ('O1',)]
    out.append(f'\nShams matching their twins (same V, no event flags, same number of state-change detections) at O1: {np.mean(m):.2f} of {len(m)} triplets.')
open('results_heldout/tables.md', 'w').write('\n'.join(out))
print('\n'.join(out)[:200])
