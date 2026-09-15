/* Tab 4 -- Collective landscape. "Which candidate regions actually look
   like coherent, individuated collectives?" Not playback-first: an
   interactive scatter over five independent axes (C,G,L,D,Q), no timeline. */
(function () {
  "use strict";
  const D = TAB4_DATA;
  const AXES = { C: "coherence C", G: "internal integration G", L: "exterior leakage L", D: "exterior contrast D", Q: "clumpness Q" };
  let axX = D.default_axes.x, axY = D.default_axes.y;
  let selected = null;
  let activeCategory = null;
  const byId = {}; D.rows.forEach((r) => { byId[r.id] = r; });

  function drawScatter() {
    const svg = document.getElementById("t4Svg");
    Viz.clearSvg(svg);
    const w = 520, h = 460, pad = 36;
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    const xs = D.rows.map((r) => r[axX]), ys = D.rows.map((r) => r[axY]);
    const xlo = Math.min(...xs), xhi = Math.max(...xs), ylo = Math.min(...ys), yhi = Math.max(...ys);
    const X = (v) => pad + (v - xlo) / (xhi - xlo || 1) * (w - 2 * pad);
    const Y = (v) => h - pad - (v - ylo) / (yhi - ylo || 1) * (h - 2 * pad);
    svg.appendChild(Viz.el("line", { x1: pad, y1: h - pad, x2: w - pad, y2: h - pad, stroke: "#ccc" }));
    svg.appendChild(Viz.el("line", { x1: pad, y1: pad, x2: pad, y2: h - pad, stroke: "#ccc" }));
    svg.appendChild(Viz.el("text", { x: w / 2, y: h - 8, "font-size": 10, fill: "var(--muted)", "text-anchor": "middle" })).textContent = AXES[axX];
    const yl = Viz.el("text", { x: -h / 2, y: 12, "font-size": 10, fill: "var(--muted)", "text-anchor": "middle", transform: "rotate(-90)" });
    yl.textContent = AXES[axY]; svg.appendChild(yl);
    const exampleIds = new Set((activeCategory ? D.examples[activeCategory] : []).map((r) => r.id));
    D.rows.forEach((r) => {
      const qColor = qToColor(r.Q);
      const isEx = exampleIds.has(r.id);
      const dot = Viz.el("circle", { cx: X(r[axX]), cy: Y(r[axY]), r: r.id === selected ? 5.5 : isEx ? 4.5 : 3,
        fill: qColor, "fill-opacity": isEx || r.id === selected ? 1 : 0.55,
        stroke: r.id === selected ? "#111" : isEx ? "#555" : "none", "stroke-width": 1.6 });
      dot.style.cursor = "pointer";
      dot.addEventListener("mousemove", (ev) => Viz.showTip(ev, rowTip(r)));
      dot.addEventListener("mouseleave", Viz.hideTip);
      dot.addEventListener("click", () => selectRow(r.id));
      svg.appendChild(dot);
    });
  }

  function qToColor(q) {
    // low Q (stringy) -> orange-ish, high Q (compact) -> teal-ish; neutral, not a role color.
    const t = Math.max(0, Math.min(1, q));
    const r = Math.round(240 - t * 140), g = Math.round(160 + t * 40), b = Math.round(120 + t * 90);
    return `rgb(${r},${g},${b})`;
  }

  function rowTip(r) {
    return `<b>seed ${r.seed} / ${r.condition} / ${r.src}</b><br>C ${r.C.toFixed(2)} G ${r.G.toFixed(2)} L ${r.L.toFixed(3)}<br>D ${r.D.toFixed(2)} Q ${r.Q.toFixed(2)} (n=${r.n})`;
  }

  function selectRow(id) {
    selected = id;
    const r = byId[id];
    drawScatter();
    drawThumb("t4Thumb", r, 220);
    drawStrip(r);
    document.querySelectorAll("#t4ExampleStrip .miniThumb").forEach((el) => el.classList.toggle("active", +el.dataset.id === id));
  }

  /* Triangles with real headings (representative_z, shared by every candidate
     from the same seed/condition) + the candidate's own boundary ring --
     consistent glyph language with every other tab, not bare dots. */
  function drawThumb(svgId, r, size) {
    const svg = document.getElementById(svgId);
    Viz.clearSvg(svg);
    if (!r) return;
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    const z = D.representative_z[`${r.seed}_${r.condition}`] || [];
    const inSet = new Set(r.node_ids);
    const bSet = new Set(r.boundary_ids || []);
    const rad = Math.max(2, size / D.lattice.L * 0.30);
    for (let id = 0; id < D.lattice.nn; id++) {
      const [x, y] = Viz.latticeXY(D.lattice.positions, D.lattice.L, id, size);
      const inside = inSet.has(id);
      const onB = bSet.has(id);
      const fill = inside ? "var(--core)" : "#e5e5e2";
      const stroke = inside ? "var(--core-stroke)" : onB ? "var(--shell-stroke)" : "#c7c7c2";
      Viz.drawBird(svg, x, y, z[id] || 0, inside ? rad : rad * 0.75, { fill, stroke, strokeWidth: onB ? 2 : 1,
        ring: onB && !inside ? "var(--shell-stroke)" : null });
    }
  }

  function drawStrip(r) {
    const wrap = document.getElementById("t4Strip");
    if (!r) { wrap.innerHTML = ""; return; }
    const keys = ["C", "G", "L", "D", "Q"];
    wrap.innerHTML = `<p class="footnote" style="margin:0 0 4px;">seed ${r.seed}, ${r.condition}, ${r.src}, n=${r.n}</p>` + keys.map((k) => {
      const v = r[k];
      const pct = Math.max(2, Math.min(100, Math.abs(v) * 100));
      return `<div style="display:flex;align-items:center;gap:5px;font-size:10.5px;margin:2px 0;">
        <div style="width:14px;color:var(--muted);">${k}</div>
        <div style="flex:1;background:#eee;border-radius:3px;overflow:hidden;"><div style="width:${pct}%;height:7px;background:var(--accent);"></div></div>
        <div style="width:42px;text-align:right;font-variant-numeric:tabular-nums;">${v.toFixed(3)}</div>
      </div>`;
    }).join("");
  }

  function renderExampleStrip(key) {
    activeCategory = key;
    const wrap = document.getElementById("t4ExampleStrip");
    wrap.innerHTML = "";
    const rows = D.examples[key] || [];
    rows.forEach((r) => {
      const cell = document.createElement("div");
      cell.className = "miniThumb";
      cell.dataset.id = r.id;
      cell.style.cssText = "display:flex;flex-direction:column;align-items:center;gap:3px;cursor:pointer;padding:5px;border-radius:7px;border:1px solid transparent;";
      const svgId = "t4Mini" + r.id.replace(/[^a-zA-Z0-9]/g, "");
      cell.innerHTML = `<svg id="${svgId}" viewBox="0 0 130 130" style="width:100%;max-width:130px;aspect-ratio:1/1;"></svg>
        <div style="font-size:9.5px;color:var(--muted);text-align:center;">seed ${r.seed}<br>${r.condition}</div>`;
      cell.addEventListener("click", () => selectRow(r.id));
      wrap.appendChild(cell);
      drawThumb(svgId, r, 130);
    });
    drawScatter();
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">4. Collective landscape — which candidate regions look like coherent, individuated collectives?</h2>
      <p class="qCaption">Five independent axes, never combined into one score. Compact clumps and coherent snakes are both legitimate statistical patterns.</p>
      <div class="panelBody">
        <div class="stageWrap">
          <div class="axisRow">
            <label>x: <select class="axisSel" id="t4X"></select></label>
            <label>y: <select class="axisSel" id="t4Y"></select></label>
            <span style="color:var(--muted);font-size:10.5px;">dot color = Q (clumpness): orange = stringy, teal = compact</span>
          </div>
          <svg class="stageSvg" id="t4Svg" style="aspect-ratio: 520/460;"></svg>
          <div class="methodSelect" id="t4Examples"></div>
          <div id="t4ExampleStrip" style="display:flex;gap:10px;flex-wrap:wrap;"></div>
        </div>
        <div class="sideWrap">
          <div class="card">
            <h3>Selected candidate</h3>
            <svg id="t4Thumb" viewBox="0 0 220 220" style="width:100%;max-width:220px;aspect-ratio:1/1;"></svg>
            <div id="t4Strip" style="margin-top:6px;"></div>
          </div>
          <div class="card">
            <h3>Reading Q (clumpness)</h3>
            <p class="footnote">Compact blob → high Q. Elongated / diagonal snake → low Q. Both can score highly on C/G/L/D -- clumpness is a separate morphology axis, not a filter.</p>
          </div>
        </div>
      </div>
    `;
    const xSel = document.getElementById("t4X"), ySel = document.getElementById("t4Y");
    Object.keys(AXES).forEach((k) => {
      xSel.appendChild(new Option(AXES[k], k, k === axX, k === axX));
      ySel.appendChild(new Option(AXES[k], k, k === axY, k === axY));
    });
    xSel.addEventListener("change", () => { axX = xSel.value; drawScatter(); });
    ySel.addEventListener("change", () => { axY = ySel.value; drawScatter(); });

    const exWrap = document.getElementById("t4Examples");
    const labels = { compact_clump: "Compact clump", coherent_but_hollow: "Coherent but hollow", snake_like: "Snake-like connected", weak_noisy: "Weak / noisy" };
    Object.keys(labels).forEach((key) => {
      if (!D.examples[key] || !D.examples[key].length) return;
      const b = document.createElement("button");
      b.className = "methodChip";
      b.textContent = labels[key] + ` (${D.examples[key].length})`;
      b.addEventListener("click", () => {
        document.querySelectorAll("#t4Examples .methodChip").forEach((x) => x.classList.remove("active"));
        b.classList.add("active");
        renderExampleStrip(key);
        if (D.examples[key] && D.examples[key].length) selectRow(D.examples[key][0].id);
      });
      exWrap.appendChild(b);
    });
    drawScatter();
    const firstKey = Object.keys(labels).find((k) => D.examples[k] && D.examples[k].length);
    if (firstKey) {
      exWrap.firstChild && exWrap.firstChild.classList.add("active");
      renderExampleStrip(firstKey);
      selectRow(D.examples[firstKey][0].id);
    }
  }

  window.Tabs = window.Tabs || {};
  window.Tabs.tab4 = {
    legend: [
      { shape: "dot", color: "rgb(100,200,210)", label: "high clumpness Q" },
      { shape: "dot", color: "rgb(240,160,120)", label: "low clumpness Q" },
      { shape: "dot", color: "var(--core)", label: "selected candidate's interior" },
      { shape: "ring", color: "var(--shell-stroke)", label: "selected candidate's boundary" },
    ],
    render,
    onActivate() { Viz.TL.bind("tab4", null); },
    provenanceHtml() {
      const p = D.provenance;
      return Viz.provRow("Source", p.source) + Viz.provRow("Metrics code", p.metrics_code) +
        Viz.provRow("Q derivation", p.q_derivation) +
        Viz.provRow("Heading note", p.heading_note) +
        Viz.provRow("Candidates shown", `${p.n_candidates_shown} (sampled every ${p.sample_stride} of ${p.n_candidates_full_per_snapshot} per seed/condition snapshot)`) +
        Viz.provRow("Labeled snake example", p.labeled_snake_trajectory);
    },
  };
})();
