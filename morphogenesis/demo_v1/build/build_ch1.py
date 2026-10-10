"""Chapter 1.1-1.4 assets: published 8-cell oracle trace (Octave, canonical clock) + v3 natural body 2100 (clone pair a/b), window t = 3000..3059."""
import sys; sys.path.insert(0, '.')
from common import *
import scipy.io as sio
tm, XS, CT = template()
# ---------------- v3 natural body 2100 (package run_00011 = state a, run_00133 = state b: same body id, same seed)
T0, NT = 3000, 60
R_ = {}
for st in 'ab':
    d = pickle.load(open(f'{V3}/data/raw_v4/natural/{st}_cal_2100.pkl', 'rb')); R_[st] = d['frames'][T0:T0 + NT]
F0 = R_['a'][0]; R, tc, xc, assign = frame_map(F0['X'], F0['MU'])
types = CT[assign]                                      # true place type of each cell (1 head, 2 trunk, 3 limb, 4 tail) from the assigned place
from shape import cell_types
types_code = cell_types(F0['C'].T) if False else cell_types(F0['C'].T.T) if False else None
def stack(st, k): return np.stack([f[k] for f in R_[st]])
X = np.stack([to_body(f['X'], R, tc, xc) for f in R_['a']])                       # (T,24,2) body frame (head left = -x, limb side = +y)
Xb = np.stack([to_body(f['X'], R, tc, xc) for f in R_['b']]); print('max |Xa-Xb| (body frame):', np.abs(X - Xb).max())
sgm = lambda z: 1 / (1 + np.exp(-z))
def fpar(Xf, D):
    d = np.linalg.norm(Xf[:, None] - Xf[None], axis=-1); W = np.exp(-d); np.fill_diagonal(W, 0); A = W @ D[:, 0]; B = W @ D[:, 1]; return (A + 5e-4) / (A + B + 1e-3)
out = dict(T=NT, dt=1.0, X=enc16(X, 1000), types=types.tolist(), place=assign.tolist(), tmplXY=XS.tolist(), tmplType=CT.tolist(),
           C=enc16(stack('a', 'C'), 1000), note='body frame: +x = tail end, -x = head end, +y = limb side; C columns ch0..ch3 (ch0 = axial gradient = package c6; ch2,ch1,ch3 = package c1,c2,c3)')
for st in 'ab':
    L = stack(st, 'L'); D = stack(st, 'D'); E = stack(st, 'E'); MU = stack(st, 'MU'); q = softmax(MU)
    f = np.stack([fpar(X[k], D[k]) for k in range(NT)])
    out[st] = dict(L=enc16(L, 2000), rho=enc16(sgm(L), 20000), D=enc16(D, 20000), E=enc16(E, 20000), f=enc16(f, 20000), q=enc8(np.round(q * 255)))
    print(st, 'mean rho', sgm(L).mean().round(3), 'reporter mean on +y/-y rows', 'ok')
out['C_rows'] = None
write_js('body2100', out)
# ---------------- published 8-cell model: canonical-clock Octave oracle
m = sio.loadmat(f'{MORPH}/m2a_audit_and_library/data/part0/direct_primary_0000.mat', squeeze_me=True); P = m['positions']; NB = 64
Xo = np.stack([P[0::2, :NB], P[1::2, :NB]], -1).transpose(1, 0, 2)       # (bins,8,2)
tgt = sio.loadmat(f'{MORPH}/m0b_reference_port/data/oracle_traces/vanilla8_N32_seed0.mat', squeeze_me=True); TX = tgt['target_x'].T; TS = tgt['target_s'].T
# align final frame to target (Hungarian + rotation search, proper rotations only), assign cells to places
Xall = np.stack([P[0::2, :], P[1::2, :]], -1).transpose(1, 0, 2); Xf = Xall[-1]; best = (1e9, None, None)
for th in np.linspace(0, 2 * np.pi, 721):
    c, s = np.cos(th), np.sin(th); Rr = np.array([[c, -s], [s, c]]); Y = (Xf - Xf.mean(0)) @ Rr.T; Cm = np.linalg.norm(Y[:, None] - (TX - TX.mean(0))[None], axis=-1); r, cc = linear_sum_assignment(Cm)
    if Cm[r, cc].mean() < best[0]: best = (Cm[r, cc].mean(), Rr, cc)
_, Rr, place8 = best; print('oracle final-frame alignment rms', round(best[0], 3))
# types: group places by their secretion code; order groups front->back along x
codes = {}
for k in range(8): codes.setdefault(tuple(TS[k]), []).append(k)
order = sorted(codes.items(), key=lambda kv: np.mean([TX[k, 0] for k in kv[1]])); tmap = {}
for gi, (cd, ks) in enumerate(order):
    for k in ks: tmap[k] = gi + 1
types8 = [tmap[place8[i]] for i in range(8)]
Xo2 = np.stack([(Xo[b] - Xf.mean(0)) @ Rr.T for b in range(NB)])
print('final (bin 512) positions in body frame', np.round((Xf - Xf.mean(0)) @ Rr.T, 2).tolist())
print('8-cell type groups (front->back):', [(cd, ks) for cd, ks in order], 'cell types', types8)
write_js('oracle8', dict(T=NB, X=enc16(Xo2, 1000), types=types8, target=(TX - TX.mean(0)).tolist(), source='m2a_audit_and_library/data/part0/direct_primary_0000.mat (Octave oracle, canonical clock T_dev=32), bins 1-64; types from target_s grouped front->back'))
