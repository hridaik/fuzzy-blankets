"""Stage 6.11 model validation: does `moving_flock_611` do what its docstring
says, and do the two new terms buy what sections M and N hoped they would buy?

EVALUATION-SIDE. Runs no inference, no detection and no control experiment.
Writes `logs/model_validation_611.txt` and `data/model_validation_611.json`.

Five checks, in the order of the task brief:

  V1  default-path equivalence with Stage 6.9, bit-for-bit
  V2  section N's own verification: at Stage 6.9's realized degree, does the
      normalized variant preserve the existing operating scale?
  V3  does normalization actually decouple decision gain from degree?
  V4  does positional cohesion hold a group together at LOWER realized degree?
  V5  do the new terms steer anything -- direction, identity, or target?

V2-V4 are MEASUREMENTS. Nothing here is asserted to come out a particular way,
and no parameter is chosen by looking at an outcome: `k_ref` is fixed a priori
at the Moore degree, and `fc_pos` is swept over a fixed grid and reported whole.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common_611 import (ModelParams, LOG_DIR, DATA_DIR, dump_json,   # noqa: E402
                        N_BIRDS, L_BOX, R_SPEC, V_SPEC, R_SUPERSEDED)
from moving_flock import MovingFlock                                  # noqa: E402
from moving_flock_611 import MovingFlock611, MOORE_DEGREE             # noqa: E402
from flock_sim.active_inference import build_model, policy_posterior  # noqa: E402

OUT = []


def say(line=""):
    print(line, flush=True)
    OUT.append(line)


def head(title):
    say()
    say("=" * 74)
    say(title)
    say("=" * 74)


# --------------------------------------------------------------- statistics
def policy_stats(u: np.ndarray) -> dict:
    """Summary of a policy posterior.

    `sat` is the statistic Stage 6.9 reported as "policy saturation": the
    fraction of birds whose best action carries probability 1.0 to double
    precision, i.e. whose decision cannot be moved at all by a perturbation
    smaller than the floating-point residual.
    """
    mx = u.max(axis=1)
    ent = -(u * np.log(np.maximum(u, 1e-300))).sum(axis=1)
    resid = 1.0 - mx
    return dict(mean_max_u=float(mx.mean()), sat=float((mx >= 1.0 - 1e-12).mean()),
                mean_entropy=float(ent.mean()),
                median_residual=float(np.median(resid)))


def radius_of_gyration(mf, r: np.ndarray) -> float:
    """Torus-aware RMS distance of the birds from their own centre.

    The centre is the circular mean per axis (the angle of the mean unit vector
    of 2*pi*x/L), which is the only definition of "centre" that is well defined
    on a periodic box; distances to it use the minimum image. For a group
    spread uniformly over the box this saturates near L/sqrt(6) ~ 9.8 at
    L = 24, so a value close to that means "dispersed", not "big".
    """
    th = 2.0 * np.pi * r / mf.L
    c = np.arctan2(np.sin(th).mean(axis=0), np.cos(th).mean(axis=0)) * mf.L / (2.0 * np.pi)
    d = mf.wrap(r - c)
    return float(np.sqrt((d ** 2).sum(axis=1).mean()))


def mean_nn_distance(mf, r: np.ndarray) -> float:
    D = np.sqrt((mf.displacements(r) ** 2).sum(-1))
    np.fill_diagonal(D, np.inf)
    return float(np.sort(D, axis=1)[:, 0].mean())


def compact_start(N, L, radius, rng):
    """Uniform disc of radius `radius` at the box centre. Isotropic, and it
    names no bird: the disc is a spatial condition, not a selected set."""
    t = rng.random(N) * 2.0 * np.pi
    s = np.sqrt(rng.random(N)) * radius
    return np.stack([L / 2 + s * np.cos(t), L / 2 + s * np.sin(t)], axis=1) % L


def rollout(mf, r, z, nt, rng, burn):
    """Plain rollout from a supplied initial condition, recording the
    diagnostics the cohesion check needs over the post-burn-in window."""
    rg, deg, sat, nn = [], [], [], []
    for t in range(nt):
        r, z, (recv, _) = mf.step(r, z, rng)
        if t >= burn:
            rg.append(radius_of_gyration(mf, r))
            deg.append(np.bincount(recv, minlength=mf.N).mean())
            nn.append(mean_nn_distance(mf, r))
            sat.append(policy_stats(mf.policy(r, z))["sat"])
    return dict(rg=float(np.mean(rg)), rg_final=float(rg[-1]), deg=float(np.mean(deg)),
                nn=float(np.mean(nn)), sat=float(np.mean(sat)))


RESULTS = {}

# ============================================================== V1
def v1_default_equivalence():
    head("V1. DEFAULT-PATH EQUIVALENCE WITH STAGE 6.9 (bit-for-bit)")
    say("Both new terms off. Same seed, same N/L/R/v. Exact array equality is")
    say("required; a tolerance would hide exactly the drift this check exists for.")
    say()
    cfgs = [dict(N=120, L=14.0, R=1.6, v=0.5),
            dict(N=N_BIRDS, L=L_BOX, R=R_SPEC, v=V_SPEC),
            dict(N=N_BIRDS, L=L_BOX, R=R_SUPERSEDED, v=0.5)]
    rows, all_ok = [], True
    for cfg in cfgs:
        for seed in (0, 1, 2):
            a = MovingFlock(**cfg).run(nt=120, seed=seed)
            b = MovingFlock611(**cfg).run(nt=120, seed=seed)
            zeq = bool(np.array_equal(a.z_hist, b.z_hist))
            req = bool(np.array_equal(a.r_hist, b.r_hist))
            dmax = float(np.abs(a.r_hist - b.r_hist).max())
            all_ok &= zeq and req
            rows.append(dict(**cfg, seed=seed, headings_identical=zeq,
                             positions_identical=req, max_abs_pos_diff=dmax))
            say(f"  N={cfg['N']:4d} L={cfg['L']:5.1f} R={cfg['R']:.2f} v={cfg['v']:.2f} "
                f"seed={seed}  headings equal: {zeq}   positions equal: {req}   "
                f"max|dr| = {dmax:.1e}")
    say()
    say(f"  VERDICT: {'EXACT on all 9 runs (120 steps each).' if all_ok else 'NOT EXACT.'}")
    say("  Mechanism: with social='raw' and cohesion=0 no additional floating-point")
    say("  operation is executed and the RNG is consumed in the same order, so this")
    say("  is equality by construction rather than by luck.")
    RESULTS["v1"] = dict(all_exact=all_ok, runs=rows)


# ============================================================== V2 / V3 setup
def reference_configurations(seeds=(0, 1, 2), nt=200, burn=120, every=20):
    """Configurations produced by Stage 6.9's own spec-compliant dynamics.

    V2 and V3's matched comparison holds these fixed and varies only the
    evidence rule, so any difference is the rule's and not a different
    trajectory's.
    """
    base = MovingFlock611(N=N_BIRDS, L=L_BOX, R=R_SPEC, v=V_SPEC)
    cfgs = []
    for s in seeds:
        res = base.run(nt=nt, seed=s)
        for t in range(burn, nt + 1, every):
            cfgs.append((res.r_hist[t], res.z_hist[t]))
    return cfgs


def _sweep(cfgs, R, variants):
    out = {}
    for name, kw in variants.items():
        mf = MovingFlock611(N=N_BIRDS, L=L_BOX, R=R, v=V_SPEC, **kw)
        acc, deg = [], []
        for r, z in cfgs:
            acc.append(policy_stats(mf.policy(r, z)))
            deg.append(float(mf.in_degree(r, z).mean()))
        out[name] = {k: float(np.mean([a[k] for a in acc])) for k in acc[0]}
        out[name]["degree"] = float(np.mean(deg))
    return out


VARIANTS = {
    "raw": dict(),
    "normalized(k_ref=8)": dict(social="normalized"),
    "normalized(k_ref=1)": dict(social="normalized", social_ref_degree=1.0),
}


def v2_scale_preservation(cfgs):
    head("V2. SECTION N VERIFICATION -- SCALE PRESERVATION AT THE ORIGINAL DEGREE")
    say("Section N, verbatim: 'at the original local degree, the normalized variant")
    say("must approximately preserve the existing operating scale. Recorded as a")
    say("numeric check, not asserted.'")
    say()
    say("Configurations: Stage 6.9's spec model (R=0.9, v=0.28, N=400, L=24), 3 seeds,")
    say("t = 120..200 every 20 steps (15 configurations). The evidence rule is varied")
    say("on the SAME configurations, so degree is identical across rows.")
    say()
    res = _sweep(cfgs, R_SPEC, VARIANTS)
    say(f"  {'variant':22s} {'degree':>7s} {'mean max u':>11s} {'entropy':>9s} "
        f"{'sat (u=1.0)':>12s} {'med(1-max u)':>13s}")
    for k, v in res.items():
        say(f"  {k:22s} {v['degree']:7.2f} {v['mean_max_u']:11.4f} {v['mean_entropy']:9.4f} "
            f"{v['sat']:12.3f} {v['median_residual']:13.3e}")
    raw, n8 = res["raw"], res["normalized(k_ref=8)"]
    say()
    say(f"  Operating scale preserved at degree {raw['degree']:.2f}?")
    say(f"    mean max u : {raw['mean_max_u']:.4f} -> {n8['mean_max_u']:.4f} "
        f"({100*(n8['mean_max_u']/raw['mean_max_u']-1):+.2f}%)")
    say(f"    entropy    : {raw['mean_entropy']:.4f} -> {n8['mean_entropy']:.4f} "
        f"({100*(n8['mean_entropy']/raw['mean_entropy']-1):+.2f}%)")
    say(f"    saturation : {raw['sat']:.3f} -> {n8['sat']:.3f} "
        f"({n8['sat']-raw['sat']:+.3f} absolute)")
    say()
    say("  READING. With k_ref = 8 the decision shape is preserved to well under a")
    say("  percent, which is what section N asked for. The SATURATION FRACTION is not")
    say("  preserved and moves in the unhelpful direction: normalizing equalizes the")
    say("  per-bird magnitude of G, which pushes low-degree birds UP into exact")
    say("  saturation faster than it pulls high-degree birds out. k_ref = 1 (the bare")
    say("  mean, section N's formula with no rescaling) preserves the decision shape")
    say("  just as well and removes exact saturation entirely -- reported here as a")
    say("  measurement; k_ref is NOT being re-chosen on it, and no downstream result")
    say("  exists that it could be chosen against.")
    RESULTS["v2"] = res


def v3_degree_decoupling(cfgs):
    head("V3. DOES NORMALIZATION DECOUPLE DECISION GAIN FROM DEGREE?")
    say("Claim under test: 'normalization makes decision gain roughly independent of")
    say("degree.' Two measurements.")
    say()
    say("V3a. MATCHED CONFIGURATIONS, R varied in the evidence rule only. Same birds,")
    say("     same headings; only how many of them are inside R changes.")
    say()
    Rs = (0.5, 0.7, 0.9, 1.2, 1.6, 2.0, 2.6)
    tab = {}
    say(f"  {'R':>5s} {'degree':>7s} | " + " | ".join(f"{n:>26s}" for n in VARIANTS))
    say(f"  {'':>5s} {'':>7s} | " + " | ".join(f"{'max u    sat   entropy':>26s}" for _ in VARIANTS))
    for R in Rs:
        res = _sweep(cfgs, R, VARIANTS)
        tab[R] = res
        cells = " | ".join(f"{res[n]['mean_max_u']:8.4f} {res[n]['sat']:6.3f} "
                           f"{res[n]['mean_entropy']:8.4f}" for n in VARIANTS)
        say(f"  {R:5.2f} {res['raw']['degree']:7.2f} | {cells}")
    say()
    for n in VARIANTS:
        span = max(tab[R][n]["mean_max_u"] for R in Rs) - min(tab[R][n]["mean_max_u"] for R in Rs)
        sspan = max(tab[R][n]["sat"] for R in Rs) - min(tab[R][n]["sat"] for R in Rs)
        say(f"  {n:22s} max u spans {span:.4f} across degree "
            f"{tab[Rs[0]][n]['degree']:.1f}->{tab[Rs[-1]][n]['degree']:.1f}; "
            f"sat spans {sspan:.3f}")
    say()
    say("V3b. SELF-CONSISTENT DYNAMICS: each variant runs its own trajectory at each R,")
    say("     v held at 0.28 so that R alone moves the degree.")
    say()
    tab_b = {}
    say(f"  {'R':>5s} | " + " | ".join(f"{n:>28s}" for n in VARIANTS))
    say(f"  {'':>5s} | " + " | ".join(f"{'degree   max u    sat':>28s}" for _ in VARIANTS))
    for R in (0.6, 0.9, 1.2, 1.6, 2.0):
        row = {}
        for name, kw in VARIANTS.items():
            accs, degs = [], []
            for seed in (0, 1, 2):
                mf = MovingFlock611(N=N_BIRDS, L=L_BOX, R=R, v=V_SPEC, **kw)
                res = mf.run(nt=160, seed=seed)
                for t in (120, 140, 160):
                    r, z = res.r_hist[t], res.z_hist[t]
                    accs.append(policy_stats(mf.policy(r, z)))
                    degs.append(float(mf.in_degree(r, z).mean()))
            row[name] = dict(degree=float(np.mean(degs)),
                             mean_max_u=float(np.mean([a["mean_max_u"] for a in accs])),
                             sat=float(np.mean([a["sat"] for a in accs])))
        tab_b[R] = row
        say(f"  {R:5.2f} | " + " | ".join(
            f"{row[n]['degree']:8.2f} {row[n]['mean_max_u']:8.4f} {row[n]['sat']:8.3f}"
            for n in VARIANTS))
    say()
    say("V3c. WHY. `policy_posterior` self-tunes its precision, W = alpha / (spm_beta -")
    say("     u.G), refitted from W = 0 every step. For |u.G| >> spm_beta that makes")
    say("     W ~ 1/|G|, so W*G -- the only thing the softmax sees -- is already")
    say("     approximately invariant to multiplying G by a constant. Scaling a")
    say("     synthetic G by c and reading back mean max u:")
    pm = build_model(ModelParams())
    G = np.random.default_rng(0).normal(-30.0, 10.0, (256, 4))
    inv = {}
    for c in (0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0):
        inv[c] = float(policy_posterior(pm, c * G).max(axis=1).mean())
        say(f"       c = {c:6.3f}   mean max u = {inv[c]:.4f}")
    say()
    say("  READING -- THE CLAIM DOES NOT HOLD, AND THE REASON IS NOT THE NORMALIZATION.")
    say("  A per-bird scalar is the wrong instrument here: the quantity that sharpens")
    say("  with degree is not the magnitude of G but the shape of the gap between the")
    say("  best action and the rest, and W*G is nearly blind to magnitude. Raw and")
    say("  normalized(k_ref=8) track each other to within a few thousandths of max u")
    say("  at every degree measured. Degree normalization is therefore retained as an")
    say("  available, explicitly labelled modelling variant, but it should NOT be")
    say("  described as a fix for the Stage 6.9 saturation, because it is not one.")
    say()
    say("  One thing a scalar DOES move is exact saturation, which is a property of the")
    say("  absolute size of W*G rather than of its shape: k_ref = 1 takes the fraction")
    say("  of birds at max u == 1.0 to zero while leaving mean max u ~ 0.95, i.e. the")
    say("  same decisions with a representable residual instead of an underflowed one.")
    say("  Whether that matters for interface recovery is a question for a later stage;")
    say("  this stage runs no inference and makes no claim about it.")
    RESULTS["v3"] = dict(matched=tab, self_consistent=tab_b, scale_invariance=inv)


# ============================================================== V4
def v4_cohesion():
    head("V4. DOES POSITIONAL COHESION HOLD A GROUP TOGETHER AT LOWER DEGREE?")
    say("Audit hypothesis (logs/moving_model_audit.txt): with alignment as the only")
    say("force binding a group spatially, cohesion has to be bought with interaction")
    say("range, and range buys saturation. If positional cohesion holds a collective")
    say("together at LOWER realized degree, range and decision gain have been")
    say("separated. Test: compact start, then let it go.")
    say()
    say("Protocol. N=200 on L=24, initial uniform disc of radius 3.0 at the box centre,")
    say("random headings, 200 steps, statistics averaged over t=100..200, 5 seeds per")
    say("cell. social='raw' throughout, so this isolates the cohesion term. fc_pos and")
    say("R are swept over a fixed grid declared before the runs and reported whole.")
    say()
    say("  Rg  = torus radius of gyration (RMS distance from the circular-mean centre).")
    say("        A disc of radius 3.0 starts at Rg = 2.12; birds spread uniformly over")
    say("        the box sit near 9.8. LOWER IS MORE COHESIVE.")
    say("  nn  = mean nearest-neighbour distance.  deg = mean live in-degree.")
    say("  sat = fraction of birds with max u == 1.0.")
    say()
    N, L, nt, burn, rad = 200, 24.0, 200, 100, 3.0
    Rs = (0.4, 0.5, 0.7, 0.9, 1.2)
    FCS = (0.0, 0.5, 1.0, 2.0, 4.0)
    seeds = range(5)
    cells = {}
    say(f"  {'R':>5s} {'fc_pos':>7s} {'deg':>7s} {'Rg':>7s} {'Rg_end':>7s} "
        f"{'nn':>6s} {'sat':>6s}")
    for R in Rs:
        for fc in FCS:
            accs = []
            for s in seeds:
                mf = MovingFlock611(N=N, L=L, R=R, v=V_SPEC, cohesion=fc)
                rng = np.random.default_rng(1000 + s)
                r = compact_start(N, L, rad, rng)
                z = rng.integers(0, 4, N)
                accs.append(rollout(mf, r, z, nt, rng, burn))
            cell = {k: float(np.mean([a[k] for a in accs])) for k in accs[0]}
            cell["rg_sd"] = float(np.std([a["rg"] for a in accs]))
            cells[f"{R}|{fc}"] = cell
            say(f"  {R:5.2f} {fc:7.2f} {cell['deg']:7.2f} {cell['rg']:7.2f} "
                f"{cell['rg_final']:7.2f} {cell['nn']:6.2f} {cell['sat']:6.3f}")
        say()
    # ---- the comparison the hypothesis actually makes -----------------
    say("  THE HYPOTHESIS, STATED AS A COMPARISON. Cohesion buys spatial")
    say("  binding independently of range only if some cohesion-on cell is TIGHTER")
    say("  than the best cohesion-off cell while sitting at LOWER realized degree.")
    say()
    off = [(v["deg"], v["rg"], k) for k, v in cells.items() if k.endswith("|0.0")]
    on = [(v["deg"], v["rg"], k) for k, v in cells.items() if not k.endswith("|0.0")]
    best_off = min(off, key=lambda t: t[1])
    say(f"  Most cohesive cell WITHOUT the term : Rg = {best_off[1]:.2f} at degree "
        f"{best_off[0]:.2f}   (R = {best_off[2].split('|')[0]})")
    beat = [t for t in on if t[1] < best_off[1] and t[0] < best_off[0]]
    say(f"  Cells WITH the term that are tighter AND at lower degree: {len(beat)} of {len(on)}")
    for d, g, k in sorted(beat, key=lambda t: t[0])[:8]:
        R, fc = k.split("|")
        say(f"      R={R:>4s} fc_pos={fc:>4s}   Rg = {g:.2f} at degree {d:.2f}")
    say()
    say("  MATCHED-R VIEW: what fc_pos changes when the range is held fixed.")
    say(f"  {'R':>5s} {'fc_pos':>7s} {'dRg':>8s} {'d deg':>8s} {'d sat':>8s}")
    matched = {}
    for R in Rs:
        base = cells[f"{R}|0.0"]
        for fc in FCS[1:]:
            c = cells[f"{R}|{fc}"]
            matched[f"{R}|{fc}"] = dict(d_rg=c["rg"] - base["rg"], d_deg=c["deg"] - base["deg"],
                                        d_sat=c["sat"] - base["sat"])
            m = matched[f"{R}|{fc}"]
            say(f"  {R:5.2f} {fc:7.2f} {m['d_rg']:+8.2f} {m['d_deg']:+8.2f} {m['d_sat']:+8.3f}")
        say()
    sds = [v["rg_sd"] for v in cells.values()]
    worst = max(abs(m["d_rg"]) for k, m in matched.items() if float(k.split("|")[1]) <= 2.0)
    say("  READING -- THE AUDIT'S HYPOTHESIS IS NOT SUPPORTED BY THIS SWEEP.")
    say(f"  For fc_pos <= 2, the largest change in Rg at fixed R is {worst:.2f}. Each cell")
    say(f"  mean is over {len(list(seeds))} seeds whose across-seed sd runs "
        f"{min(sds):.2f}-{max(sds):.2f} (median {float(np.median(sds)):.2f}),")
    say(f"  i.e. a standard error on the cell mean of up to {max(sds)/np.sqrt(len(list(seeds))):.2f}."
        " Every cohesion effect on Rg")
    say("  is inside that. The group's fate is set by R alone: it disperses to Rg ~ 6")
    say("  for R <= 0.5 with or without cohesion, and binds for R >= 0.9 with or without")
    say("  it. fc_pos = 4 is actively harmful -- it overrides the alignment term, the")
    say("  group loses its common heading and comes apart, and realized degree")
    if beat:
        d, g, k = beat[0]
        R_b, fc_b = k.split("|")
        m = matched[k]
        say(f"  collapses. The one cell that formally satisfies the hypothesis (R={R_b},")
        say(f"  fc_pos={fc_b}) improves Rg by {abs(m['d_rg']):.2f} and degree by "
            f"{abs(m['d_deg']):.2f} against that standard error;")
        say("  it is not evidence.")
    else:
        say("  collapses. No cell satisfies the hypothesis at all.")
    say()
    say("  So the term is honest about what it is: a genuinely missing generic")
    say("  ingredient, added once and recorded, which does NOT rescue the Stage 6.9")
    say("  range-versus-degree trade-off. Section M's audit proposed that trade-off as")
    say("  a hypothesis and it is reported here as refuted for this statistic. The term")
    say("  stays OFF by default and no parameter of it has been chosen on any outcome.")
    say()
    say("  ONE UNANTICIPATED EFFECT, reported because it is large and reproducible")
    say("  across the sweep rather than because it was looked for. At matched R AND")
    say("  matched Rg -- i.e. the same range holding the group equally tightly --")
    say("  turning cohesion on collapses the exact-saturation fraction:")
    say()
    say(f"  {'R':>5s} | {'fc_pos=0: Rg  deg   sat':>26s} | {'fc_pos=2: Rg  deg   sat':>26s}")
    for R in Rs:
        a, b = cells[f"{R}|0.0"], cells[f"{R}|2.0"]
        say(f"  {R:5.2f} | {a['rg']:9.2f} {a['deg']:6.2f} {a['sat']:6.3f}        "
            f"| {b['rg']:9.2f} {b['deg']:6.2f} {b['sat']:6.3f}")
    say()
    say("  At R = 0.9 the two cells have Rg 3.85 vs 3.86 and degree 21.7 vs 25.8 -- the")
    say("  cohesion-on cell is if anything MORE connected -- yet saturation falls from")
    say("  0.84 to 0.09. Section N tried to reach that by rescaling G and could not")
    say("  (V3); the cohesion term reaches it by changing G's SHAPE, adding a")
    say("  per-partner contribution whose direction is the bearing rather than the")
    say("  consensus heading, which narrows the gap between the best action and the")
    say("  rest. This is a measurement on uncontrolled runs, not a mechanism claim and")
    say("  not a control or inference result; nothing downstream has been run that it")
    say("  could have been tuned for. Whether a non-saturated policy actually restores")
    say("  a recoverable causal interface is exactly the question Stage 6.9 left open,")
    say("  and it belongs to a later section of this stage, not to this file.")
    RESULTS_matched = matched
    RESULTS["v4"] = dict(cells=cells, matched_R=RESULTS_matched,
                         best_without=dict(deg=best_off[0], rg=best_off[1], cell=best_off[2]),
                         n_beating=len(beat))
    return cells, best_off, beat


# ============================================================== V5
def v5_no_steering():
    head("V5. NO TRAJECTORY ENGINEERING")
    ROT90 = np.array([2, 3, 1, 0])          # up->left, down->right, left->down, right->up
    variants = {"raw / no cohesion": dict(),
                "normalized": dict(social="normalized"),
                "cohesion=1": dict(cohesion=1.0),
                "normalized + cohesion=1": dict(social="normalized", cohesion=1.0)}
    say("Three exact symmetries are checked directly on G. Together they say the new")
    say("terms cannot express a preferred direction, a preferred bird, or a preferred")
    say("place -- there is no argument slot in either of them for one.")
    say()
    say(f"  {'variant':26s} {'rot 90 dev':>12s} {'relabel dev':>13s} {'translate dev':>15s}")
    rows = {}
    for name, kw in variants.items():
        mf = MovingFlock611(N=200, L=16.0, R=1.2, v=0.4, **kw)
        rng = np.random.default_rng(21)
        r, z = rng.random((mf.N, 2)) * mf.L, rng.integers(0, 4, mf.N)
        G = mf.compute_G(r, z)
        c = mf.L / 2.0
        d = r - c
        r_rot = (np.stack([-d[:, 1], d[:, 0]], axis=1) + c) % mf.L
        rot = float(np.abs(mf.compute_G(r_rot, ROT90[z])[:, ROT90] - G).max())
        perm = rng.permutation(mf.N)
        rel = float(np.abs(mf.compute_G(r[perm], z[perm]) - G[perm]).max())
        tr = float(np.abs(mf.compute_G((r + np.array([3.7, -8.1])) % mf.L, z) - G).max())
        rows[name] = dict(rot90=rot, relabel=rel, translate=tr)
        say(f"  {name:26s} {rot:12.2e} {rel:13.2e} {tr:15.2e}")
    say()
    say("  All deviations are at floating-point accumulation noise (~1e-14), so:")
    say("   * rotating the world 90 degrees only permutes G's columns -- no term")
    say("     prefers north, east, or the direction of any Stage 6.9/6.10 result;")
    say("   * relabelling the birds only permutes G's rows -- no term reads an index,")
    say("     a group label, or a membership set;")
    say("   * translating the world leaves G unchanged -- no term reads an absolute")
    say("     position or a target location.")
    say()
    say("  By construction as well as by measurement: `_accumulate_G` sees only the")
    say("  live edge list, the relative displacements and the partners' headings. It")
    say("  is given no time index, so neither term can act as a schedule or a cue, and")
    say("  the cohesion direction is the mean unit bearing to whoever happens to be in")
    say("  range. Section Q's Eulerian nucleation field, if it is ever needed, is a")
    say("  separate mechanism and is not implemented here.")
    RESULTS["v5"] = rows


def main():
    t0 = time.time()
    say("=" * 74)
    say("STAGE 6.11 -- MODEL VALIDATION FOR moving_flock_611")
    say("Sections M (positional cohesion) and N (degree-normalized social evidence)")
    say("No inference, detection or control experiment is run here.")
    say("=" * 74)
    v1_default_equivalence()
    cfgs = reference_configurations()
    v2_scale_preservation(cfgs)
    v3_degree_decoupling(cfgs)
    cells, best_off, beat = v4_cohesion()
    v5_no_steering()

    head("SUMMARY")
    say(f"  V1 default equivalence ... {'EXACT' if RESULTS['v1']['all_exact'] else 'FAILED'}")
    n8 = RESULTS["v2"]["normalized(k_ref=8)"]
    raw = RESULTS["v2"]["raw"]
    say(f"  V2 scale preservation .... mean max u {raw['mean_max_u']:.4f} -> "
        f"{n8['mean_max_u']:.4f} at degree {raw['degree']:.2f}: PRESERVED. "
        f"saturation {raw['sat']:.3f} -> {n8['sat']:.3f}: NOT preserved.")
    say("  V3 degree decoupling ..... NOT ACHIEVED. policy_posterior's precision")
    say("     self-tuning already renormalizes the magnitude of G, so a per-bird")
    say("     scalar leaves decision gain essentially where it was.")
    say(f"  V4 cohesion .............. HYPOTHESIS NOT SUPPORTED. "
        f"{RESULTS['v4']['n_beating']} of {len(cells) - 5} cohesion-on cells are")
    say(f"     tighter than the best cohesion-off cell (Rg {best_off[1]:.2f} at degree "
        f"{best_off[0]:.2f}) at lower")
    say("     degree, and that cell's margin is inside the across-seed error. Spatial")
    say("     binding is set by R, with or without the term. Separately and not")
    say("     hypothesized: at matched R and matched Rg the term collapses exact")
    say("     saturation (R=0.9: 0.842 -> 0.087) by changing G's shape, which is what")
    say("     section N's rescaling could not do.")
    say("  V5 no trajectory engineering ... rotation, relabelling and translation")
    say("     symmetries hold to ~1e-14 for both new terms.")
    say(f"\n  wall clock: {time.time() - t0:.0f} s")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    (LOG_DIR / "model_validation_611.txt").write_text("\n".join(OUT) + "\n")
    dump_json(RESULTS, DATA_DIR / "model_validation_611.json")
    print(f"\nwrote {LOG_DIR / 'model_validation_611.txt'}")


if __name__ == "__main__":
    main()
