"""D3 analysis -> data/v2/d3_summary.json and HYSTERESIS.md table fragments."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
TAU = json.load(open(os.path.join(SEALED, "thresholds_v2.json")))["tau_pair"]
def load_chain(f): return json.load(open(os.path.join(DATA, "v2", f"d3_{f}.json")))
def summarize(f):
    R = load_chain(f); n = len(R); top = max(range(n), key=lambda i: R[i]["level"]); up = R[:top + 1]; down = R[top:]
    out = dict(chain=f, n_steps=n, top_level=R[top]["level"])
    pairs = []
    for u in up:
        for d in down:
            if abs(u["level"] - d["level"]) < 1e-9 and u is not d:
                pairs.append(dict(level=u["level"], kind_up=u["kind"], kind_down=d["kind"], slots_up="".join(map(str, u["slots"])), slots_down="".join(map(str, d["slots"])),
                                  d_up=u["d_ref0"], d_down=d["d_ref0"], shape_differs=abs(u["d_ref0"] - d["d_ref0"]) > 1e-3, roles_differ=u["slots"] != d["slots"], kind_differs=u["kind"] != d["kind"]))
    out["pairs"] = pairs; out["n_levels_compared"] = len(pairs)
    out["n_shape_differs"] = sum(p["shape_differs"] for p in pairs); out["n_roles_differ"] = sum(p["roles_differ"] for p in pairs); out["n_kind_differs"] = sum(p["kind_differs"] for p in pairs)
    s, e = R[0], R[-1]
    out["baseline"] = dict(start_slots="".join(map(str, s["slots"])), end_slots="".join(map(str, e["slots"])), start_d0=s["d_ref0"], end_d0=e["d_ref0"], start_d1=s["d_ref1"], end_d1=e["d_ref1"],
                           same_shape=abs(s["d_ref1"] - e["d_ref1"]) < 1e-3 and abs(s["d_ref0"] - e["d_ref0"]) < 1e-3, same_roles=s["slots"] == e["slots"], end_kind=e["kind"])
    out["cycles"] = [dict(step=r["step"], level=r["level"], dir="up" if r["step"] <= top else "down", amp=r.get("cycle_amp")) for r in R if r["kind"] == "CYCLE2"]
    out["nonconv"] = [dict(step=r["step"], level=r["level"], dir="up" if r["step"] <= top else "down") for r in R if r["kind"] is None]
    return out
if __name__ == "__main__":
    S = {f: summarize(f) for f in ("DH_c0", "DT_c0", "PREC_c0", "PREC_c1")}
    # class-1 DH chain: merge verification against class-0 chain (up to eps 0.5)
    c0, c1 = load_chain("DH_c0"), load_chain("DH_c1"); k = min(len(c0), len(c1))
    S["DH_c1_merge"] = dict(steps_compared=k - 1, max_abs_diff_d0=max(abs(c0[i]["d_ref0"] - c1[i]["d_ref0"]) for i in range(1, k)), max_abs_diff_d1=max(abs(c0[i]["d_ref1"] - c1[i]["d_ref1"]) for i in range(1, k)),
                            first_step_d0=c1[1]["d_ref0"], first_step_d1=c1[1]["d_ref1"], kinds_equal=all(c0[i]["kind"] == c1[i]["kind"] for i in range(1, k)))
    try:
        c0, c1 = load_chain("DT_c0"), load_chain("DT_c1"); k = min(len(c0), len(c1))
        S["DT_c1_merge"] = dict(steps_compared=k - 1, max_abs_diff_d0=max(abs(c0[i]["d_ref0"] - c1[i]["d_ref0"]) for i in range(1, k)), max_abs_diff_d1=max(abs(c0[i]["d_ref1"] - c1[i]["d_ref1"]) for i in range(1, k)),
                                first_step_d0=c1[1]["d_ref0"], first_step_d1=c1[1]["d_ref1"], kinds_equal=all(c0[i]["kind"] == c1[i]["kind"] for i in range(1, k)))
    except Exception as e: S["DT_c1_merge"] = str(e)
    json.dump(S, open(os.path.join(DATA, "v2", "d3_summary.json"), "w"), indent=1)
    for k, v in S.items():
        print(k, {a: b for a, b in v.items() if a != "pairs"})
