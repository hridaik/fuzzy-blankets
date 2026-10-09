"""morphogenesis/viz/build_viewer_m2a.py — M2a extension of the shared viewer (build_viewer.py is NOT modified).
Adds to the template (all optional per rollout):
  caption   : list (per frame) of short strings drawn top-left of the arena (OBSERVABLE builds use opaque wording only)
  labels    : AUDIT only. list (per frame) of per-cell strings drawn beside each cell (role-map overlay)
  arrows    : AUDIT only. per-frame (or single static) list of per-cell [dx, dy] arrow vectors (eigenmode visualisation), drawn from each cell
An OBSERVABLE build never receives labels/arrows: rollout_to_json_dict_m2a(...) drops them unless is_audit=True, so the OBSERVABLE file physically cannot contain them."""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_viewer as BV

PATCH_DRAW = r"""
  if (r.caption) {
    ctx.fillStyle = '#ccc'; ctx.font = '11px sans-serif';
    ctx.fillText(r.caption[Math.min(b, r.caption.length-1)], 6, 14);
  }
  if (IS_AUDIT && r.arrows) {
    const A = Array.isArray(r.arrows[0][0]) && Array.isArray(r.arrows[0][0][0]) ? r.arrows[Math.min(b, r.arrows.length-1)] : r.arrows;
    ctx.strokeStyle = '#ff6'; ctx.lineWidth = 1.5;
    for (let c=0; c<A.length; c++) {
      const x = cx + r.a_x[b][0][c]*scale, y = cy + r.a_x[b][1][c]*scale;
      ctx.beginPath(); ctx.moveTo(x,y); ctx.lineTo(x + A[c][0]*scale, y + A[c][1]*scale); ctx.stroke();
    }
    ctx.lineWidth = 1;
  }
  if (IS_AUDIT && r.labels) {
    const Lb = r.labels[Math.min(b, r.labels.length-1)];
    ctx.fillStyle = '#9f9'; ctx.font = '11px sans-serif';
    for (let c=0; c<Lb.length; c++) {
      const x = cx + r.a_x[b][0][c]*scale, y = cy + r.a_x[b][1][c]*scale;
      ctx.fillText(Lb[c], x+8, y-7);
    }
  }
}

function drawTimeSeries(idx, bin) {"""
TEMPLATE = BV.TEMPLATE.replace("}\n\nfunction drawTimeSeries(idx, bin) {", PATCH_DRAW, 1)
assert "r.caption" in TEMPLATE

def rollout_to_json_dict_m2a(label, a_x, a_s, caption=None, labels=None, arrows=None, is_audit=False, max_frames=BV.DEFAULT_MAX_FRAMES, ligand=None, images=None, image_stride=1):
    """a_x (N,2,n), a_s (N,4,n). Frame downsampling applies to every per-frame field identically."""
    n = a_x.shape[0]; stride = 1 if n <= max_frames else int(np.ceil(n / max_frames)); sel = slice(None, None, stride)
    d = {"label": label + (f" [every {stride}th bin]" if stride > 1 else ""), "a_x": a_x[sel].tolist(), "a_s": a_s[sel].tolist()}
    if caption is not None: d["caption"] = list(caption)[sel]
    if is_audit and labels is not None: d["labels"] = list(labels)[sel]
    if is_audit and arrows is not None: d["arrows"] = arrows if np.ndim(arrows) == 2 else np.asarray(arrows)[sel].tolist()
    if ligand is not None: d["ligand"] = np.asarray(ligand)[sel].tolist()
    if images is not None: d["images"] = np.asarray(images).tolist(); d["image_stride"] = image_stride
    return d

def build_html(rollout_dicts, title, banner_text, banner_class, header_info, is_audit, out_path):
    data_json = json.dumps({"rollouts": rollout_dicts})
    html = (TEMPLATE.replace("__TITLE__", title).replace("__BANNER_CLASS__", banner_class).replace("__BANNER_TEXT__", banner_text).replace("__HEADER_INFO__", header_info)
            .replace("__DATA_JSON__", data_json).replace("__IS_AUDIT__", "true" if is_audit else "false"))
    open(out_path, "w").write(html); size = os.path.getsize(out_path)
    if size >= BV.MAX_BYTES: raise ValueError(f"{out_path} is {size} bytes (> 20 MB)")
    return size
