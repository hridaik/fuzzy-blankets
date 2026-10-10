"""analysis helpers v3"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine3 import *
from an2 import classify_shape, orbits
PI_C, PI_L = float(np.e), float(np.e ** 3)
def summarize3(eng, st):
    tm = eng.tm; X, C, MU, L, D, E = [np.array(a) for a in st]
    q = np.array(jax.nn.softmax(jnp.array(MU), axis=1)); orb = orbits(tm, PI_C, PI_L); no = orb.max() + 1; O = np.zeros((no, tm.S)); O[orb, np.arange(tm.S)] = 1; qo = q @ O.T
    okc = bool((np.bincount(qo.argmax(1), minlength=no) == np.bincount(orb, minlength=no)).all()); lab, dL, dR = classify_shape(tm, X, C); rho = 1 / (1 + np.exp(-L))
    return dict(label=lab, dL=dL, orbit_complete=okc, min_orbit_bel=float(qo.max(1).min()), mean_rho=float(rho.mean()), min_rho=float(rho.min()), max_rho=float(rho.max()), mean_l=float(L.mean()), std_l=float(L.std()))
