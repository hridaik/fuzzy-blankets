"""Testbed templates (T2).  Four cell types as in the vanilla model: codes [1, b2, b3, b4]
   type1=(1,1,1,0)  type2=(1,1,0,0)  type3=(1,0,1,0)  type4=(1,0,0,1)    (vanilla T-values 1,2,3,4)."""
import numpy as np
from engine import make_template

TYPE_CODES = {1: (1, 1, 1, 0), 2: (1, 1, 0, 0), 3: (1, 0, 1, 0), 4: (1, 0, 0, 1)}
TYPE_NAMES = {1: "head (red)", 2: "trunk (blue)", 3: "limb (green)", 4: "tail (gold)"}

GRADED = True     # channel 0 ("existence/axial") carries a graded axial-position morphogen: 0.3 (anterior end) .. 2.3 (posterior end)
AX_RANGE = (-4.0, 4.0)

def axial_level(xs):
    return 0.3 + 2.0 * (np.asarray(xs, float) - AX_RANGE[0]) / (AX_RANGE[1] - AX_RANGE[0])

def codes_from_types(types, nm=0, xs=None):
    C = np.array([TYPE_CODES[int(t)] for t in types], float).T          # (4,n)
    if GRADED and xs is not None: C[0] = axial_level(xs)
    if nm: C = np.vstack([C, np.zeros((nm, C.shape[1]))])
    return C

ROW_DX = 0.9

def _rows(sizes, x0=0.0):
    pos = []
    for r, k in enumerate(sizes):
        for j in range(k):
            pos.append((x0 + r * ROW_DX, (j - (k - 1) / 2.0) * 1.0))
    return pos

def body24_planA():
    """compact one-headed body, anterior (x small) -> posterior. rows of cells: head 1,3,4 | body 4,4 | tail 2,2,2,2
    slots 0-7 head (T1), 8-11 trunk (T2: two centre cells per row), 12-15 limbs (T3: outer cells), 16-23 tail (T4)"""
    pos = _rows([1, 3, 4, 4, 4, 2, 2, 2, 2])
    types = [1] * 8
    body = pos[8:16]                              # rows 3 and 4
    trunk = [p for p in body if abs(p[1]) < 1.0]; limb = [p for p in body if abs(p[1]) >= 1.0]
    tail = pos[16:24]
    P = pos[:8] + trunk + limb + tail
    types = [1] * 8 + [2] * 4 + [3] * 4 + [4] * 8
    X = np.array(P, float).T; X[0] -= X[0].mean()
    return X, np.array(types)

def body24_planB():
    """plan B: the 8 tail slots (16-23) are re-coded as a second head (T1) and re-arranged as a mirrored head cap (rows 3,3,2 outward);
    33% of the slots change both colour and position. Slots 0-15 identical to plan A."""
    X, ty = body24_planA(); X = X.copy(); ty = ty.copy()
    xe = X[0, :16].max()
    rear = []
    for r, k in enumerate([3, 3, 2]):
        for j in range(k):
            rear.append((xe + (r + 1) * ROW_DX, (j - (k - 1) / 2.0) * 1.0))
    X[:, 16:24] = np.array(rear, float).T; ty[16:24] = 1
    return X, ty

def chiral24():
    """plan-A geometry with all limb cells (T3) on the +y side: in each limb row the types read (T2,T2,T3,T3) from -y to +y.
    No mirror symmetry -> the shape and its mirror image are distinct enantiomorphs."""
    X, ty = body24_planA(); X = X.copy(); ty = ty.copy()
    trunk = list(range(8, 12)); limb = list(range(12, 16))
    for r in range(2):   # the two body rows: slots (trunk,limb) positions
        pass
    # recode by position: body-row cells sorted by (x, y)
    body_idx = list(range(8, 16)); order = sorted(body_idx, key=lambda i: (round(X[0, i], 6), X[1, i]))
    for r in range(2):
        row = order[4 * r:4 * r + 4]
        for j, i in enumerate(row): ty[i] = 2 if j < 2 else 3
    return X, ty

def make_body(kind, kappa=1.0, kappa_m=0.3, mem_amp=0.25):
    xa = body24_planA()[0][0]          # slot axial coordinate (plan-A geometry) defines the per-slot graded level for every plan
    if kind == "A":
        X, ty = body24_planA(); return make_template(X, codes_from_types(ty, xs=xa), kappa, ty[None])
    if kind == "B":
        X, ty = body24_planB(); return make_template(X, codes_from_types(ty, xs=X[0]), kappa, ty[None])
    if kind == "chiral":
        X, ty = chiral24(); return make_template(X, codes_from_types(ty, xs=xa), kappa, ty[None])
    if kind == "AB":   # two plans + 5th (memory) channel: A secretes none, B secretes 1 at every slot
        XA, tA = body24_planA(); XB, tB = body24_planB()
        CA = codes_from_types(tA, 1, xs=XA[0]); CB = codes_from_types(tB, 1, xs=XB[0]); CB[4] = mem_amp
        kap = np.array([kappa] * 4 + [kappa_m])
        return make_template(np.stack([XA, XB]), np.stack([CA, CB]), kap, np.stack([tA, tB]))
    raise ValueError(kind)

def type_vector(tmpl, plan=0):
    return np.asarray(tmpl.types[plan])


def multiscale(tmpl, kappas):
    """Fix F1: every signal is secreted and sensed at several diffusion lengths. Returns a template with nc = 4*len(kappas) channels
    (row r*4+k has the code of signal k and kernel kappas[r]); first 4 rows are the original (kappas[0])."""
    Cs = np.concatenate([tmpl.Cs[:, :4]] * len(kappas), axis=1)
    kap = np.repeat(np.asarray(kappas, float), 4)
    return make_template(tmpl.Xs, Cs, kap, tmpl.types)
