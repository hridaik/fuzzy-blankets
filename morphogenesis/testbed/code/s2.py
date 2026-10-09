"""S2 switch geometry: how do L and R differ?"""
import sys, json; sys.path.insert(0, '.')
from asm import *
from scipy.optimize import linear_sum_assignment
t = make_body('chiral'); X = t.Xs[0]; ty = type_vector(t); n = 24
R = X * np.array([[1], [-1]])                                   # mirror image, same cell order of slots
out = {}
out['position_only_rigid_distance_reflection_allowed'] = d_rigid(X, None, R, None, reflection=True)
out['position_only_rigid_distance_proper_rotations_only'] = d_rigid(X, None, R, None, reflection=False)
out['typed_rigid_distance_proper_rotations_only'] = d_rigid(X, ty, R, ty[[int(np.argmin(np.linalg.norm(R - X[:, [j]], axis=0))) for j in range(n)]] if False else ty, reflection=False)
# R target with its own types: slot j of R is the mirror image of slot j of L (same type)
tyR = ty
# best correspondence L-cell -> R-slot: (1) type-free (min movement), (2) type-preserving
D = np.linalg.norm(X[:, :, None] - R[:, None, :], axis=0)              # (cell at L slot i, R slot j)
r, c = linear_sum_assignment(D); mv = D[r, c]
changed = int((ty[r] != tyR[c]).sum())
out['type_free_assignment'] = dict(mean_move=float(mv.mean()), max_move=float(mv.max()), n_type_changes=changed, n_cells_moving_gt_0p1=int((mv > 0.1).sum()))
Dt = D + 100 * (ty[:, None] != tyR[None, :]); r2, c2 = linear_sum_assignment(Dt); mv2 = D[r2, c2]
out['type_preserving_assignment'] = dict(mean_move=float(mv2.mean()), max_move=float(mv2.max()), n_type_changes=0, n_cells_moving_gt_0p1=int((mv2 > 0.1).sum()))
# is the position set mirror invariant? and which rows change type
sym = d_rigid(X, None, R, None)
out['position_set_mirror_symmetric'] = bool(sym < 1e-9)
chg = [int(i) for i in range(n) if ty[r[i]] != tyR[c[i]]]
out['type_changing_cells'] = dict(slots=chg, y_of_slots=[float(X[1, i]) for i in chg], types_from=[int(ty[r[i]]) for i in chg], types_to=[int(tyR[c[i]]) for i in chg])
print(json.dumps(out, indent=1)); json.dump(out, open('../data/s2_geometry.json', 'w'), indent=1)
