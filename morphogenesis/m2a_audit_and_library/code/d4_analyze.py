"""D4 analysis: thresholds per actuator class and per role / region; min, median, max/min ratios; identity outcome just above each threshold. Writes data/v2/d4_summary.json."""
import sys, os, json, glob, re, collections
sys.path.insert(0, os.path.dirname(__file__))
from d4_full import *
def parse(did):
    m = re.match(r"disp1_r(\d+)_t(\d+)$", did)
    if m: return "disp1", dict(role=int(m[1]), theta=int(m[2]))
    m = re.match(r"pulsec_r(\d+)_l(\d)$", did)
    if m: return "pulse_single", dict(role=int(m[1]), lig=int(m[2]))
    m = re.match(r"region_g(\d+)_l(\d)$", did)
    if m: return "pulse_region", dict(g=int(m[1]), lig=int(m[2]))
    m = re.match(r"global_l(\d)$", did)
    if m: return "pulse_global", dict(lig=int(m[1]))
    if did.startswith("body_eig"): return "body_eigpos", dict(k=int(did[8:]))
    if did.startswith("bodyv_eig"): return "body_eigbelief", dict(k=int(did[9:]))
    if did.startswith("body_rand"): return "body_random", dict(k=int(did[9:]))
    return "other", {}
def stat(v):
    v = [x for x in v if x is not None]; return dict(n=len(v), min=min(v), median=float(np.median(v)), max=max(v)) if v else dict(n=0)
def main():
    rows = []
    cent = {s["id"]: s.get("centre") for s in dirs_region()}
    for f in sorted(glob.glob(os.path.join(DATA, "v2", "d4", "dir_*.json"))):
        r = json.load(open(f)); cls, meta = parse(r["id"]); meta["id"] = r["id"]; meta["centre"] = cent.get(r["id"])
        top = {"disp1": 10.0, "body_eigpos": 10.0, "body_eigbelief": 10.0, "body_random": 10.0}.get(cls, 50.0)
        rows.append(dict(cls=cls, meta=meta, swap=r.get("swap"), switch=r.get("switch"), a_max=r["a_max"], swap_above=r.get("swap_just_above"), switch_above=r.get("switch_just_above"),
                         nonmono=r["nonmonotone"], top=r["outcomes_top"],
                         swap_nchg=(r["evals"].get(f"{float(f'{r['swap']:.6g}'):.6g}", {}).get("n_changed") if r.get("swap") else None)))
    out = dict(n_dirs=len(rows), classes={})
    for cls in sorted({r["cls"] for r in rows}):
        R = [r for r in rows if r["cls"] == cls]; d = dict(n=len(R), a_max=R[0]["a_max"])
        for key in ("swap", "switch"):
            thr = [r[key] for r in R]; d[key] = dict(n_with_threshold=sum(t is not None for t in thr), n_none=sum(t is None for t in thr), **{k: v for k, v in stat(thr).items() if k != "n"},
                                                       above=dict(collections.Counter(r[key + "_above"] for r in R if r[key] is not None)))
        nc = [r["swap_nchg"] for r in R if r["swap_nchg"] is not None]; d["swap"]["cells_changed_at_threshold"] = dict(collections.Counter(nc))
        d["n_nonmonotone"] = sum(r["nonmono"] for r in R)
        if cls in ("disp1", "pulse_single"):
            byrole = {}
            for ro in range(8):
                rr = [r for r in R if r["meta"]["role"] == ro]
                byrole[ro] = {key: dict(n=len(rr), n_thr=sum(r[key] is not None for r in rr), min=(min([r[key] for r in rr if r[key] is not None]) if any(r[key] is not None for r in rr) else None),
                                        median=(float(np.median([r[key] for r in rr if r[key] is not None])) if any(r[key] is not None for r in rr) else None)) for key in ("swap", "switch")}
            d["by_role"] = byrole
            for key in ("swap", "switch"):
                med = [byrole[ro][key]["median"] for ro in range(8) if byrole[ro][key]["median"] is not None]; mn = [byrole[ro][key]["min"] for ro in range(8) if byrole[ro][key]["min"] is not None]
                d[key]["role_ratio_median_max_over_min"] = (max(med) / min(med)) if len(med) >= 2 else None; d[key]["role_ratio_min_max_over_min"] = (max(mn) / min(mn)) if len(mn) >= 2 else None
        if cls == "pulse_region":
            bg = {}
            for r in R: bg.setdefault(r["meta"]["g"], []).append(r)
            d["by_centre"] = {str(g): dict(centre=v[0]["meta"]["centre"], swap_min=min([x["swap"] for x in v if x["swap"] is not None], default=None), swap_median=(float(np.median([x["swap"] for x in v if x["swap"] is not None])) if any(x["swap"] is not None for x in v) else None),
                                           switch_min=min([x["switch"] for x in v if x["switch"] is not None], default=None)) for g, v in sorted(bg.items())}
            meds = [x["swap_median"] for x in d["by_centre"].values() if x["swap_median"] is not None]; d["swap"]["centre_ratio_median_max_over_min"] = (max(meds) / min(meds)) if len(meds) >= 2 else None
        out["classes"][cls] = d
    json.dump(out, open(os.path.join(DATA, "v2", "d4_summary.json"), "w"), indent=1, default=str)
    for c, d in out["classes"].items(): print(c, d["n"], "swap", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in d["swap"].items()}, "| switch", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in d["switch"].items()})
if __name__ == "__main__": main()
