import sys, os, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *
from outcomes import *
from r1_analyze import full
from analysis import d_target, P_X
ref = load_ref(); rp, rs = ref
R2 = json.load(open(os.path.join(DATA, "v2", "r2_results.json")))
B = {n: state(full(n)) for n in ("secondary_0005", "secondary_0012", "secondary_0013")}
ex = B["secondary_0005"][:2]
# (b)
nov = [r for r in R2 if r["shape"] == "NOVEL"]; ends = []
for r in nov:
    ind = Ind("primary", r["ind"]); m = load(path("r2", f"{ind.name}_{r['kind']}_{r['timing']}")); p, s, _ = state(m); ends.append((p, s))
print("(b) NOVEL runs:", [(r["ind"], r["kind"], r["timing"]) for r in nov])
print("   d_pair to ref:", [round(d_pair_pos(*e, *ref), 3) for e in ends])
print("   d_pair to class-1 exemplar:", [round(d_pair_pos(*e, *ex), 4) for e in ends])
print("   mutual d_pair:", np.round([[d_pair_pos(*a, *b) for b in ends] for a in ends], 3).tolist())
# (e) class 1
for n, (p, s, v) in B.items():
    P = softmax_cols(v); am = P.argmax(0); cnt = np.bincount(am, minlength=8)
    d, rm, ft, mm = d_target(p, s)
    print(n, "argmax slots", am.tolist(), "duplicated slots", np.nonzero(cnt > 1)[0].tolist(), "vacant", np.nonzero(cnt == 0)[0].tolist(), "max belief", P.max(0).round(3).tolist(), "least concentrated cell", int(P.max(0).argmin()))
    sl, _ = slot_assignment(p, s); print("   ref-slot assignment", sl.tolist(), "unmatched? distinct", len(set(sl)))
    mf = full(n); fe = load(path("census", n + "_B"))["free_energy_J"].ravel()[-1]
    print("   free energy J end", float(fe))
f0 = load(path("census", "primary_0000_B"))["free_energy_J"].ravel()[-1]; print("class 0 J end", float(f0))
# symmetry: mirror images
def hung_pos(a, b):
    from scipy.optimize import linear_sum_assignment
    C = np.linalg.norm(a[:, :, None] - b[:, None, :], axis=0); r, c = linear_sum_assignment(C); return float(C[r, c].mean())
names = list(B)
for i in range(3):
    for j in range(i + 1, 3):
        pi, pj = B[names[i]][0], B[names[j]][0]
        print(names[i], names[j], "d(pos)", round(hung_pos(pi, pj), 4), "d(pos mirrored y)", round(hung_pos(pi * np.array([[1], [-1]]), pj), 4))
# mirror symmetry of one class-1 state about the best y0 and of class-0
for nm, (p, s, v) in [("class0", state(full("primary_0000"))), ("class1", B["secondary_0005"])]:
    best = min(((hung_pos(p * np.array([[1], [-1]]) + np.array([[0], [2 * y0]]), p), y0) for y0 in np.linspace(-0.5, 0.5, 101)))
    bestx = min(((hung_pos(p * np.array([[-1], [1]]) + np.array([[2 * x0], [0]]), p), x0) for x0 in np.linspace(-1, 1, 201)))
    print(nm, "y-mirror residual", round(best[0], 4), "at y0", round(best[1], 3), "| x-mirror residual", round(bestx[0], 4))
