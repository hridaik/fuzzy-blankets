"""Part 1 analysis (v2). 1.1 16-cell census (permutation-invariant clustering, tau rescaled to the 16-cell reference's NN spacing);
1.2 FR / PL families vs the class-0/class-1 taxonomy and role maps; 1.3 high initial identity expectation k=2,4."""
import sys, os, json, glob
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *
from r1_analyze import single_linkage
from r2_analyze import wilson
import r2_withdrawal as R2
TAU8 = json.load(open(os.path.join(SEALED, "thresholds_v2.json")))["tau_pair"]
EX1 = None
def cls8(pos, sec):
    global EX1
    if EX1 is None: EX1 = state(load(path("census", "secondary_0005_A")))[:2]
    rp, rs = load_ref()
    if d_pair_pos(pos, sec, rp, rs) < TAU8: return "class0"
    if d_pair_pos(pos, sec, *EX1) < TAU8: return "class1"
    return "other"
def full(stage, name, parts, n=8):
    ms = [load(path(stage, f"{name}_{p}")) for p in parts]; out = {k: np.hstack([m[k] for m in ms]) for k in ("positions", "secretion", "v_expect")}; out["n"] = n; return out
def p11():
    ends, stat = {}, {}
    for i in range(30):
        nm = f"primary_{i:04d}"; m = full("p1_16", nm, "AB", 16); st = stationarity(m); stat[nm] = st["kind"]; ends[nm] = state(m, n=16)[:2]
    ref = ends["primary_0000"][0]; dd = np.linalg.norm(ref[:, :, None] - ref[:, None, :], axis=0); np.fill_diagonal(dd, np.inf); nn = dd.min(1)
    tau = 0.25 * nn.min(); names = list(ends); n = len(names); D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n): D[i, j] = D[j, i] = d_pair_pos(*ends[names[i]], *ends[names[j]])
    lab = single_linkage(D, tau); sizes = np.bincount(lab)
    return dict(n=n, stationary=dict(zip(*np.unique([str(v) for v in stat.values()], return_counts=True))), min_nn=float(nn.min()), mean_nn=float(nn.mean()), tau16=float(tau),
                n_clusters=int(len(sizes)), cluster_sizes=sorted(sizes.tolist(), reverse=True), within_cluster_max=float(max([D[i, j] for i in range(n) for j in range(n) if lab[i] == lab[j] and i != j] or [0])),
                dmin_between=float(min([D[i, j] for i in range(n) for j in range(n) if lab[i] != lab[j]] or [np.nan])), labels=lab)
def p12():
    W = R2.W_bins(); out = {}
    for fam in ("FR", "PL"):
        for t in ("SUSTAINED", "DEV-LONG", "ADULT"):
            rows = []
            for i in range(10):
                nm = f"primary_{i:04d}"; f = path("p1_fam", f"{nm}_{fam}_{'SUST' if t == 'SUSTAINED' else t}")
                if not os.path.exists(f): continue
                m = load(f); m["n"] = 8; st = stationarity(m); pos, sec, _ = state(m)
                if t == "ADULT":
                    A = load(path("census", f"{nm}_A")); pu, su, _ = state(A); sl_u, _ = slot_assignment(pu, su); sl, _ = slot_assignment(pos, sec)
                    rel = bool((sl != sl_u).sum() > 0); dU = d_pair_pos(pos, sec, pu, su)
                else:
                    rel = None; dU = None
                rows.append(dict(ind=nm, stat=st["kind"], cls=cls8(pos, sec) if st["kind"] else "NONCONV", d_ref=float(d_pair_pos(pos, sec, *load_ref())), relabelled=rel, d_unpert=dU))
            c = {}
            for r in rows: c[r["cls"]] = c.get(r["cls"], 0) + 1
            out[f"{fam}-{t}"] = dict(n=len(rows), classes=c, stat={k: sum(1 for r in rows if str(r["stat"]) == k) for k in set(str(r["stat"]) for r in rows)},
                                     relabelled=None if t != "ADULT" else sum(1 for r in rows if r["relabelled"]), d_ref=[round(r["d_ref"], 3) for r in rows])
    return out
def p13():
    out = {}
    for k in (2, 4):
        rows = []
        for i in range(10):
            nm = f"primary_{i:04d}_k{k}"; m = full("p1_hi", nm, "AB"); st = stationarity(m); pos, sec, _ = state(m); sl, _ = slot_assignment(pos, sec)
            base = load(path("census", f"primary_{i:04d}_A")); pu, su, _ = state(base); sl0, _ = slot_assignment(pu, su)
            rows.append(dict(ind=nm, stat=st["kind"], cls=cls8(pos, sec) if st["kind"] else "NONCONV", d_ref=float(d_pair_pos(pos, sec, *load_ref())), slots_first_k=[int(x) for x in sl[:k]],
                             slots_first_k_default=[int(x) for x in sl0[:k]], same_slots=bool((sl[:k] == sl0[:k]).all())))
        c = {}
        for r in rows: c[r["cls"]] = c.get(r["cls"], 0) + 1
        out[f"k{k}"] = dict(n=10, classes=c, same_roles_first_k=sum(r["same_slots"] for r in rows), rows=rows)
    return out
if __name__ == "__main__":
    R = dict(p11=p11(), p12=p12(), p13=p13()); R["p11"]["labels"] = [int(x) for x in R["p11"]["labels"]]; R["p11"]["stationary"] = {str(k): int(v) for k, v in R["p11"]["stationary"].items()}
    json.dump(R, open(os.path.join(DATA, "v2", "p1_results.json"), "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in R["p11"].items() if k != "labels"}, indent=1)); print(json.dumps(R["p12"], indent=1)); print({k: {x: y for x, y in v.items() if x != "rows"} for k, v in R["p13"].items()})
