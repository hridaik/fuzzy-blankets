/* Tab 1 -- Boundary. "Can trajectories reveal a compact screen around a
   collective?" Fixed seed-2 no_control flock; interior + candidate
   boundaries only appear at the stored identification time. */
(function () {
  "use strict";
  const D = TAB1_DATA;
  const toggles = { predictive: true, dynamical: true, fiedler: true };
  const arrows = ["↑", "↓", "←", "→"];
  let previewId = null;       // candidate id being dashed-previewed (auto-cycle or manual click)
  let previewManual = false;  // true once the viewer has taken control by clicking a point
  let inspectId = null;       // bird whose structural neighbors are drawn
  let cycleTimer = null;
  const byId = {}; D.screening.candidates.forEach((c) => { byId[c.id] = c; });
  // A handful of visually-distinct real candidates to auto-cycle through
  // during the observation window (excludes established_I0, the committed answer).
  const AUTO_CANDIDATES = D.screening.candidates
    .filter((c) => c.label !== "established_I0")
    .filter((c, i, arr) => arr.findIndex((x) => x.label === c.label) === i)
    .slice(0, 6);

  function classify(id) {
    return {
      inInterior: D.roles.interior.includes(id),
      inDynamical: D.roles.dynamical_shell.includes(id),
      inFiedler: D.roles.fiedler.includes(id),
      inPredictive: D.roles.predictive.includes(id),
    };
  }

  function drawStage(t) {
    const svg = document.getElementById("t1Svg");
    Viz.clearSvg(svg);
    const size = 400;
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    const identified = t >= D.timeline.identify;
    document.getElementById("t1ScanBadge").style.display = identified ? "none" : "block";
    const z = D.headings[Math.min(t, D.headings.length - 1)];
    const r = Math.max(4, size / D.lattice.L * 0.30);

    if (inspectId !== null) Viz.drawNeighborLines(svg, D.lattice.positions, D.lattice.L, size, inspectId, D.neighbors);

    for (let id = 0; id < D.lattice.nn; id++) {
      const [x, y] = Viz.latticeXY(D.lattice.positions, D.lattice.L, id, size);
      const cls = classify(id);
      let fill = "#d7d7d3", stroke = "#aaaaa4", sw = 1, halo = null, ring = null;
      if (identified && cls.inInterior) { fill = "var(--core)"; stroke = "var(--core-stroke)"; sw = 2; }
      if (identified && cls.inDynamical && toggles.dynamical) halo = "var(--shell-stroke)";
      if (identified && cls.inFiedler && toggles.fiedler) ring = "var(--fiedler)";
      if (identified && cls.inPredictive && toggles.predictive) {
        stroke = "var(--predictive)"; sw = 2.4;
      }
      if (inspectId === id) ring = "#111";
      const g = Viz.drawBird(svg, x, y, z[id], r, { fill, stroke, strokeWidth: sw, halo, ring, id,
        onClick: (bid) => { inspectId = inspectId === bid ? null : bid; drawStage(Viz.TL.t); },
        onHover: (bid, ev) => Viz.showTip(ev, birdTip(bid, cls, z[bid])),
        onLeave: Viz.hideTip });
      // dashed preview overlay -- candidate-under-test, drawn ON TOP of
      // (not instead of) whatever is already committed, so the viewer can
      // compare "this candidate's proposal" against the real answer at once.
      const prev = previewId !== null ? byId[previewId] : null;
      if (prev) {
        if (prev.I.includes(id)) {
          const pr = Viz.el("circle", { cx: x, cy: y, r: r * 1.35, fill: "none", stroke: "var(--core-stroke)",
            "stroke-width": 1.6, "stroke-dasharray": "2.5,2" });
          svg.appendChild(pr);
        }
        if (prev.B_hat_pred.includes(id)) {
          const pr = Viz.el("circle", { cx: x, cy: y, r: r * 2.05, fill: "none", stroke: "var(--predictive)",
            "stroke-width": 2, "stroke-dasharray": "2.5,2" });
          svg.appendChild(pr);
        }
      }
    }
  }

  function birdTip(id, cls, h) {
    const roles = [];
    if (cls.inInterior) roles.push("interior");
    if (cls.inDynamical) roles.push("dynamical shell B^D");
    if (cls.inFiedler) roles.push("Fiedler B^F");
    if (cls.inPredictive) roles.push("predictive B^pred");
    return `<b>Bird ${id}</b><br>Heading ${arrows[h]}<br>${roles.length ? roles.join(", ") : "exterior"}<br><i>click to inspect neighbors</i>`;
  }

  function updateScanCaption(t) {
    const el = document.getElementById("t1ScanCaption");
    const identified = t >= D.timeline.identify;
    if (identified || previewManual) { el.style.display = "none"; return; }
    el.style.display = "";
    if (previewId !== null && !previewManual) {
      const c = byId[previewId];
      el.innerHTML = `Testing candidate boundary: <b>${c.label}</b> (interior size ${c.I.length}, B̂ size ${c.boundary_size}, excess loss ${Viz.fmtNum(c.excess_loss_test)})`;
    } else {
      el.innerHTML = "Scanning… evaluating candidate boundaries in the background (dashed = under test, not yet the answer).";
    }
  }

  function updatePreviewBanner() {
    const el = document.getElementById("t1PreviewBanner");
    if (!previewManual || previewId === null) { el.style.display = "none"; return; }
    const c = byId[previewId];
    el.style.display = "";
    el.innerHTML = `<span>Previewing <b>${c.label}</b> — interior ${c.I.length}, B̂ ${c.boundary_size}, excess loss ${Viz.fmtNum(c.excess_loss_test)}</span>
      <button class="chip" id="t1ClearPreview">Clear</button>`;
    document.getElementById("t1ClearPreview").addEventListener("click", () => { previewManual = false; previewId = null; drawStage(Viz.TL.t); drawScatter(); updatePreviewBanner(); updateScanCaption(Viz.TL.t); });
  }

  function startAutoCycle() {
    stopAutoCycle();
    let idx = 0;
    cycleTimer = setInterval(() => {
      const t = Viz.TL.t;
      if (t >= D.timeline.identify || previewManual) { stopAutoCycle(); if (!previewManual) { previewId = null; drawStage(t); drawScatter(); updateScanCaption(t); } return; }
      previewId = AUTO_CANDIDATES[idx % AUTO_CANDIDATES.length].id;
      idx++;
      drawStage(t); drawScatter(); updateScanCaption(t);
    }, 1500);
  }
  function stopAutoCycle() { if (cycleTimer) clearInterval(cycleTimer); cycleTimer = null; }

  function drawScatter() {
    const svg = document.getElementById("t1Scatter");
    Viz.clearSvg(svg);
    const w = 460, h = 150, padL = 34, padB = 22, padT = 10, padR = 10;
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    const cands = D.screening.candidates;
    const maxSize = Math.max(...cands.map((c) => c.boundary_size), 3);
    const maxLoss = Math.max(...cands.map((c) => c.excess_loss_test), D.screening.delta_pred * 1.2);
    const X = (s) => padL + (s / maxSize) * (w - padL - padR);
    const Y = (l) => h - padB - (Math.max(0, l) / maxLoss) * (h - padT - padB);
    svg.appendChild(Viz.el("line", { x1: padL, y1: h - padB, x2: w - padR, y2: h - padB, stroke: "#ccc" }));
    svg.appendChild(Viz.el("line", { x1: padL, y1: padT, x2: padL, y2: h - padB, stroke: "#ccc" }));
    svg.appendChild(Viz.el("text", { x: w / 2, y: h - 4, "font-size": 9, fill: "var(--muted)", "text-anchor": "middle" })).textContent = "boundary size (selected sources)";
    const ylab = Viz.el("text", { x: 10, y: padT + 8, "font-size": 9, fill: "var(--muted)" });
    ylab.textContent = "excess loss"; svg.appendChild(ylab);
    const ty = Y(D.screening.delta_pred);
    svg.appendChild(Viz.el("line", { x1: padL, y1: ty, x2: w - padR, y2: ty, stroke: "var(--warn)", "stroke-dasharray": "3,2", "stroke-width": 1 }));
    svg.appendChild(Viz.el("text", { x: w - padR, y: ty - 3, "font-size": 8, fill: "var(--warn)", "text-anchor": "end" })).textContent = "tolerance δ=" + D.screening.delta_pred;
    cands.forEach((c) => {
      const isSel = previewId === c.id;
      const dot = Viz.el("circle", { cx: X(c.boundary_size), cy: Y(c.excess_loss_test), r: isSel ? 5 : 3,
        fill: isSel ? "var(--core-stroke)" : "#94a3b8", "fill-opacity": isSel ? 1 : 0.75,
        stroke: isSel ? "#111" : "none", "stroke-width": 1.4 });
      dot.style.cursor = "pointer";
      dot.addEventListener("mousemove", (ev) => Viz.showTip(ev, `<b>${c.label}</b><br>size ${c.boundary_size}, excess loss ${Viz.fmtNum(c.excess_loss_test)}<br><i>click to view this boundary</i>`));
      dot.addEventListener("mouseleave", Viz.hideTip);
      dot.addEventListener("click", () => {
        stopAutoCycle();
        previewManual = true;
        previewId = c.id;
        drawStage(Viz.TL.t); drawScatter(); updatePreviewBanner(); updateScanCaption(Viz.TL.t);
      });
      svg.appendChild(dot);
    });
    const refs = [
      { key: "dynamical_shell", size: D.screening.reference_sizes.dynamical_shell, color: "var(--shell-stroke)", label: "B^D" },
      { key: "fiedler", size: D.screening.reference_sizes.fiedler, color: "var(--fiedler)", label: "B^F" },
      { key: "predictive", size: D.screening.reference_sizes.predictive, color: "var(--predictive)", label: "B^pred" },
    ];
    const foundExcess = { dynamical_shell: 0, fiedler: null, predictive: null };
    cands.forEach((c) => { if (c.label === "established_I0") foundExcess.predictive = c.excess_loss_test; });
    refs.forEach((rf) => {
      let y = rf.key === "dynamical_shell" ? Y(0.0002) : rf.key === "predictive" ? Y(foundExcess.predictive || 0) : Y(0.02);
      svg.appendChild(Viz.el("circle", { cx: X(rf.size), cy: y, r: 4.3, fill: "none", stroke: rf.color, "stroke-width": 2 }));
      svg.appendChild(Viz.el("text", { x: X(rf.size), y: y - 6, "font-size": 8.5, fill: rf.color, "text-anchor": "middle" })).textContent = rf.label;
    });
  }

  function drawGeneralization() {
    const wrap = document.getElementById("t1Gen");
    wrap.innerHTML = "";
    const rows = [
      { k: "B_hat", label: "Predictive (B̂)", color: "var(--predictive)" },
      { k: "B_D", label: "Dynamical shell", color: "var(--shell-stroke)" },
      { k: "B_F", label: "Fiedler", color: "var(--fiedler)" },
      { k: "random_matched_mean", label: "Random, size-matched", color: "#9aa1ab" },
    ];
    const maxV = Math.max(...rows.map((r) => Math.abs(D.generalization.mean_excess_loss[r.k])), 0.001);
    rows.forEach((r) => {
      const v = D.generalization.mean_excess_loss[r.k];
      const row = document.createElement("div");
      row.style.cssText = "display:flex;align-items:center;gap:6px;margin:3px 0;font-size:10.5px;";
      const barMax = 120;
      const w = Math.max(1, Math.abs(v) / maxV * barMax);
      row.innerHTML = `<div style="width:98px;color:var(--muted);">${r.label}</div>
        <div style="width:${barMax}px;background:#eee;border-radius:3px;overflow:hidden;">
          <div style="width:${w}px;height:9px;background:${r.color};"></div>
        </div>
        <div style="font-variant-numeric:tabular-nums;">${v.toFixed(4)}</div>`;
      wrap.appendChild(row);
    });
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">1. Boundary — can trajectories reveal a compact screen around a collective?</h2>
      <p class="qCaption">Observe the trajectory. Ask which exterior variables still improve prediction. A good predictive boundary removes that residual information with few states.</p>
      <div class="panelBody">
        <div class="stageWrap">
          <div class="stageBox">
            <svg class="stageSvg" id="t1Svg"></svg>
            <div class="scanBadge" id="t1ScanBadge">Scanning… observation window</div>
          </div>
          <div class="timelineSlot" id="tab1TimelineSlot"></div>
          <div class="scanCaption" id="t1ScanCaption"></div>
          <div class="previewBanner" id="t1PreviewBanner" style="display:none;"></div>
          <div class="methodSelect" id="t1Toggles"></div>
          <div class="card">
            <h3>Predictive screening (same flock) — excess loss vs. boundary size <span style="font-weight:400;color:var(--muted);">(click a point to view that boundary)</span></h3>
            <svg id="t1Scatter" viewBox="0 0 460 150" style="width:100%;height:auto;"></svg>
          </div>
        </div>
        <div class="sideWrap">
          <div class="card">
            <h3>Headline (40 trajectories, seed-2 regime)</h3>
            <div class="metric"><span>mean log-loss, full exterior</span><b>${D.headline.mean_logloss_full.toFixed(4)}</b></div>
            <div class="metric"><span>mean log-loss, B^D</span><b>${D.headline.mean_logloss_BD.toFixed(4)}</b></div>
            <div class="metric"><span>mean log-loss, B^F</span><b>${D.headline.mean_logloss_BF.toFixed(4)}</b></div>
            <p class="footnote">${D.headline.interpretation}</p>
          </div>
          <div class="card">
            <h3>Generalization — mean excess loss, 3 held-out seeds</h3>
            <div id="t1Gen"></div>
            <p class="footnote">Seeds ${D.generalization.held_out_seeds.join(", ")}, never used to tune the selection rule. Predictive boundary (B̂) tracks B^D far better than the Fiedler proposal, which performs about as poorly as a size-matched random set.</p>
          </div>
        </div>
      </div>
    `;
    const togglesWrap = document.getElementById("t1Toggles");
    [["predictive", "Predictive boundary"], ["dynamical", "Dynamical shell"], ["fiedler", "Fiedler proposal"]].forEach(([key, label]) => {
      const b = document.createElement("button");
      b.className = "methodChip active";
      b.textContent = label;
      b.addEventListener("click", () => { toggles[key] = !toggles[key]; b.classList.toggle("active", toggles[key]); drawStage(Viz.TL.t); });
      togglesWrap.appendChild(b);
    });
    drawScatter();
    drawGeneralization();
  }

  window.Tabs = window.Tabs || {};
  window.Tabs.tab1 = {
    legend: [
      { shape: "dot", color: "#d7d7d3", label: "ordinary bird" },
      { shape: "dot", color: "var(--core)", label: "interior" },
      { shape: "ring", color: "var(--predictive)", label: "predictive boundary" },
      { shape: "ring", color: "var(--fiedler)", label: "Fiedler proposal" },
      { shape: "ring", color: "var(--shell-stroke)", label: "dynamical shell" },
    ],
    render,
    onActivate() {
      Viz.TL.bind("tab1", {
        tMin: 0, tMax: D.headings.length - 1,
        phases: [{ key: "observe", label: "Observe", t: 0 }, { key: "identified", label: "Identified", t: D.timeline.identify }],
        onTick: (t) => { drawStage(t); updateScanCaption(t); },
      });
      updatePreviewBanner();
      startAutoCycle();
    },
    onDeactivate() { stopAutoCycle(); },
    provenanceHtml() {
      const p = D.provenance, g = D.generalization;
      return Viz.provRow("Stage / source", p.trajectory_source) +
        Viz.provRow("Predictive boundary source", p.predictive_boundary_source) +
        Viz.provRow("Generalization source", p.generalization_source) +
        Viz.provRow("Screening headline", p.screening_headline_source) +
        Viz.provRow("Representativeness", p.note) +
        Viz.provRow("Held-out seeds", g.held_out_seeds.join(", ") + ` (shortlist_k=${g.shortlist_k}, delta_tol_frac=${g.delta_tol_frac})`) +
        Viz.provRow("Overlays", "Interior/B^D/B^F/B^pred are blind, frozen results (roles.core / dynamic_shell / fiedler from the seed-2 bundle; B^pred from the 6.7 predictive-boundary panel's established_I0 candidate). Dashed rings are a preview of a DIFFERENT candidate's proposal, not a reference/oracle overlay.");
    },
  };
})();
