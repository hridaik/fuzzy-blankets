"""Part 3: build the blind data package (protocol v2 data ONLY) from the audit-side store. OBSERVABLE tier only: tracked positions and the four secreted levels per bin.
Writes morphogenesis/m2_blind_package/{segments/*.npz, manifest.jsonl, individuals.json, splits.json} and the sealed mapping sealed/blind_mapping.json (never in the package).
Segments are stored once; a continuation segment names its parent segment and the bin at which it starts, so no data is duplicated."""
import sys, os, json, glob, hashlib
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from v2 import *
PKG = os.path.join(os.path.dirname(M2A), "m2_blind_package")
SEED = 20261002
SPLIT_SEED = 7771
INCLUDE_DIRS = ["census", "census512", "r2", "r3", "r4", "p1_16", "p1_fam", "p1_hi", "p2rbase", "p2r"]
CH = {("pos", 1): "CH1", ("pos", 2): "CH2", **{("sec", k): f"CH{2 + k}" for k in (1, 2, 3, 4)}, **{("gain", k): f"CH{6 + k}" for k in (1, 2, 3, 4)}}
TX = {("kuch", 1): "TX1", ("kuch", -1): "TX2", ("sham", 0): "TX3", ("fscale", 3): "TX4", ("prec", 0): "TX5", ("belief", 0): "TX6"}
NOISE = {}                       # GV1 -> label, filled by registry order
DEFAULT_W = 4

def sid_of(f): return os.path.relpath(f, os.path.join(DATA, "v2"))[:-4]
def read_side(f): return json.load(open(f[:-4] + ".json"))
def treatments(side, base_bin):
    """experimenter-level description of what was done in this segment (opaque channel / treatment labels)."""
    out = []; N = side["N"]
    for e in side.get("events", []):
        t = e["type"]; cells = e.get("cells", [])
        tg = {"all": True} if len(cells) == 8 and t in ("kuch", "sham", "fscale", "sec", "gain", "pos") and len(cells) == side.get("n_cells", 8) else {"cells": [int(c) for c in cells]}
        if t in ("pos", "sec", "gain"):
            out.append(dict(kind="pulse", channel=CH[(t, int(e["ch"]))], applied_to=tg, onset_bin=int(e["onset"]), width_bins=int(e["w"]), shape="raised-cosine", amplitude=float(e["amp"])))
        elif t == "kuch":
            out.append(dict(kind="sustained" if e.get("off") in (None, float("inf")) else "window", family=TX[("kuch", int(e["sign"]))], applied_to=tg, onset_bin=int(e["onset"]),
                            off_bin=None if e.get("off") in (None, float("inf")) else int(e["off"]), ramp_bins=int(e["w"]), level=1.0))
        elif t == "sham":
            out.append(dict(kind="sustained" if e.get("off") in (None, float("inf")) else "window", family=TX[("sham", 0)], applied_to=tg, onset_bin=int(e["onset"]),
                            off_bin=None if e.get("off") in (None, float("inf")) else int(e["off"]), ramp_bins=int(e["w"]), amplitude=float(e["amp"])))
        elif t == "fscale":
            out.append(dict(kind="sustained" if e.get("off") in (None, float("inf")) else "window", family=TX[("fscale", 3)], applied_to=tg, onset_bin=int(e["onset"]),
                            off_bin=None if e.get("off") in (None, float("inf")) else int(e["off"]), ramp_bins=int(e["w"]), level=float(e["amp"])))
    if side.get("prec"):
        p = side["prec"]; off = p.get("off")
        out.append(dict(kind="sustained" if off in (None, float("inf")) else "window", family=TX[("prec", 0)], applied_to={"all": True}, onset_bin=int(p["onset"]),
                        off_bin=None if off in (None, float("inf")) else int(off), ramp_bins=int(p["w"]), level=float(p["F"])))
    k = side.get("kick")
    if k:
        if k["type"] == "pos": out.append(dict(kind="displacement", applied_to={"all": True}, onset_bin=int(base_bin), displacement_xy=np.asarray(k["dpos"]).T.tolist()))
        elif k["type"] == "sec": out.append(dict(kind="level-shift", applied_to={"all": True}, onset_bin=int(base_bin), shift=np.asarray(k["sec"]).tolist() if "sec" in k else None))
        elif k["type"] == "belief": out.append(dict(kind="sudden", family=TX[("belief", 0)], applied_to={"all": True}, onset_bin=int(base_bin)))
    return out

def collect():
    """registry of source segments: list of dict(path, side, parent_path, bin_start)"""
    files = []
    for d in INCLUDE_DIRS: files += sorted(glob.glob(os.path.join(DATA, "v2", d, "*.mat")))
    files += d4_transition_files()
    reg = {f: dict(path=f, side=read_side(f)) for f in files if os.path.exists(f[:-4] + ".json")}
    # absolute start bin of each segment = parent end (bins), recursion over continuation_of
    def start(f):
        r = reg.get(f)
        p = r["side"].get("continuation_of") if r else None
        if p is None: return 0
        if p in reg: return start(p) + reg[p]["side"]["N"]
        m = sio.loadmat(p); return int(np.ravel(m["b_end"])[0])
    for f, r in reg.items(): r["bin_start"] = start(f); r["parent"] = r["side"].get("continuation_of")
    return reg

def d4_transition_files():
    """TRANSITION DATASET: D4 run pairs just below / at the threshold for SHAPE-SWITCH and FATE-SWAP, plus the maximum-amplitude run of every direction with no threshold."""
    out = []; D = os.path.join(DATA, "v2", "d4")
    def segs(did, amp):
        fs = sorted(glob.glob(os.path.join(D, f"{did}_a{amp:.6g}_[0-9].mat"))); return fs
    for f in sorted(glob.glob(os.path.join(D, "dir_*.json"))):
        r = json.load(open(f)); did = r["id"]
        ev = {float(a): v for a, v in r["evals"].items()}
        for key in ("swap", "switch"):
            if r.get(key):
                hi = float(f"{r[key]:.6g}"); lows = [a for a, v in ev.items() if a < hi and ({"swap": v["label"] == "SAME", "switch": v["label"] != "SHAPE-SWITCH" and v["label"] != "NONCONV"}[key])]
                if hi in ev: out += segs(did, hi)
                if lows: out += segs(did, max(lows))
        if not r.get("swap") and not r.get("switch"): out += segs(did, max(ev))
    return sorted(set(out))

def build(dry=False):
    reg = collect(); rng = np.random.default_rng(SEED)
    paths = sorted(reg); order = rng.permutation(len(paths)); seg_id = {paths[i]: f"R{n + 1:06d}" for n, i in enumerate(order)}
    inds = sorted({(r["side"]["individual"], r["side"].get("L", 2)) for r in reg.values()}); io = rng.permutation(len(inds)); ind_id = {inds[i]: f"I{n + 1:03d}" for n, i in enumerate(io)}
    gv = sorted({r["side"]["GV1"] for r in reg.values() if r["side"].get("GV1") is not None}); gp = rng.permutation(len(gv)); noise_lab = {gv[i]: f"NL{k + 1}" for k, i in enumerate(gp)}   # labels deliberately not ordered by magnitude
    rows, mapping = [], {}; cond_key = {}
    base_labels = {}
    for f in paths:
        r = reg[f]; s = r["side"]; n_cells = 8 * (s.get("L", 2) // 2)  # L=2 -> 8 cells, L=4 -> 16
        s["n_cells"] = n_cells
        tr = treatments(s, r["bin_start"])
        sp = (s.get("meta") or {}).get("spec") or {}
        if sp.get("centre"):
            for t in tr: t["applied_to"] = {"region": dict(centre=[float(x) for x in sp["centre"]], radius=0.88, cells_at_actuation=[int(c) for c in sp["cells"]])}
        parent = seg_id.get(r["parent"]) if r["parent"] else None
        if r["parent"] and parent is None: parent = "EXTERNAL"      # base state outside the package (not expected)
        rows.append(dict(segment_id=seg_id[f], individual_id=ind_id[(s["individual"], s.get("L", 2))], protocol="v2", n_cells=n_cells, n_bins=int(s["N"]), bin_start=int(r["bin_start"]),
                         parent_segment=parent, treatments=tr, noise_label=noise_lab.get(s.get("GV1"), "NL0"), rearing_label="RC2" if s.get("T_dev", 32) != 32 else "RC1"))
        mapping[seg_id[f]] = dict(source=os.path.relpath(f, DATA), individual=s["individual"], meta=s.get("meta"), GV1=s.get("GV1"), T_dev=s.get("T_dev"))
    # matched controls: untreated sibling segment with same parent and same length
    by_par = {}
    for row in rows:
        if not row["treatments"] and row["parent_segment"]: by_par.setdefault((row["parent_segment"], row["n_bins"], row["noise_label"]), []).append(row["segment_id"])
    for row in rows:
        c = by_par.get((row["parent_segment"], row["n_bins"], row["noise_label"]), []) if row["parent_segment"] else []
        row["matched_control"] = None if (row["segment_id"] in c or not c) else c[0]
    # conditions = whole treatment types (opaque id); baseline (no treatment) conditions are never held out
    def ckey(row):
        if not row["treatments"]: return "NONE|" + row["noise_label"] + "|" + str(row["n_cells"])
        parts = []
        for t in row["treatments"]:
            tg = "all" if t["applied_to"].get("all") else ("one" if len(t["applied_to"].get("cells", [])) == 1 else "set")
            parts.append("|".join(str(x) for x in (t["kind"], t.get("channel") or t.get("family"), tg, np.sign(t.get("amplitude", 1)), round(abs(t.get("amplitude", t.get("level", 0)) or 0), 3))))
        return "+".join(parts) + "|" + row["noise_label"]
    keys = sorted({ckey(r) for r in rows}); co = rng.permutation(len(keys)); cid = {keys[i]: f"C{n + 1:03d}" for n, i in enumerate(co)}
    for r in rows: r["condition_id"] = cid[ckey(r)]; r["_ck"] = ckey(r)
    # ---- splits ----
    srng = np.random.default_rng(SPLIT_SEED); ind_list = sorted(set(ind_id.values())); ho_ind = sorted(srng.choice(ind_list, size=max(1, int(round(0.2 * len(ind_list)))), replace=False).tolist())
    treated = sorted({r["condition_id"] for r in rows if r["treatments"]}); ho_cond = sorted(srng.choice(treated, size=max(1, int(round(0.15 * len(treated)))), replace=False).tolist())
    centres = sorted({tuple(t["applied_to"]["region"]["centre"]) for r in rows for t in r["treatments"] if "region" in t["applied_to"]}); ho_centres = []
    if centres: ho_centres = sorted(tuple(c) for c in [centres[i] for i in srng.choice(len(centres), size=max(1, int(round(0.3 * len(centres)))), replace=False)])
    for r in rows:
        r["holdout_region"] = any("region" in t["applied_to"] and tuple(t["applied_to"]["region"]["centre"]) in ho_centres for t in r["treatments"])
        r["holdout_individual"] = r["individual_id"] in ho_ind; r["holdout_condition"] = r["condition_id"] in ho_cond
        why = [n for n, f in (("individual", r["holdout_individual"]), ("condition", r["holdout_condition"]), ("region", r["holdout_region"])) if f]
        r["split"] = "dev" if not why else "holdout_" + "+".join(why)
    if dry: return rows, mapping, cid, ho_ind, ho_cond
    os.makedirs(os.path.join(PKG, "segments"), exist_ok=True); inv = {f: seg_id[f] for f in paths}
    for f in paths:
        m = load(f); s = reg[f]["side"]; n = s["n_cells"]; N = m["positions"].shape[1]
        pos = m["positions"].reshape(n, 2, N).transpose(2, 0, 1) if False else np.stack([m["positions"][:, b].reshape(n, 2) for b in range(N)]); sec = np.stack([m["secretion"][:, b].reshape(4, n, order="F").T for b in range(N)])
        np.savez_compressed(os.path.join(PKG, "segments", seg_id[f] + ".npz"), position=pos.astype(np.float32), levels=sec.astype(np.float32))
    with open(os.path.join(PKG, "manifest.jsonl"), "w") as fh:
        for r in sorted(rows, key=lambda r: r["segment_id"]):
            r = {k: v for k, v in r.items() if k != "_ck"}; fh.write(json.dumps(r) + "\n")
    json.dump(dict(development_individuals=sorted(set(ind_list) - set(ho_ind)), holdout_individuals=ho_ind, holdout_conditions=ho_cond, holdout_region_centres=[list(c) for c in ho_centres], rule="20 % of individuals and 15 % of treated conditions drawn at random (seed withheld by the package author)"),
              open(os.path.join(PKG, "splits.json"), "w"), indent=1)
    json.dump(dict(segments=mapping, individuals={v: dict(real=k[0], L=k[1]) for k, v in ind_id.items()}, conditions={v: k for k, v in cid.items()}, noise={v: k for k, v in noise_lab.items()},
                   channels={v: dict(zip(("type", "index"), k)) for k, v in CH.items()}, treatments={v: list(k) for k, v in TX.items()}, seeds=dict(opaque_ids=SEED, split=SPLIT_SEED)),
              open(os.path.join(SEALED, "blind_mapping.json"), "w"), indent=1, default=str)
    return rows

if __name__ == "__main__":
    dry = "--dry" in sys.argv; res = build(dry)
    if dry:
        rows, mapping, cid, ho_ind, ho_cond = res; print(len(rows), "segments;", len(cid), "conditions;", len(ho_ind), "holdout individuals;", len(ho_cond), "holdout conditions")
        import collections; print(collections.Counter(r["split"] for r in rows)); print(collections.Counter(r["noise_label"] for r in rows)); print(sum(r["n_bins"] for r in rows), "bins")
