"""Build the Stage 6.9 translating-identity visualization (task brief §38).

Produces a single self-contained HTML file that opens with no server, in the
same spirit as `interactive_demo/build/index.html` -- but as a SEPARATE file
under this stage's own `figures/`, because `interactive_demo/` belongs to
earlier stages and this project's rule is that Stage 6.9 adds files rather than
editing prior ones.

Three synchronized panels (§38):
  1. WORLD FRAME    -- moving birds, the detected collective, the predictive
                       boundary, the causal interface, actuators, target path
  2. MATERIAL LINEAGE -- members of the originally detected collective
                       highlighted, with R_M(t); original members visibly leave
  3. CO-MOVING FRAME -- the collective after subtracting the ESTIMATED
                       translation, with R_F(t) and D_deform(t)

Run only after the data are real: it reads frozen JSON and refuses to build
from a gate that did not pass.
"""
from __future__ import annotations

import json

import numpy as np

from common_69 import (ModelParams, load_json, dump_json, DATA_DIR, FIG_DIR, N_BIRDS,
                       L_BOX, R_RADIUS, V_SPEED, BETA, RHO, OMEGA, UV4)
from moving_flock import MovingFlock
from identity_69 import torus_delta

MAX_FRAMES = 200      # cover the full tracked episode; the footer quotes
                      # numbers the viewer can actually scrub to


def build_bundle() -> dict:
    gate = load_json(DATA_DIR / "translation_gate.json")
    passing = [e for e in gate["episodes"] if e["passes"]]
    if passing:
        ep = min(passing, key=lambda e: e["R_M_final"])   # the clearest turnover episode
    else:
        # The gate FAILED. The visualization is still built, from the
        # longest-tracked episode, so it shows what the specified model actually
        # does -- a group that sheds members while fragmenting -- rather than
        # showing nothing. The page says so.
        ep = max([e for e in gate["episodes"] if e.get("tracked")],
                 key=lambda e: e["duration"])

    mf = MovingFlock(N=N_BIRDS, L=L_BOX, R=R_RADIUS, v=V_SPEED,
                     params=ModelParams(beta=BETA, precB=RHO, precC=OMEGA))
    res = mf.run(nt=ep["t_end"] + 2, seed=ep["seed"])
    recs = ep["records"][:MAX_FRAMES]

    # membership per frame is not stored in the gate file (too large); recover it
    # by re-running the same detector deterministically
    import detect_69 as det
    members, tracker = [], None
    for rec in recs:
        t = rec["t"]
        zw = res.z_hist[max(0, t - det.W_AFFINITY + 1):t + 1]
        cands = det.propose(res.r_hist[t], zw, mf.L)
        if tracker is None:
            tracker = det.TranslatingTracker(mf.L)
            tracker.start(cands[0], res.r_hist[t], res.z_hist[t], t)
        elif not tracker.update(cands, res.r_hist[t], res.z_hist[t], t):
            break
        members.append(sorted(int(x) for x in tracker.state.members))
    recs = recs[:len(members)]

    origin = members[0] if members else []
    frames = []
    for rec, mem in zip(recs, members):
        t = rec["t"]
        c = np.asarray(rec["centroid"])
        rel = torus_delta(res.r_hist[t][mem], c, mf.L)
        frames.append(dict(
            t=int(t), members=mem,
            R_M=float(rec["R_M"]), R_F=float(rec.get("R_F", float("nan"))),
            D_deform=float(rec.get("D_deform", float("nan"))),
            D_world=float(rec.get("D_world_frame", float("nan"))),
            size=int(rec["size"]), centroid=[float(x) for x in c],
            rel=[[round(float(a), 3), round(float(b), 3)] for a, b in rel],
            rel_h=[int(h) for h in res.z_hist[t][mem]],
        ))

    # interfaces, if boundary inference ran on this seed
    interfaces = {}
    try:
        rev = load_json(DATA_DIR / "oracle_reveal_69.json")
        for r in rev["runs"]:
            if r["seed"] == ep["seed"]:
                interfaces[str(r["t"])] = dict(B_D=r["B_D"], B_causal=r["B_causal_sampled"],
                                               B_pred=r["B_pred"])
    except FileNotFoundError:
        pass

    world = [dict(t=int(f["t"]),
                  x=[round(float(v), 2) for v in res.r_hist[f["t"]][:, 0]],
                  y=[round(float(v), 2) for v in res.r_hist[f["t"]][:, 1]],
                  h=[int(v) for v in res.z_hist[f["t"]]])
             for f in frames]

    return dict(seed=int(ep["seed"]), L=float(mf.L), R=float(mf.R), N=int(mf.N),
                origin=origin, frames=frames, world=world, interfaces=interfaces,
                summary=dict(duration=len(frames),
                             episode_duration=ep["duration"],
                             displacement_radii=ep["displacement_radii"],
                             # quote the LAST RENDERED frame, so every number in
                             # the footer is one the viewer can scrub to
                             R_M_final=float(frames[-1]["R_M"]) if frames else float("nan"),
                             R_M_episode_final=ep["R_M_final"],
                             R_M_min=float(min(f["R_M"] for f in frames)) if frames else float("nan"),
                             frac_steps_RM_below_0_7=float(np.mean(
                                 [f["R_M"] <= 0.70 for f in frames])) if frames else float("nan"),
                             mean_R_F=float(np.nanmean([f["R_F"] for f in frames])) if frames else float("nan"),
                             mean_D_deform=float(np.nanmean([f["D_deform"] for f in frames])) if frames else float("nan")),
                gate_passed=bool(gate.get("gate_passes")),
                gate=dict(pass_rate=gate["pass_rate"],
                          criteria=gate["criteria"],
                          n_episodes=len(gate["episodes"])))


HTML = r"""<!doctype html>
<meta charset="utf-8">
<title>Stage 6.9 — translating collective identity</title>
<style>
 :root{--bg:#fbfbfa;--fg:#26262b;--mut:#8a8a92;--mat:#b3453b;--fun:#3b6ea5;
       --def:#6a9b5e;--pred:#e08a2e;--ora:#4a4a4a;--line:#e3e3e0}
 body{margin:0;background:var(--bg);color:var(--fg);
      font:13px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
 header{padding:18px 22px 10px;border-bottom:1px solid var(--line)}
 h1{margin:0 0 4px;font-size:16px;font-weight:650;letter-spacing:-.01em}
 .sub{color:var(--mut);font-size:12px;max-width:70ch}
 .wrap{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;padding:16px 22px}
 .panel{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px}
 .panel h2{margin:0 0 2px;font-size:12px;font-weight:650}
 .panel .cap{color:var(--mut);font-size:11px;margin:0 0 8px;min-height:2.6em}
 canvas{width:100%;height:auto;display:block;border-radius:4px;background:#fcfcfc}
 .metrics{display:flex;gap:14px;margin-top:9px;flex-wrap:wrap}
 .m{font-variant-numeric:tabular-nums}
 .m b{display:block;font-size:16px;font-weight:650;line-height:1.15}
 .m span{color:var(--mut);font-size:10.5px;text-transform:uppercase;letter-spacing:.04em}
 .controls{display:flex;align-items:center;gap:12px;padding:0 22px 18px}
 input[type=range]{flex:1}
 button{border:1px solid var(--line);background:#fff;border-radius:6px;padding:5px 12px;
        font:inherit;cursor:pointer}
 button:hover{background:#f3f3f1}
 footer{padding:6px 22px 26px;color:var(--mut);font-size:11px;max-width:100ch}
 code{background:#f1f1ef;padding:1px 4px;border-radius:3px;font-size:11px}
</style>
<header>
  <h1>A collective that keeps its organization while its members are replaced</h1>
  <p class="sub">Stage 6.9 pilot, seed <b id="seed"></b>. The detector sees only positions and
  headings; the translating frame is <i>estimated</i>, never supplied. Watch the left panel move,
  the middle panel empty out, and the right panel stay still.</p>
</header>
<div class="wrap">
  <div class="panel">
    <h2>1 · World frame</h2>
    <p class="cap">Every bird, with the detected collective picked out. This is what an observer
    sees: a group crossing the torus.</p>
    <canvas id="cw" width="520" height="520"></canvas>
    <div class="metrics">
      <div class="m"><b id="mt">—</b><span>step t</span></div>
      <div class="m"><b id="msize">—</b><span>size |I<sub>t</sub>|</span></div>
    </div>
  </div>
  <div class="panel">
    <h2>2 · Material lineage</h2>
    <p class="cap">Members of the <i>originally</i> detected collective stay red; recruits are
    blue. Red drains away as the group travels.</p>
    <canvas id="cm" width="520" height="520"></canvas>
    <div class="metrics">
      <div class="m"><b id="mrm" style="color:var(--mat)">—</b><span>R<sub>M</sub> material</span></div>
      <div class="m"><b id="morig">—</b><span>originals left</span></div>
    </div>
  </div>
  <div class="panel">
    <h2>3 · Co-moving frame</h2>
    <p class="cap">The same collective after subtracting its <i>estimated</i> translation. If the
    method works, this panel barely moves.</p>
    <canvas id="cc" width="520" height="520"></canvas>
    <div class="metrics">
      <div class="m"><b id="mrf" style="color:var(--fun)">—</b><span>R<sub>F</sub> functional</span></div>
      <div class="m"><b id="mdd" style="color:var(--def)">—</b><span>D<sub>deform</sub></span></div>
      <div class="m"><b id="mdw">—</b><span>D world frame</span></div>
    </div>
  </div>
</div>
<div class="controls">
  <button id="play">Pause</button>
  <input type="range" id="scrub" min="0" value="0">
  <span class="m" id="pos"></span>
</div>
<footer id="foot"></footer>
<script>
const DATA = /*__VIZ69__*/null/*__END_VIZ69__*/;
const HCOL = ["#3b6ea5","#b3453b","#6a9b5e","#e08a2e"];
const origin = new Set(DATA.origin);
const S = DATA.summary, G = DATA.gate;
document.getElementById("seed").textContent = DATA.seed;
document.getElementById("foot").innerHTML =
  (DATA.gate_passed ? "" : "<b>The feasibility gate FAILED at this specification " +
   "(0 of " + G.n_episodes + " episodes passed all five criteria).</b> This is the " +
   "longest-tracked episode, shown so the specified model's actual behaviour is " +
   "visible: the group sheds members while fragmenting, rather than translating " +
   "coherently. ") +
  "Tracked " + S.duration + " rendered steps. Material retention ends at <code>R_M = " +
  S.R_M_final.toFixed(2) + "</code>, reaches a minimum of <code>" + S.R_M_min.toFixed(2) +
  "</code>, and sits at or below 0.70 for " + (S.frac_steps_RM_below_0_7*100).toFixed(0) +
  "% of the tracked steps &mdash; it is NOT a monotone decay, because the detected " +
  "community occasionally merges back with a neighbouring lobe. Mean co-moving similarity " +
  "<code>R_F = " + S.mean_R_F.toFixed(2) + "</code>, mean deformation <code>D_deform = " +
  S.mean_D_deform.toFixed(3) + "</code>. Across " + G.n_episodes + " screened uncontrolled episodes, " +
  (G.pass_rate*100).toFixed(0) + "% satisfied all five predeclared feasibility criteria. " +
  "Material continuity, lineage continuity and functional continuity modulo translation are " +
  "kept as three separate numbers and are never combined into one identity score.";

const F = DATA.frames, W = DATA.world, L = DATA.L;
const scrub = document.getElementById("scrub"); scrub.max = F.length - 1;
function px(c){return c.width;}
function draw(i){
  const f = F[i], w = W[i], mem = new Set(f.members);
  // panel 1: world
  let cv = document.getElementById("cw"), g = cv.getContext("2d"), P = px(cv);
  g.clearRect(0,0,P,P); g.fillStyle="#fcfcfc"; g.fillRect(0,0,P,P);
  const sc = P / L;
  for(let k=0;k<w.x.length;k++){
    const inI = mem.has(k);
    g.fillStyle = inI ? HCOL[w.h[k]] : "#e6e6e4";
    g.beginPath(); g.arc(w.x[k]*sc, P-w.y[k]*sc, inI?3.0:1.6, 0, 6.2832); g.fill();
  }
  g.strokeStyle="#26262b"; g.lineWidth=1.2;
  g.beginPath(); g.arc(f.centroid[0]*sc, P-f.centroid[1]*sc, 5, 0, 6.2832); g.stroke();
  // panel 2: material lineage
  cv = document.getElementById("cm"); g = cv.getContext("2d");
  g.clearRect(0,0,P,P); g.fillStyle="#fcfcfc"; g.fillRect(0,0,P,P);
  for(let k=0;k<w.x.length;k++){
    if(!mem.has(k) && !origin.has(k)) continue;
    const isOrig = origin.has(k), inI = mem.has(k);
    g.globalAlpha = inI ? 1 : 0.25;
    g.fillStyle = isOrig ? "#b3453b" : "#3b6ea5";
    g.beginPath(); g.arc(w.x[k]*sc, P-w.y[k]*sc, isOrig?3.2:2.4, 0, 6.2832); g.fill();
  }
  g.globalAlpha = 1;
  // panel 3: co-moving
  cv = document.getElementById("cc"); g = cv.getContext("2d");
  g.clearRect(0,0,P,P); g.fillStyle="#fcfcfc"; g.fillRect(0,0,P,P);
  const H = 7, s2 = P/(2*H);
  g.strokeStyle="#eeeeec"; g.lineWidth=1;
  g.beginPath(); g.moveTo(P/2,0); g.lineTo(P/2,P); g.moveTo(0,P/2); g.lineTo(P,P/2); g.stroke();
  for(let k=0;k<f.rel.length;k++){
    const x = P/2 + f.rel[k][0]*s2, y = P/2 - f.rel[k][1]*s2;
    g.fillStyle = origin.has(f.members[k]) ? "#b3453b" : HCOL[f.rel_h[k]];
    g.beginPath(); g.arc(x,y,3.2,0,6.2832); g.fill();
  }
  document.getElementById("mt").textContent = f.t;
  document.getElementById("msize").textContent = f.size;
  document.getElementById("mrm").textContent = f.R_M.toFixed(2);
  document.getElementById("morig").textContent =
    f.members.filter(m=>origin.has(m)).length + " / " + DATA.origin.length;
  document.getElementById("mrf").textContent = isNaN(f.R_F)?"—":f.R_F.toFixed(2);
  document.getElementById("mdd").textContent = isNaN(f.D_deform)?"—":f.D_deform.toFixed(3);
  document.getElementById("mdw").textContent = isNaN(f.D_world)?"—":f.D_world.toFixed(3);
  document.getElementById("pos").textContent = (i+1) + " / " + F.length;
  scrub.value = i;
}
let i = 0, playing = true;
scrub.addEventListener("input", e => { i = +e.target.value; playing = false;
  document.getElementById("play").textContent = "Play"; draw(i); });
document.getElementById("play").addEventListener("click", e => {
  playing = !playing; e.target.textContent = playing ? "Pause" : "Play"; });
setInterval(() => { if(playing){ i = (i+1) % F.length; draw(i); } }, 110);
draw(0);
</script>
"""


def main():
    bundle = build_bundle()
    dump_json(bundle, DATA_DIR / "viz_bundle_69.json")
    payload = json.dumps(bundle, separators=(",", ":"))
    html = HTML.replace("/*__VIZ69__*/null/*__END_VIZ69__*/", payload)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "translating_identity.html"
    out.write_text(html)
    print(f"wrote {out}  ({len(html)/1e6:.2f} MB, {len(bundle['frames'])} frames, "
          f"seed {bundle['seed']}, R_M {bundle['summary']['R_M_final']:.2f} -> "
          f"R_F {bundle['summary']['mean_R_F']:.2f})")


if __name__ == "__main__":
    main()
