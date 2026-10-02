"""Part 2: perturbation-response library (protocol v2). Pulses are raised-cosine bumps of width w = 4 bins (M1 TIMESCALES), applied as
CONTINUATIONS from a saved base state (S_FP: adult fixed point b=320; S_DEV: b = 16, 32, 64, 128 = 0.5, 1, 2, 4 x T_dev) with the matched
unperturbed twin on the same continuation. Channels per cell: POS (x,y offset of the sensed position), SEC (ligand k additionally released
into the field), GAIN (extracellular sensitivity to ligand k x (1+eps))."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *

PULSE_W = 4
WINDOW = 192                 # bins run after the base state (>= ~21 contraction time constants)
ONSET_LAG = 2                # pulse starts 2 bins after the base state
BASES = {"FP": B_ADULT, "D16": 16, "D32": 32, "D64": 64, "D128": 128}
LIB_INDS = [0, 1, 2, 3]      # replaced by the declared IDs (distinct role maps) in p2_declare; 3 DEV + 1 HOLDOUT
AMP = dict(pos=None, sec=None, gain=None)     # filled from the amplitude pilot (sealed/p2_amplitudes.json)
DISC_RADIUS = 0.880          # = mean nearest-neighbour spacing of the reference phenotype (declared)

def amps():
    return json.load(open(os.path.join(SEALED, "p2_amplitudes.json")))

def base_path(ind, base): return path("p2base", f"{ind.name}_{base}")

def make_bases(i):
    """chain of continuation segments 0->16->32->64->128->320; state after each is the base for pulses."""
    ind = Ind("primary", i); prev = None; t = 0
    for name, b in sorted(BASES.items(), key=lambda kv: kv[1]):
        sim(base_path(ind, name), b - t, ind, cont=prev, meta=dict(stage="P2-base", base=name)); prev = base_path(ind, name); t = b
    return ind.name

def pulse_events(spec, b0, amp_scale=1.0, sign=1.0):
    """spec: dict(cls, ch, cells, k) -> list of event dicts. onset absolute = b0 + ONSET_LAG."""
    a = amps(); on = b0 + ONSET_LAG; ev = []
    cls = spec["cls"]
    if cls in ("POS", "REGION_POS"):
        ev.append(dict(type="pos", cells=spec["cells"], ch=spec["k"], amp=sign * amp_scale * a["pos"], onset=on, w=PULSE_W))
    elif cls in ("SEC", "REGION_SEC", "GLOBAL_SEC"):
        ev.append(dict(type="sec", cells=spec["cells"], ch=spec["k"], amp=sign * amp_scale * a["sec"], onset=on, w=PULSE_W))
    elif cls in ("GAIN", "REGION_GAIN", "GLOBAL_GAIN"):
        ev.append(dict(type="gain", cells=spec["cells"], ch=spec["k"], amp=sign * amp_scale * a["gain"], onset=on, w=PULSE_W))
    elif cls == "SHAM":
        g = np.random.default_rng(spec["seed"]).standard_normal((8, 10)); g *= np.sqrt(8) / np.linalg.norm(g)   # matched norm: sqrt(8) (= A-GLOBAL pulse)
        for c in range(8):
            for kk in range(2): ev.append(dict(type="pos", cells=[c], ch=kk + 1, amp=sign * amp_scale * a["pos"] * g[c, kk], onset=on, w=PULSE_W))
            for kk in range(4): ev.append(dict(type="sec", cells=[c], ch=kk + 1, amp=sign * amp_scale * a["sec"] * g[c, 2 + kk], onset=on, w=PULSE_W))
            for kk in range(4): ev.append(dict(type="gain", cells=[c], ch=kk + 1, amp=sign * amp_scale * a["gain"] * g[c, 6 + kk], onset=on, w=PULSE_W))
    else: raise ValueError(cls)
    return ev

def region_centres(ref_pos):
    """declared grid: spacing = DISC_RADIUS over the reference phenotype's bounding box (rows/columns inclusive of the box edges)."""
    xs = np.arange(ref_pos[0].min(), ref_pos[0].max() + 1e-9, DISC_RADIUS); ys = np.arange(ref_pos[1].min(), ref_pos[1].max() + 1e-9, DISC_RADIUS)
    if ys.max() < ref_pos[1].max() - 0.3: ys = np.append(ys, ref_pos[1].max())
    return [(float(x), float(y)) for x in xs for y in ys]

def specs_for(pos_at_base, centres):
    """All pulse specs for a base state. Region membership = cells within DISC_RADIUS of the centre at the base state (frozen at actuation)."""
    S = []
    for c in range(8):
        for k in (1, 2): S.append(dict(cls="POS", cells=[c], k=k, id=f"POS_c{c}_{'xy'[k-1]}"))
        for k in (1, 2, 3, 4): S.append(dict(cls="SEC", cells=[c], k=k, id=f"SEC_c{c}_l{k}")); S.append(dict(cls="GAIN", cells=[c], k=k, id=f"GAIN_c{c}_l{k}"))
    for gi, (cx, cy) in enumerate(centres):
        inside = [int(c) for c in range(8) if np.hypot(pos_at_base[0, c] - cx, pos_at_base[1, c] - cy) <= DISC_RADIUS]
        if not inside: continue
        for k in (1, 2, 3, 4):
            S.append(dict(cls="REGION_SEC", cells=inside, k=k, id=f"REG_g{gi}_SEC_l{k}", centre=(cx, cy)))
            S.append(dict(cls="REGION_GAIN", cells=inside, k=k, id=f"REG_g{gi}_GAIN_l{k}", centre=(cx, cy)))
    for k in (1, 2, 3, 4):
        S.append(dict(cls="GLOBAL_SEC", cells=list(range(8)), k=k, id=f"GLOB_SEC_l{k}")); S.append(dict(cls="GLOBAL_GAIN", cells=list(range(8)), k=k, id=f"GLOB_GAIN_l{k}"))
    for s in range(20): S.append(dict(cls="SHAM", cells=list(range(8)), k=0, seed=910000 + s, id=f"SHAM_s{s:02d}"))
    return S

def pulse_job(i, base, spec, sign=1.0, amp_scale=1.0, tag="p"):
    ind = Ind("primary", i); b0 = BASES[base]
    out = path("p2", f"{ind.name}_{base}_{spec['id']}_{tag}")
    sim(out, WINDOW, ind, cont=base_path(ind, base), events=pulse_events(spec, b0, amp_scale, sign),
        meta=dict(stage="P2", base=base, spec={k: v for k, v in spec.items()}, sign=sign, amp_scale=amp_scale))
    return out

def twin_job(i, base):
    ind = Ind("primary", i)
    sim(path("p2", f"{ind.name}_{base}_TWIN"), WINDOW, ind, cont=base_path(ind, base), meta=dict(stage="P2", base=base, twin=True))
