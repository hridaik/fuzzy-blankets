"""Part 4 (revised): M2a viewer builds, OBSERVABLE + AUDIT. Run:  python build_m2a_viewer.py <group> [...]   groups: class1 sustained triples d3 d4 d5 eigen
Exemplar rule (declared, as M1): per batch, median / best / worst by the batch's hidden-tier metric + two uniformly random picks (seed recorded in output/m2a/exemplar_selection.json)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from viewer_common import *
REG = os.path.join(OUT, "exemplar_selection.json"); ENT = os.path.join(OUT, "entries.json")
def load_json(p, d): return json.load(open(p)) if os.path.exists(p) else d
SEL = load_json(REG, {}); ENTRIES = load_json(ENT, [])
def save():
    os.makedirs(OUT, exist_ok=True); json.dump(SEL, open(REG, "w"), indent=1); json.dump(ENTRIES, open(ENT, "w"), indent=1)
def add(name, *a, **k):
    global ENTRIES; ENTRIES = [e for e in ENTRIES if e["name"] != name]; write_pair(name, *a, entries=ENTRIES, **k); save()
BAN = "v2 protocol; data from the white-box harness"
def trip(pairs, caps, is_aud):
    """pairs: list of (label, a_x, a_s); returns rollout dicts. Audit adds role overlay."""
    out = []
    for (lab, ax, as_), cap in zip(pairs, caps):
        lab_r = role_labels(ax, as_, stride=8) if is_aud else None
        out.append(BM.rollout_to_json_dict_m2a(lab, ax, as_, caption=cap, labels=lab_r, is_audit=is_aud))
    return out

def class1():
    names = ["secondary_0005", "secondary_0012", "secondary_0013"]; ref = chain([path("census", "primary_0000_A"), path("census", "primary_0000_B")])
    J = {n: float(np.ravel(load(path("census", n + "_B"))["free_energy_J"])[-1]) if "free_energy_J" in load(path("census", n + "_B")) else 0.0 for n in names}
    SEL["class1"] = dict(rule="all class-1 individuals of the census (3) shown; metric = final free energy J (audit)", J=J, batch=names)
    for n in names:
        c1 = chain([path("census", n + "_A"), path("census", n + "_B")]); N = c1[0].shape[0]
        cap = [f"bin {b}" for b in range(N)]
        pairs = [("class-1 individual (left) vs class-0 reference (right)", *c1), ("reference individual", *ref)]
        add(f"class1_{n}", trip(pairs, [cap, cap], False), trip(pairs, [cap, cap], True), f"Class-1 exemplar {n}", BAN, f"two preparations side by side, same bins; {n} settles in a second end-state", f"{n}: role overlay shows duplicated/vacant slots (hidden-derived)")

def sustained():
    metrics = {}
    for i in range(20):
        m = load(path("r2", f"primary_{i:04d}_SUST_DH")); metrics[f"primary_{i:04d}"] = float(np.linalg.norm(m["positions"][:, -1] - m["positions"][:, -2]))
    sel = select_exemplars({k: -v for k, v in metrics.items()}, 101); SEL["sustained_DH"] = dict(sel, metric="last-bin lag-1 position change (cycle amplitude), best = largest")
    picks = [sel["best"], sel["median"], sel["worst"]] + sel["random"]
    for p in sorted(set(picks)):
        ax, as_ = chain([path("r2", f"{p}_SUST_DH")]); N = ax.shape[0]; cap = [f"bin {b} (TX1 sustained from bin 0)" for b in range(N)]
        pairs = [("sustained treatment, full run", ax, as_)]
        add(f"sustained_DH_{p}", trip(pairs, [cap], False), trip(pairs, [cap], True), f"Sustained TX1 run {p}", BAN, "sustained treatment from bin 0; a flicker with period 2 bins is expected at late bins (use step-fwd)", "role overlay")

def triples():
    kinds = {"DH": "TX1", "DT": "TX2", "AN": "TX1 (one cell)", "SHAM_DH": "TX3"}
    for k, tx in kinds.items():
        metrics = {}
        for i in range(20):
            nm = f"primary_{i:04d}"; P = load(path("r2", f"{nm}_{k}_ADULT")); U = load(path("r2", f"{nm}_UNP_ADULT"))
            pp, sp, _ = state(P); pu, su, _ = state(U); sl_p, _ = slot_assignment(pp, sp); sl_u, _ = slot_assignment(pu, su)
            metrics[nm] = float((sl_p != sl_u).sum()) + 1e-3 * d_pair_pos(pp, sp, pu, su)
        sel = select_exemplars(metrics, 202 + len(k)); SEL[f"triples_{k}"] = dict(sel, metric="cells changing role + 1e-3 x d_pair to the unperturbed twin (hidden-tier)")
        for p in sorted(set([sel["best"], sel["median"], sel["worst"]] + sel["random"])):
            A = path("census", f"{p}_A"); sk = {"DH": "SUST_DH", "DT": "SUST_DT", "AN": "SUST_AN"}.get(k)
            per = chain([A, path("r2", f"{p}_{k}_ADULT")]); unp = chain([A, path("r2", f"{p}_UNP_ADULT")])
            items = [("treated for a window starting at bin 320", *per), ("untreated twin (same history)", *unp)]
            if sk: items.append(("treatment sustained from bin 0 (twin)", *chain([path("r2", f"{p}_{sk}")])))
            capf = lambda ax: [f"bin {b}" for b in range(ax.shape[0])]
            add(f"triple_{k}_{p}", trip(items, [capf(i[1]) for i in items], False), trip(items, [capf(i[1]) for i in items], True), f"{tx}-ADULT synced {'triple' if sk else 'pair'} {p}", BAN,
                f"{tx}: treated vs untreated vs sustained, shared scrubber (bins aligned by absolute bin; the sustained run starts at bin 0)", "role overlay shows relabelling vs the unperturbed twin")

def d3():
    from d3_analyze import load_chain
    def frames(chain_name):
        R = load_chain(chain_name); top = max(range(len(R)), key=lambda i: R[i]["level"]); fam, st = chain_name.split("_")
        def last(r):
            j = r["n_seg"] - 1; ax, as_ = chain([path("d3", f"{fam}_{st}_s{r['step']:03d}_{j}")]); return ax[-1], as_[-1]
        up = [last(r) for r in R[:top + 1]]; down = [last(r) for r in R[top:]][::-1]; lev = [R[i]["level"] for i in range(top + 1)]
        return lev, up, down, R, top
    for cn, tx in (("DH_c0", "TX1"), ("DT_c0", "TX2"), ("DT_c1", "TX2"), ("PREC_c0", "TX5"), ("PREC_c1", "TX5"), ("DH_c1", "TX1")):
        try: lev, up, down, R, top = frames(cn)
        except Exception as e: print("skip", cn, e); continue
        k = min(len(up), len(down)); ax_u = np.stack([u[0] for u in up[:k]]); as_u = np.stack([u[1] for u in up[:k]]); ax_d = np.stack([d[0] for d in down[:k]]); as_d = np.stack([d[1] for d in down[:k]])
        cap = [f"{tx} level {lev[i]:g}" for i in range(k)]
        items = [("level stepped UP (settled state at each level)", ax_u, as_u), ("level stepped DOWN (settled state at the same level)", ax_d, as_d)]
        if cn.endswith("c1") and cn.startswith("DH"): items = items[:1]
        add(f"sweep_{cn}", trip(items, [cap] * len(items), False), trip(items, [cap] * len(items), True), f"Quasi-static sweep {cn}", BAN, f"one frame per parameter level (settled), start from the {'second' if cn.endswith('c1') else 'first'} end-state; left = up-sweep, right = down-sweep, synced by level", "role overlay")

def d4():
    import glob
    for key, sty in (("switch", "SHAPE-SWITCH"), ("swap", "FATE-SWAP")):
        dirs = {}
        for f in sorted(glob.glob(os.path.join(DATA, "v2", "d4", "dir_*.json"))):
            r = json.load(open(f))
            if r.get(key): dirs[r["id"]] = r
        if not dirs: print("no", key); continue
        sel = select_exemplars({k: v[key] for k, v in dirs.items()}, 303 + len(key)); SEL[f"d4_{key}"] = dict(sel, metric=f"{sty} threshold amplitude (hidden-tier), best = smallest", n_directions=len(dirs))
        for p in sorted(set([sel["best"], sel["median"], sel["worst"]] + sel["random"])):
            r = dirs[p]; ev = {float(a): v for a, v in r["evals"].items()}; hi = float(f"{r[key]:.6g}")
            lows = [a for a, v in ev.items() if a < hi and (v["label"] == "SAME" if key == "swap" else v["label"] not in ("SHAPE-SWITCH", "NONCONV"))]; lo = max(lows)
            def run(a):
                fs = sorted(glob.glob(os.path.join(DATA, "v2", "d4", f"{p}_a{a:.6g}_[0-9].mat"))); return chain([path("census", "primary_0000_A")] + [f[:-4] and f for f in fs])
            lo_ax, lo_s = run(lo); hi_ax, hi_s = run(hi); items = [(f"just below threshold (amplitude {lo:.4g})", lo_ax, lo_s), (f"just above threshold ({hi:.4g})", hi_ax, hi_s)]
            capf = lambda ax: [f"bin {b}" for b in range(ax.shape[0])]
            add(f"pair_{key}_{p}", trip(items, [capf(i[1]) for i in items], False), trip(items, [capf(i[1]) for i in items], True), f"Near-threshold pair ({sty}) {p}", BAN, "two runs whose treatment amplitudes differ by 1 %, synced; treatment applied at bin 320", f"role overlay; audit outcome below/above: {r['evals'].get(f'{lo:.6g}',{}).get('label')} / {r['evals'].get(f'{hi:.6g}',{}).get('label')}")

def eigen():
    import scipy.io as sio
    for name, cont in (("class0", path("census", "primary_0000_A")), ("class1", path("census", "secondary_0005_A"))):
        J = sio.loadmat(path("d1", f"J_{name}"))["J"][:, :, 1]; w, V = np.linalg.eig(J); o = np.argsort(-np.abs(w)); w, V = w[o], V[:, o]
        ax, as_ = seg_arrays(load(cont)); ax = np.repeat(ax[-1:], 12, 0); as_ = np.repeat(as_[-1:], 12, 0)
        for k in range(5):
            v = V[:, k].real; pv = v[128:144].reshape(8, 2); pv = pv / (np.linalg.norm(pv) + 1e-12) * 1.0
            arrows = pv.tolist(); lab = [[f"mode {k}: |mu|={abs(w[k]):.3f}"] * 8] * 12
            d_obs = BM.rollout_to_json_dict_m2a(f"{name} adult state (static)", ax, as_, caption=["adult state; no overlay in this tier"] * 12, is_audit=False)
            d_aud = BM.rollout_to_json_dict_m2a(f"{name}: position-action part of eigenvector {k} (yellow arrows, unit norm)", ax, as_, caption=[f"mode {k}: |mu| = {abs(w[k]):.3f}, rate {np.log(abs(w[k])):.3f}/bin"] * 12, arrows=arrows, is_audit=True)
            add(f"eigen_{name}_m{k}", [d_obs], [d_aud], f"Eigenmode {k} {name}", BAN, "static adult state (the eigenmode overlay exists in the AUDIT build only)", f"audit: arrows = position-action component of the slowest-mode eigenvector {k}")


def d5():
    import scipy.io as sio
    D5 = os.path.join(DATA, "v2", "d5"); P = lambda n: os.path.join(D5, n + ".mat")
    hops = chain([P(f"adv_a_{k}") for k in range(15)]); ea = chain([P("adv_a_14"), P("esc_a")]); eb = chain([P("adv_b_14"), P("esc_b")])
    J = sio.loadmat(P("J_edge_hop14"))["J"][:, :, 1]; w, V = np.linalg.eig(J); o = np.argsort(-np.abs(w)); u = V[:, o[0]].real; pv = u[128:144].reshape(8, 2); pv = pv / (np.linalg.norm(pv) + 1e-12)
    capH = [f"hop {b // 8} (class-0-side member, 8 bins per hop)" for b in range(hops[0].shape[0])]
    capE = lambda ax, s: [f"edge state + {b} bins ({s})" for b in range(ax.shape[0])]
    obs = [BM.rollout_to_json_dict_m2a("edge tracking: state of the bracketing pair, hops 0-14", *hops, caption=capH, is_audit=False),
           BM.rollout_to_json_dict_m2a("started on one side of the boundary (edge state at bin 0)", *ea, caption=capE(ea[0], "side A"), is_audit=False),
           BM.rollout_to_json_dict_m2a("started on the other side", *eb, caption=capE(eb[0], "side B"), is_audit=False)]
    aud = [BM.rollout_to_json_dict_m2a("edge tracking: hops 0-14", *hops, caption=capH, labels=role_labels(*hops), is_audit=True),
           BM.rollout_to_json_dict_m2a("side A (arrows: position part of the single unstable eigenvector, unit norm)", *ea, caption=capE(ea[0], "side A; mu_unstable=%.3f" % abs(w[o[0]])), labels=role_labels(*ea), arrows=pv.tolist(), is_audit=True),
           BM.rollout_to_json_dict_m2a("side B", *eb, caption=capE(eb[0], "side B"), labels=role_labels(*eb), is_audit=True)]
    add("edge_state_D5", obs, aud, "Edge state on the basin boundary", BAN, "left: states visited by edge tracking; centre/right: the two sides of the boundary released from the edge state (they separate to the two end-states)", "audit: role overlay + unstable eigenvector arrows (unstable mu 1.66)")

if __name__ == "__main__":
    for g in sys.argv[1:]: globals()[g](); print("built", g)
