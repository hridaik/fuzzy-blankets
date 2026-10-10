"""Declared G2 operating point (all knobs within declared ranges)."""
import numpy as np
G1 = dict(beta_E=4.0, k_mu=0.2, pi_c=float(np.e), pi_lam=float(np.e ** 3))          # G1 operating point
MEM0 = dict(pi_d=0.02, pi_psi=0.1, r=0.05, k_h=0.1)                                  # first analytic choice from the spec's design rule (w=1 isolated cell): FAILS G2(b), see MEMORY.md
MEM = dict(pi_d=0.01, pi_psi=0.04, r=0.10, k_h=0.1)                                  # revised after the isolated-cell diagnosis: G_iso(w_k) < 4r for every place
FULL = dict(G1, **MEM)
FULL0 = dict(G1, **MEM0)
MEM_B = dict(pi_d=0.0005, pi_psi=0.002, r=0.10, k_h=2.0)                              # variant VB: same k_h*beta*pi_psi (same evidence per unit dose, same G_iso, G) with 20x smaller pi_psi (20x less position force)
FULL_B = dict(G1, **MEM_B)
DT = 0.0125
def mean_field(tm, P):
    """returns dict of mean-field numbers. morphological evidence for a cell at place k with uniform rho: (1/2)(2rho-1)(pi_c|dC_k|^2 + pi_lam|dLam_k|^2)"""
    kb = P['k_h'] * P['beta_E']; w2 = float((tm.w ** 2).mean())
    dC = ((tm.CL - tm.CR) ** 2).sum(0); dL = ((tm.LamL - tm.LamR) ** 2).sum(0)
    gm = 0.5 * (P['pi_c'] * dC + P['pi_lam'] * dL)          # per-place coefficient of (2rho-1) in Delta_morph
    G1_ = kb * (P['pi_d'] + P['pi_psi']); Gmem = kb * (P['pi_d'] + P['pi_psi'] * w2); Gmorph_k = kb * gm; Gmorph = float(Gmorph_k.mean())
    r = P['r']; out = dict(wbar2=w2, w_min=float(tm.w.min()), w_max=float(tm.w.max()), G1=G1_, G_mem=Gmem, G_morph_mean=Gmorph, G_tot=Gmem + Gmorph, four_r=4 * r, eight_r=8 * r,
                           rule_G1_lt_4r=bool(G1_ < 4 * r), rule_G_ge_8r=bool(Gmem >= 8 * r), Gmorph_per_place=Gmorph_k.tolist())
    def lstar(G):
        return float(2 * np.arccosh(np.sqrt(G / (4 * r)))) if G > 4 * r else 0.0
    def dU(G):
        l = lstar(G); U = lambda x: 2 * r * np.cosh(x) - 2 * G * np.log(np.cosh(x / 2)); return float(U(0.0) - U(l))
    out.update(lstar_mem_only=lstar(Gmem), dU_mem_only=dU(Gmem), lstar_tot=lstar(Gmem + Gmorph), dU_tot=dU(Gmem + Gmorph), lstar_single=lstar(G1_), relax_rate_isolated_pred=2 * r - G1_ / 2)
    out['G_iso_per_place'] = (kb * (P['pi_d'] + P['pi_psi'] * tm.w) ** 2 / (P['pi_d'] + P['pi_psi'])).tolist()   # isolated cell holding place k: d is amplified by (pi_d+pi_psi w_k)/(pi_d+pi_psi)
    out['G_iso_max'] = max(out['G_iso_per_place']); out['G_iso_min'] = min(out['G_iso_per_place'])
    # per-cell memory-only + own morphological
    out['lstar_per_place'] = [lstar(Gmem + g) for g in Gmorph_k]
    return out
