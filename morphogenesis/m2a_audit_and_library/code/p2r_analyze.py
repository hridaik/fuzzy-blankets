"""Analysis of the revised Part 2 library (audit side): response = perturbed - matched unperturbed twin (positions + secreted levels), per role x channel x base.
Outputs data/v2/p2r_results.json. Summaries only (no blind-stage analysis: no partitions, no representation learning)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from p2_revised import *
def ex(p): return os.path.exists(p)
def R(base, role, ch, mode, verif=False):
    f = path("p2r", run_id(base, role, ch, mode, verif)); t = path("p2r", f"{'V_' if verif else ''}{base}_TWIN")
    if not (ex(f) and ex(t)): return None
    m, w = load(f), load(t); return np.vstack([m["positions"] - w["positions"], m["secretion"] - w["secretion"]])
def role_order(base, verif):
    cr = cells_by_role()["V" if verif else ("C1" if base == "C1" else "C0")]; return [cr[r] for r in range(8)]
def by_role(Rm, base, verif):
    """reorder the response rows so that cell blocks follow the role order (equivariance comparison across individuals)."""
    o = role_order(base, verif); pos = Rm[:16].reshape(8, 2, -1)[o].reshape(16, -1); sec = Rm[16:].reshape(8, 4, -1)[o].reshape(32, -1); return np.vstack([pos, sec])
def main():
    out = dict(amp=AMP, bases={}, linearity={}, equivariance={}, channels=CHN)
    for b in ("C0", "C1", *DEV):
        n = np.full((8, 10), np.nan); pk = np.full((8, 10), np.nan); fin = np.full((8, 10), np.nan)
        for r in range(8):
            for c in range(10):
                x = R(b, r, c, "p")
                if x is None: continue
                n[r, c] = np.linalg.norm(x); pk[r, c] = np.abs(x).max(); fin[r, c] = np.linalg.norm(x[:, -1])
        out["bases"][b] = dict(norm=n.tolist(), peak=pk.tolist(), final_norm=fin.tolist(), n_done=int(np.isfinite(n).sum()),
                               mean_norm_by_channel=np.nanmean(n, 0).tolist() if np.isfinite(n).any() else None, mean_norm_by_role=np.nanmean(n, 1).tolist() if np.isfinite(n).any() else None,
                               role_ratio_max_min=float(np.nanmax(np.nanmean(n, 1)) / np.nanmin(np.nanmean(n, 1))) if np.isfinite(n).all() else None)
    for b in LIN_BASES:
        rows = []
        for r in LIN_ROLES:
            for c in range(10):
                p, n_, x2 = R(b, r, c, "p"), R(b, r, c, "n"), R(b, r, c, "x2")
                if p is None or n_ is None or x2 is None: continue
                npn = np.linalg.norm(p)
                rows.append(dict(role=r, ch=CHN[c], resp_norm=float(npn), sign_err=float(np.linalg.norm(n_ + p) / npn), x2_err=float(np.linalg.norm(x2 - 2 * p) / np.linalg.norm(2 * p))))
        out["linearity"][b] = dict(rows=rows, n=len(rows), median_sign_err=float(np.median([r["sign_err"] for r in rows])) if rows else None, median_x2_err=float(np.median([r["x2_err"] for r in rows])) if rows else None,
                                   frac_sign_below_5pct=float(np.mean([r["sign_err"] < 0.05 for r in rows])) if rows else None, frac_x2_below_5pct=float(np.mean([r["x2_err"] < 0.05 for r in rows])) if rows else None)
    eq = []
    for r in range(8):
        for c in range(10):
            a, v = R("C0", r, c, "p"), R("C0", r, c, "p", True)
            if a is None or v is None: continue
            A, V_ = by_role(a, "C0", False), by_role(v, "C0", True); eq.append(dict(role=r, ch=CHN[c], rel_diff=float(np.linalg.norm(A - V_) / np.linalg.norm(A))))
    out["equivariance"] = dict(rows=eq, n=len(eq), median=float(np.median([e["rel_diff"] for e in eq])) if eq else None, max=float(np.max([e["rel_diff"] for e in eq])) if eq else None)
    json.dump(out, open(os.path.join(DATA, "v2", "p2r_results.json"), "w"), indent=1)
    for b, v in out["bases"].items(): print(b, v["n_done"], None if v["mean_norm_by_channel"] is None else np.round(v["mean_norm_by_channel"], 3), v["role_ratio_max_min"])
    for b, v in out["linearity"].items(): print("lin", b, {k: v[k] for k in v if k != "rows"})
    print("equiv", {k: out["equivariance"][k] for k in ("n", "median", "max")})
if __name__ == "__main__": main()
