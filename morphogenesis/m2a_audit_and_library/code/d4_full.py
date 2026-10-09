"""D4 full run. Declared design (see COMPUTE_PLAN.md): brackets from the D4 pilot; displacement single-cell directions use a 4-point coarse grid (pilot: no effect in
any scanned amplitude for the two tested directions), all other sets a 7-point grid; 1% log-bisection on both thresholds."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from d4_dirs import *
import scipy.io as sio
def eig_dirs():
    J = sio.loadmat(path("d1", "J_class0"))["J"][:, :, 1]; w, V = np.linalg.eig(J); o = np.argsort(-np.abs(w)); V = V[:, o]
    pos, bel = [], []
    k = 0
    while len(bel) < 5:
        v = V[:, k]; k += 1
        if abs(v.imag).max() > 1e-6 * abs(v).max() and (k > 1 and abs(w[o][k - 2].imag) > 1e-9 and np.isclose(w[o][k - 2], np.conj(w[o][k - 1]))): continue
        v = v.real if abs(v.imag).max() < 1e-6 * abs(v).max() else v.real
        pv = v[128:144]; bv = v[:64]
        pos.append(pv / np.linalg.norm(pv)); bel.append(bv / np.linalg.norm(bv))
    return pos, bel
def specs():
    pos, bel = eig_dirs(); S = []
    S += dirs_global() + dirs_region() + dirs_pulse_single()
    S += dirs_body(pos) + [dict(id=f"bodyv_eig{k}", kind="bodyv", u=b.tolist(), br=BR_DISP) for k, b in enumerate(bel)]
    S += [dict(s, grid_n=4) for s in dirs_disp1()]
    return S
if __name__ == "__main__":
    S = specs(); W = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    S = [s for s in S if not os.path.exists(os.path.join(DATA, "v2", "d4", f"dir_{s['id']}.json"))]
    print(len(S), "directions"); run_tasks([(job, (s,)) for s in S], workers=W, label="D4")
