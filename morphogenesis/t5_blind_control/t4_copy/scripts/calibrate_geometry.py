"""Calibrate geometric constants on NATURAL DEVELOPMENT dishes, calibration subset (body_id even).
Validation subset = body_id odd (development only). Held-out natural dishes are never touched."""
import sys, json; sys.path.insert(0, '.')
import numpy as np
from t4 import io, segment
from t4.geom import mst_max_edge
cat = io.catalog()
nat = [r for r in cat if r['condition'] == 'N0' and r['split'] == 'development']
cal = [r for r in nat if r['body_id'] % 2 == 0]; val = [r for r in nat if r['body_id'] % 2 == 1]
def mx(rs): return np.array([[mst_max_edge(f['xy']) for f in io.point_frames(r['run'], 'O1')] for r in rs])
a, b = mx(cal), mx(val)
grid = np.round(np.arange(1.1, 2.5, 0.1), 2)
r_link = None
for g in grid:
    if (a.max(1) > g).mean() <= 0.01:
        r_link = float(g); break
out = dict(n_cal=len(cal), n_val=len(val), r_link=r_link, r_hold=round(1.3 * r_link, 2),
           r_coh=float(np.round(np.quantile(a, 0.99), 2)),
           val_dish_exceed_rate_at_r_link=float((b.max(1) > r_link).mean()),
           cal_dish_exceed_rate_at_r_link=float((a.max(1) > r_link).mean()),
           m_min=3, margin=0.15)
# ---- O3 observation constants (O1 used only as co-registered reference on development calibration dishes)
sc = {}
sub = cal[:40]
for s in (0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6):
    cs = []
    for r in sub[:15]:
        t, im = io.image_frames(r['run'], 'O3a'); F = io.point_frames(r['run'], 'O1')
        X, Y = segment.grid(r['fov'])
        for k in (0, 4):
            m = segment.design(X, Y, F[k]['xy'], s) @ F[k]['lev'][:, 6]
            cs.append(np.corrcoef(m, im[k, 0].ravel())[0, 1])
    sc[s] = float(np.mean(cs))
s_eff = max(sc, key=sc.get)
from t4 import o3
ms = []; trend = []
cfg0 = dict(fg_sigma_mult=4.0, s_eff=s_eff)
for r in sub:
    t, im = io.image_frames(r['run'], 'O3a'); X, Y = segment.grid(r['fov']); px = 2 * r['fov'] / 64
    far = np.hypot(X, Y) > 0.75 * r['fov']
    row = []
    for k in range(8):
        fp = o3.frame_points(im[k], r['fov'], cfg0)
        reg = o3.regions(64, [fp['ids']], r['fov'], cfg0)[0]
        I = np.clip(im[k, 0].astype(float) - im[k, 0][far].mean(), 0, None).ravel()
        row.append(I[reg].sum() * px * px / r['n_cells'])
    ms += row; trend.append(row)
trend = np.mean(trend, 0)
out.update(s_eff=s_eff, s_eff_scan=sc, mass_per_cell=float(np.mean(ms)), mass_per_cell_sd=float(np.std(ms)), mass_per_cell_by_frame=[float(v) for v in trend],
           fg_sigma_mult=4.0, rl_iters=10)
# fg threshold check on calibration dishes: single component rate
from scipy.ndimage import gaussian_filter, label
ncs = []
for r in cal[:40]:
    t, im = io.image_frames(r['run'], 'O3a'); X, Y = segment.grid(r['fov']); far = np.hypot(X, Y) > 0.75 * r['fov']
    for k in range(8):
        I = gaussian_filter(im[k, 0].astype(float), 0.5); thr = I[far].mean() + 4 * I[far].std()
        L, n = label(I > thr, structure=np.ones((3, 3))); ncs.append(int((np.bincount(L.ravel())[1:] >= 8).sum()))
out['o3_cal_single_component_rate'] = float(np.mean(np.array(ncs) == 1))
out['o3_sign_S0'] = 0.5   # declared; natural |S| ~2.0 (sd 0.04) on calibration dishes
json.dump(out, open('calibration/geometry.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
