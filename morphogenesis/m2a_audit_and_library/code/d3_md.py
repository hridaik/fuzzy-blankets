import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
def L(f): return json.load(open(os.path.join(DATA, "v2", f"d3_{f}.json")))
def table(f, title):
    R = L(f); top = max(range(len(R)), key=lambda i: R[i]["level"]); out = [f"#### {title}", "", "| step | dir | level | attractor | settle bin | roles (slot of cell 0..7) | d to class-0 ref | d to class-1 ref | cycle amp |", "|---|---|---|---|---|---|---|---|---|"]
    for r in R:
        out.append(f"| {r['step']} | {'up' if r['step'] <= top else 'down'} | {r['level']:g} | {r['kind'] or 'NONCONV (4 × 192 bins)'} | {r['settle_bin'] if r['settle_bin'] is not None else '-'} | {''.join(map(str, r['slots']))} | {r['d_ref0']:.3f} | {r['d_ref1']:.3f} | {'' if r.get('cycle_amp') is None else format(r['cycle_amp'], '.3f')} |")
    return "\n".join(out)
if __name__ == "__main__":
    parts = [table("DH_c0", "DH_ε from class 0 (s = (1−ε)x + εx²)"), table("DT_c0", "DT_ε from class 0 (s = (1−ε)x − εx²)"), table("DH_c1", "DH_ε from class 1 (up-sweep to ε = 0.5 only)"), table("DT_c1", "DT_ε from class 1"),
             table("PREC_c0", "Sensory-precision multiplier φ = ln F from class 0 (V = exp(3+φ))"), table("PREC_c1", "Sensory-precision multiplier from class 1")]
    open(os.path.join(DATA, "v2", "d3_tables.md"), "w").write("\n\n".join(parts) + "\n")
