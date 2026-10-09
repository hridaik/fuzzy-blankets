"""Observation-ladder products O2-O4 for a DECLARED SUBSET of package segments, rendered with M1's renderer (m1_dynamics_census/code/observation_ladder.py, RENDERER_VERSION m1-obsladder-v1, unmodified).
O1 (tracked positions + levels) is every segment in the package. Frame rule (declared): every bin for the first 2w bins after the treatment onset in the segment (w = pulse/ramp width, 4 bins -> 8 bins; for an untreated
segment, the first 8 bins of the segment), every 8th bin afterwards. Subset rule (declared, seeded): 8-cell segments of <= 600 bins; up to 2 segments (random, seed 5150) for each treatment family or channel and for the
untreated class, drawn from the development split only. Renders per-frame products only; nothing is analysed."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from m2a_common import M1_CODE, MORPH
sys.path.insert(0, M1_CODE)
import importlib.util
spec = importlib.util.spec_from_file_location("observation_ladder", os.path.join(M1_CODE, "observation_ladder.py")); OL = importlib.util.module_from_spec(spec); spec.loader.exec_module(OL)
PKG = os.path.join(MORPH, "m2_blind_package"); SEEDL = 5150; STRIDE = 8; W = 4
def frames_for(n_bins, onset_rel):
    first = list(range(max(0, onset_rel), min(n_bins, max(0, onset_rel) + 2 * W)))
    pre = [] if onset_rel <= 0 else list(range(0, onset_rel, STRIDE))
    after = list(range(max(0, onset_rel) + 2 * W, n_bins, STRIDE))
    return sorted(set(pre + first + after))
def main():
    rows = [json.loads(l) for l in open(os.path.join(PKG, "manifest.jsonl"))]; rng = np.random.default_rng(SEEDL)
    cands = {}
    for r in rows:
        if r["n_cells"] != 8 or r["n_bins"] > 600 or r["split"] != "dev" or r["noise_label"] != "NL0": continue
        keys = {"untreated"} if not r["treatments"] else {t.get("channel") or t.get("family") or t["kind"] for t in r["treatments"]}
        for k in keys: cands.setdefault(k, []).append(r)
    chosen = {}
    for k in sorted(cands):
        idx = rng.permutation(len(cands[k]))[:2]
        for i in idx: chosen[cands[k][i]["segment_id"]] = cands[k][i]
    os.makedirs(os.path.join(PKG, "ladder"), exist_ok=True); n_fr = 0
    for sid, r in sorted(chosen.items()):
        z = np.load(os.path.join(PKG, "segments", sid + ".npz")); pos = z["position"].astype(float); lev = z["levels"].astype(float)
        on = min([t["onset_bin"] - r["bin_start"] for t in r["treatments"]] or [0]); fr = frames_for(r["n_bins"], on); O2x, O2s, O3a, O3b, O4 = [], [], [], [], []
        for f in fr:
            a_x = pos[f].T.copy(); a_s = lev[f].T.copy()          # (2,n), (4,n)
            ox, os_ = OL.render_O2(a_x, a_s, sid, f); O2x.append(ox); O2s.append(os_)
            O3a.append(OL.render_O3a(a_x, a_s, sid, f)); O3b.append(OL.render_O3b(a_x, a_s, sid, f)); O4.append(OL.render_O4(a_x, a_s))
        np.savez_compressed(os.path.join(PKG, "ladder", sid + ".npz"), cloud_position=np.stack(O2x), cloud_levels=np.stack(O2s), image_a=np.stack(O3a), image_b=np.stack(O3b), map=np.stack(O4), frames=np.array(fr))
        n_fr += len(fr)
    json.dump(dict(renderer=OL.RENDERER_VERSION, n_segments=len(chosen), n_frames=n_fr, segments=sorted(chosen), frame_rule=f"every bin for the first {2 * W} bins after treatment onset (untreated: first {2 * W} bins), every {STRIDE}th afterwards",
                   fov_half_width=OL.FOV_HALF_WIDTH, image_size=OL.IMG_SIZE, blob_sigma_px=OL.BLOB_SIGMA_PX, snr_db=OL.NOISE_SNR_DB, map_grid=OL.LIGAND_GRID_N, seed=SEEDL), open(os.path.join(PKG, "ladder_index.json"), "w"), indent=1)
    print(len(chosen), "segments;", n_fr, "frames")
if __name__ == "__main__": main()
