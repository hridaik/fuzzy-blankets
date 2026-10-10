"""Shared helpers of the demo build (white box; reads hidden tiers).  Output: ../data/*.js (global assignments, no fetch)."""
import sys, os, json, base64, numpy as np, pickle
HERE = os.path.dirname(os.path.abspath(__file__)); DEMO = os.path.abspath(os.path.join(HERE, '..')); MORPH = os.path.abspath(os.path.join(DEMO, '..')); V3 = os.path.join(MORPH, 'testbed_v3')
AUD5 = os.path.join(V3, 'audit_t5'); T5 = os.path.join(MORPH, 't5_blind_control'); PKG = os.path.join(MORPH, 'testbed_blind_v3'); SEALED = os.path.join(V3, 'live_sealed_t5')
sys.path.insert(0, os.path.join(V3, 'code')); sys.path.insert(0, os.path.join(V3, '..', 'testbed_v2', 'code')); sys.path.insert(0, os.path.join(AUD5, 'code')); sys.dont_write_bytecode = True
from scipy.optimize import linear_sum_assignment
def enc16(a, scale):
    q = np.clip(np.round(np.asarray(a, float) * scale), -32767, 32767).astype('<i2'); return base64.b64encode(q.tobytes()).decode()
def enc8(a): return base64.b64encode(np.ascontiguousarray(a, dtype='u1').tobytes()).decode()
def write_js(name, obj):
    p = os.path.join(DEMO, 'data', name + '.js'); s = 'window.DATA=window.DATA||{};DATA.' + name + '=' + json.dumps(obj, separators=(',', ':'), default=float) + ';\n'; open(p, 'w').write(s); print('wrote', name, round(len(s) / 1e6, 2), 'MB'); return len(s)
def softmax(M): e = np.exp(M - M.max(-1, keepdims=True)); return e / e.sum(-1, keepdims=True)
_tm = None
def template():
    global _tm
    if _tm is None:
        from engine2 import make_template2; from shape import cell_types
        tm = make_template2(); _tm = (tm, tm.Xs.T.copy(), cell_types(tm.CL))
    return _tm
def frame_map(X, MU):
    """true body frame: cell->place (Hungarian on place beliefs), proper Procrustes template->cells. returns R,tc (template centroid),xc (cell centroid), assign (place index of each cell)"""
    tm, XS, CT = template(); q = softmax(MU); r, c = linear_sum_assignment(-np.log(q + 1e-12)); P = XS[c]
    a = P - P.mean(0); b = X - X.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
    if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
    return R, P.mean(0), X.mean(0), c
def to_body(X, R, tc, xc): return (R.T @ (np.atleast_2d(X) - xc).T).T + tc          # arena -> template(body) coordinates
