"""morphogenesis/viz/build_index.py — index.html listing all exemplars.

Exemplar selection rule (declared BEFORE generation, per the ground rules):
for each batch of same-kind runs (e.g. a noise-seed sweep), pick:
  - median (by a pre-declared hidden-tier metric: type-constrained Hungarian
    distance-to-template on final positions)
  - best (lowest distance)
  - worst (highest distance)
  - two uniformly random picks (seeded, recorded)
This rule and its seeds are recorded in index.html itself, not just here.
"""
import json
import os
import numpy as np
from scipy.optimize import linear_sum_assignment


def hungarian_distance_type_constrained(final_x, target_x, final_type, target_type):
    """Type-constrained: only allow assignment between cells of the same
    type (per the paper's 4-type code); falls back to unconstrained if type
    info unavailable. Returns mean per-cell distance after assignment."""
    n = final_x.shape[1]
    cost = np.full((n, n), 1e6)
    for i in range(n):
        for j in range(n):
            if final_type is None or target_type is None or final_type[i] == target_type[j]:
                cost[i, j] = np.linalg.norm(final_x[:, i] - target_x[:, j])
    ri, ci = linear_sum_assignment(cost)
    return float(cost[ri, ci].sum() / n)


def select_exemplars(batch_metrics: dict, seed: int = 0):
    """batch_metrics: {run_id: metric_value}. Returns dict with the 5 picks
    and the rule text, for embedding in index.html."""
    ids = list(batch_metrics.keys())
    vals = np.array([batch_metrics[i] for i in ids])
    order = np.argsort(vals)
    best = ids[order[0]]
    worst = ids[order[-1]]
    median = ids[order[len(order) // 2]]
    rng = np.random.default_rng(seed)
    remaining = [i for i in ids if i not in (best, worst, median)]
    random_picks = list(rng.choice(remaining, size=min(2, len(remaining)), replace=False)) if remaining else []
    return {
        "rule": "median, best, worst by type-constrained Hungarian distance "
                "to template (hidden-tier metric), plus 2 uniformly random picks",
        "seed": seed,
        "best": best, "worst": worst, "median": median,
        "random": [str(x) for x in random_picks],
    }


INDEX_TEMPLATE = r"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Morphogenesis viewer index</title>
<style>
body{font-family:-apple-system,Helvetica,Arial,sans-serif;background:#111;color:#eee;padding:20px;}
table{border-collapse:collapse;width:100%;}
td,th{border:1px solid #333;padding:6px 10px;text-align:left;font-size:13px;}
th{background:#222;}
a{color:#7cf;}
.banner-unvalidated{background:#5c1a1a;color:#ffd0d0;padding:4px 8px;border-radius:4px;}
.banner-validated{background:#1a3d1a;color:#d0ffd0;padding:4px 8px;border-radius:4px;}
.rule{background:#1a1a2d;padding:10px;border-radius:6px;margin-bottom:16px;font-size:13px;}
</style></head>
<body>
<h1>Morphogenesis interactive viewer -- exemplar index</h1>
<div class="rule"><b>Exemplar selection rule</b> (declared before generation): __RULE_TEXT__</div>
<table>
<tr><th>Exemplar</th><th>File</th><th>Engine</th><th>Validation</th><th>Tier</th><th>Notes</th></tr>
__ROWS__
</table>
</body></html>
"""


def build_index(entries: list, out_path: str, rule_text: str):
    """entries: list of dicts with keys: name, file, engine, validation, tier, notes"""
    rows = []
    for e in entries:
        vclass = "banner-validated" if e["validation"] == "validated" else "banner-unvalidated"
        rows.append(
            f"<tr><td>{e['name']}</td><td><a href='{e['file']}'>{e['file']}</a></td>"
            f"<td>{e['engine']}</td><td><span class='{vclass}'>{e['validation']}</span></td>"
            f"<td>{e['tier']}</td><td>{e.get('notes','')}</td></tr>"
        )
    html = INDEX_TEMPLATE.replace("__ROWS__", "\n".join(rows)).replace("__RULE_TEXT__", rule_text)
    with open(out_path, "w") as f:
        f.write(html)
    return out_path
