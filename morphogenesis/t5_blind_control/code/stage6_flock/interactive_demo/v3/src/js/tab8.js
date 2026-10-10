/* Tab 8 -- Contact audit. Geometric (undirected, FOV-free, D<=R) contact vs
   the simulator's actual directed FOV-gated live_edges relation, drawn as
   arrows on the same snapshot -- makes visible why prior "contact" analyses
   (mech_cumulative_contact_edges) never tested the true causal channel. */
(function () {
  "use strict";
  const D = TAB8_DATA;
  let mode = "both"; // "geometric" | "live" | "both"

  function project(size) {
    const xs = Object.values(D.positions).map(p => p[0]), ys = Object.values(D.positions).map(p => p[1]);
    const pad = size * 0.08, inner = size - 2 * pad;
    return (id) => {
      const [x, y] = D.positions[id];
      return [pad + (x / D.L) * inner, pad + (y / D.L) * inner];
    };
  }

  function drawStage() {
    const svg = document.getElementById("t8Svg");
    Viz.clearSvg(svg);
    const size = 420;
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    const xy = project(size);
    const targetSet = new Set(D.target), poolSet = new Set(D.pool20);

    // arrowhead marker
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    defs.innerHTML = `<marker id="arrowLive" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="var(--live)"/></marker>`;
    svg.appendChild(defs);

    if (mode !== "live") {
      D.geometric_contact_pairs.forEach(([p, t]) => {
        const [x1, y1] = xy(p), [x2, y2] = xy(t);
        svg.appendChild(Viz.el("line", { x1, y1, x2, y2, stroke: "var(--geo)", "stroke-width": 1.4, "stroke-dasharray": "3,2", opacity: 0.75 }));
      });
    }
    if (mode !== "geometric") {
      D.live_pool_to_target.forEach(([s, r]) => {
        const [x1, y1] = xy(s), [x2, y2] = xy(r);
        const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1;
        const shrink = 10; // stop short of the receiver glyph so the arrowhead is visible
        const x2s = x2 - dx / len * shrink, y2s = y2 - dy / len * shrink;
        svg.appendChild(Viz.el("line", { x1, y1, x2: x2s, y2: y2s, stroke: "var(--live)", "stroke-width": 1.8, "marker-end": "url(#arrowLive)" }));
      });
    }
    for (const id of [...D.target, ...D.pool20]) {
      const [x, y] = xy(id);
      const h = D.headings[id];
      let fill = "var(--nonparent)", stroke = "var(--nonparent-stroke)", r = 5;
      if (targetSet.has(id)) { fill = "var(--core)"; stroke = "var(--core-stroke)"; }
      else if (D.live_pool_to_target.some(([s]) => s === id)) { fill = "var(--liveparent)"; stroke = "var(--liveparent-stroke)"; }
      Viz.drawBird(svg, x, y, h, r, { fill, stroke, strokeWidth: 1.4, id,
        onHover: (bid, ev) => Viz.showTip(ev, tip(bid)), onLeave: Viz.hideTip });
    }
  }

  function tip(id) {
    const isTarget = D.target.includes(id);
    const outEdges = D.live_pool_to_target.filter(([s]) => s === id).length;
    const geoEdges = D.geometric_contact_pairs.filter(([p]) => p === id).length;
    return `<b>Bird ${id}</b><br>${isTarget ? "target member" : "exterior pool candidate"}<br>` +
      (isTarget ? "" : `live directed edges into target: ${outEdges}<br>geometric contacts with target: ${geoEdges}`);
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">8. Contact audit — geometric proximity vs actual directed causal access</h2>
      <p class="qCaption">Every prior stage's "contact" (mech_cumulative_contact_edges) is undirected, FOV-free distance only.
      The simulator's real influence relation (live_edges) is directed and requires the receiver's own field of view. This is
      state ${D.state_id}: ${D.n_geometric_contact_pairs} geometric contact pairs vs ${D.n_live_directed_into_target} true
      directed live edges into the target.</p>
      <div class="panelBody">
        <div class="stageWrap">
          <div class="stageBox"><svg class="stageSvg" id="t8Svg"></svg></div>
          <div class="methodSelect" id="t8Toggles"></div>
        </div>
        <div class="sideWrap">
          <div class="card">
            <div class="metric"><span>Geometric contact pairs (undirected, D&le;R)</span><b>${D.n_geometric_contact_pairs}</b></div>
            <div class="metric"><span>Live directed edges INTO target</span><b>${D.n_live_directed_into_target}</b></div>
            <div class="metric"><span>Live directed edges OUT OF target</span><b>${D.n_live_directed_out_of_target}</b></div>
            <p class="footnote">${D.note}</p>
          </div>
        </div>
      </div>`;
    const toggles = document.getElementById("t8Toggles");
    [["both", "Both"], ["geometric", "Geometric only"], ["live", "Live directed only"]].forEach(([key, label]) => {
      const b = document.createElement("button");
      b.className = "methodChip" + (mode === key ? " active" : "");
      b.textContent = label;
      b.addEventListener("click", () => {
        mode = key;
        toggles.querySelectorAll(".methodChip").forEach(x => x.classList.remove("active"));
        b.classList.add("active");
        drawStage();
      });
      toggles.appendChild(b);
    });
    drawStage();
  }

  window.Tabs = window.Tabs || {};
  window.Tabs.tab8 = {
    legend: [
      { shape: "dot", color: "var(--core)", label: "target member" },
      { shape: "dot", color: "var(--liveparent)", label: "live exterior causal parent" },
      { shape: "dot", color: "var(--nonparent)", label: "exterior pool, no live edge" },
      { shape: "dot", color: "var(--geo)", label: "geometric contact (dashed)" },
      { shape: "dot", color: "var(--live)", label: "true directed live edge (arrow)" },
    ],
    render,
    onActivate() { Viz.TL.bind("tab8", null); },
    provenanceHtml() {
      return Viz.provRow("State", D.state_id) + Viz.provRow("R (interaction radius)", D.R) +
        Viz.provRow("Note", D.note) +
        Viz.provRow("Source", "final_translating_flock_closure/code/live_edge_utils.py + moving_flock.py live_edges()");
    },
  };
})();
