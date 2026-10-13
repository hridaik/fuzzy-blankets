"""Declared constants and the per-dish hidden-parameter population (v4). All constants fixed BEFORE measuring (COMPUTE_PLAN.md)."""
import numpy as np
from template4 import make_template4
R_ = 0.05; SIG_H = 0.4; BETA_E = 4.0; PI_LAM = float(np.e ** 3); G_MIN = 4 * R_ * 1.5
THETA = 20.0   # V1 failed at 30 (14/16 completions) -> declared fallback 20
NOISE = dict(sig_x=.02, sig_c=.02, sig_mu=.02, sig_d=.02, sig_e=.02)
KG_RANGE = (1.5, 4.0); GF_RANGE = (1 / 1.5, 1.5)          # LogUniform ranges (V5 widenings: (1.2,5), (1/2,2))
KG_MED = float(np.sqrt(1.5 * 4.0))                          # median-coupling dish kappa_g = 2.449
VARIANTS = {'phi0': 0.0, 'phi04': 0.4, 'phi08': 0.8}; PRIMARY = 'phi04'

def D_k(tm):
    return 0.5 * PI_LAM * ((tm.LamA - tm.LamB) ** 2).sum(0)

def alpha_for(phi_max, tm=None):
    tm = tm or make_template4(THETA); return float(phi_max * G_MIN / (BETA_E * D_k(tm).max()))

def sample_dish(seed, kg_range=KG_RANGE, gf_range=GF_RANGE):
    rng = np.random.default_rng(910_000 + int(seed)); kg = float(np.exp(rng.uniform(np.log(kg_range[0]), np.log(kg_range[1])))); gf = float(np.exp(rng.uniform(np.log(gf_range[0]), np.log(gf_range[1]))))
    return dict(seed=int(seed), kappa_g=kg, g=4 * R_ * kg, gamma_factor=gf)

def median_dish(): return dict(seed=-1, kappa_g=KG_MED, g=4 * R_ * KG_MED, gamma_factor=1.0)
