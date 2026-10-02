"""R1 analysis (canonical clock, 50 primary + up to 50 secondary; T_dev=512 comparison on 10 primary): shape classes, d_target (audit),
residuals, beliefs, role maps, stationarity, merging. Freezes the reference phenotype (sealed)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from analysis import d_target, P_X
from outcomes import d_pair_pos
from r2_analyze import wilson

def full(name, stage="census"):
    A, B = load(path(stage, name + "_A")), load(path(stage, name + "_B"))
    return {k: np.hstack([A[k], B[k]]) for k in ("positions", "secretion", "v_expect")}

def single_linkage(D, tau):
    n = len(D); lab = list(range(n))
    def find(x):
        while lab[x] != x: lab[x] = lab[lab[x]]; x = lab[x]
        return x
    for i in range(n):
        for j in range(i + 1, n):
            if D[i, j] < tau: lab[find(i)] = find(j)
    roots = {}; out = []
    for i in range(n): out.append(roots.setdefault(find(i), len(roots)))
    return out

def main():
    names = [f"primary_{i:04d}" for i in range(50)] + [f"secondary_{i:04d}" for i in range(50) if os.path.exists(path("census", f"secondary_{i:04d}_B"))]
    rows, ends, M = [], {}, {}
    for nm in names:
        m = full(nm); M[nm] = m; pos, sec, v = state(m); ends[nm] = (pos, sec)
        d, rm, ft, mm = d_target(pos, sec); p = softmax_cols(v)
        res = sorted(float(np.linalg.norm(pos[:, i] - P_X[:, rm[i]])) for i in range(8))
        rows.append(dict(id=nm, stationary=stationarity(m), d_target=float(d), n_type_mismatch=int(mm), role_map=[int(x) for x in rm],
                         max_belief=[float(x) for x in p.max(0)], residuals=res, n_argmax_slots=int(len(set(p.argmax(0))))))
    ref_pos, ref_sec = ends["primary_0000"]
    json.dump(dict(pos=ref_pos.tolist(), sec=ref_sec.tolist(), source="R1 primary_0000, canonical clock (T_dev=32), bin 512"), open(os.path.join(SEALED, "reference_phenotype_v2.json"), "w"))
    dd = np.linalg.norm(ref_pos[:, :, None] - ref_pos[:, None, :], axis=0); np.fill_diagonal(dd, np.inf); nn = dd.min(1)
    n = len(names); D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n): D[i, j] = D[j, i] = d_pair_pos(*ends[names[i]], *ends[names[j]])
    out = dict(n=n, nn_spacing_ref=dict(mean=float(nn.mean()), min=float(nn.min())))
    for f in (0.5, 1.0, 2.0):
        tau = f * 0.25 * float(nn.min()); lab = single_linkage(D, tau); cnt = np.bincount(lab)
        out[f"classes_tau_x{f}"] = dict(tau=tau, n_classes=int(len(cnt)), sizes=sorted(cnt.tolist(), reverse=True))
    lab = single_linkage(D, 0.25 * float(nn.min()))
    for r, l in zip(rows, lab): r["class"] = int(l)
    mod = np.bincount(lab).argmax(); n_prim = 50
    cls = {}
    for c in sorted(set(lab)):
        mem = [r for r in rows if r["class"] == c]
        cls[str(c)] = dict(size=len(mem), n_primary=sum(r["id"].startswith("primary") for r in mem), n_secondary=sum(r["id"].startswith("secondary") for r in mem),
                           d_target=[min(r["d_target"] for r in mem), max(r["d_target"] for r in mem)], stationary_bins=sorted(set(r["stationary"]["bin"] for r in mem)),
                           max_belief_range=[min(min(r["max_belief"]) for r in mem), max(max(r["max_belief"]) for r in mem)], members=[r["id"] for r in mem][:10],
                           distinct_role_maps=len(set(tuple(r["role_map"]) for r in mem)), residuals_first=mem[0]["residuals"])
    out["classes"] = cls; out["modal_class"] = int(mod)
    nsec = sum(r["id"].startswith("secondary") for r in rows)
    out["class_freq"] = {"primary": {str(c): [sum(1 for r in rows if r["id"].startswith("primary") and r["class"] == c), n_prim, wilson(sum(1 for r in rows if r["id"].startswith("primary") and r["class"] == c), n_prim)] for c in sorted(set(lab))},
                         "secondary": {str(c): [sum(1 for r in rows if r["id"].startswith("secondary") and r["class"] == c), nsec, wilson(sum(1 for r in rows if r["id"].startswith("secondary") and r["class"] == c), nsec)] for c in sorted(set(lab))}}
    out["stationarity_kinds"] = {str(k): sum(1 for r in rows if r["stationary"]["kind"] == k) for k in ("FIXED", "CYCLE2", None)}
    out["role_maps_distinct_all"] = len(set(tuple(r["role_map"]) for r in rows))
    # merging within the modal class
    sel = [r["id"] for r in rows if r["class"] == mod][:6] + [r["id"] for r in rows if r["class"] == mod and r["id"].startswith("secondary")][:6]
    sel = list(dict.fromkeys(sel)); nb = M[sel[0]]["positions"].shape[1]; mx = []
    for b in range(nb):
        S = [(M[a]["positions"][:, b].reshape(8, 2).T, M[a]["secretion"][:, b].reshape(4, 8, order="F")) for a in sel]
        mx.append(max(d_pair_pos(*S[i], *S[j]) for i in range(len(S)) for j in range(i + 1, len(S))))
    mx = np.array(mx); first = {}
    for thr in (0.17, 1e-3, 1e-6, 1e-9):
        bad = np.nonzero(mx >= thr)[0]; first[str(thr)] = int(bad.max() + 1) if len(bad) else 0
    seg = np.arange(40, 120); g = mx[seg] > 1e-11; sl = np.polyfit(seg[g], np.log(mx[seg][g]), 1)[0] if g.sum() > 5 else None
    out["merge"] = dict(n_ind=len(sel), first_bin_below=first, floor=float(mx[-50:].max()), log_slope_bins_40_120=None if sl is None else float(sl), tau_bins=None if sl is None else float(-1 / sl), series_every4=mx[::4].tolist())
    s512 = []
    for i in range(10):
        m = load(path("census512", f"primary_{i:04d}")); pos, sec, v = state(m)
        s512.append(dict(id=i, stationarity=stationarity(m), d_target_512=float(d_target(*state(m, 511)[:2])[0]), d_target_1024=float(d_target(*state(m, 1023)[:2])[0]),
                         d_target_2048=float(d_target(pos, sec)[0]), dpair_end_to_canonical_ref=float(d_pair_pos(pos, sec, ref_pos, ref_sec)), max_belief=float(softmax_cols(v).max()),
                         lag1_speed_end=float(lag_speed(m, 1)[-1])))
    out["T512"] = s512
    json.dump(dict(summary=out, rows=rows), open(os.path.join(DATA, "v2", "r1_results.json"), "w"), indent=1)
    o2 = dict(out); o2["merge"] = {k: v for k, v in out["merge"].items() if k != "series_every4"}; o2.pop("T512")
    print(json.dumps(o2, indent=1))

if __name__ == "__main__":
    main()
