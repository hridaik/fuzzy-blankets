/* Tab 2 -- Causal access. "Which exterior states can move the collective
   toward a chosen target?" A single fixed-interior reference state (Stage
   6.10 audit, seed 17, t=60) -- not a trajectory, so no timeline: this is
   an analytic snapshot, exactly like the science that produced it (one
   state, many candidate interventions compared against the same baseline). */
(function () {
  "use strict";
  const D = TAB2_DATA;
  let mode = "authority"; // "causal" | "authority"
  let tau = "2";
  let selected = null;
  let inspectId = null;
  const TOP_K = 5;
  const arrows = ["↑", "↓", "←", "→"];
  const byId = {}; D.candidates.forEach((c) => { byId[c.id] = c; });

  function value(c) { return mode === "causal" ? c.causal_effect : c.authority[tau]; }

  function topKIds() {
    return D.candidates.slice().sort((a, b) => value(b) - value(a)).slice(0, TOP_K).map((c) => c.id);
  }

  function drawStage() {
    const svg = document.getElementById("t2Svg");
    Viz.clearSvg(svg);
    const size = 400;
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    const interiorSet = new Set(D.interior);
    const candIds = new Set(D.candidates.map((c) => c.id));
    const topK = new Set(topKIds());
    if (inspectId !== null) Viz.drawNeighborLines(svg, D.lattice.positions, D.lattice.L, size, inspectId, D.lattice.neighbors);
    for (let id = 0; id < D.lattice.nn; id++) {
      const [x, y] = Viz.latticeXY(D.lattice.positions, D.lattice.L, id, size);
      let fill = "#d7d7d3", stroke = "#aaaaa4", sw = 1, ring = null, r = Math.max(3, size / D.lattice.L * 0.30);
      if (interiorSet.has(id)) { fill = "var(--core)"; stroke = "var(--core-stroke)"; sw = 1.6; }
      else if (candIds.has(id)) {
        fill = "#eee8fa"; stroke = "var(--controlif)"; sw = 1.4;
        if (topK.has(id)) { fill = "var(--controlif)"; stroke = "var(--controlif-stroke)"; sw = 2.2; }
      }
      if (selected === id || inspectId === id) ring = "#111";
      const h = D.headings[id];
      Viz.drawBird(svg, x, y, h, r, { fill, stroke, strokeWidth: sw, ring, id,
        onClick: (bid) => { selected = bid; inspectId = inspectId === bid ? null : bid; drawStage(); drawBars(); drawBreakdown(); },
        onHover: (bid, ev) => Viz.showTip(ev, candTip(bid)), onLeave: Viz.hideTip });
    }
  }

  function candTip(id) {
    const c = byId[id];
    if (!c) return `<b>Bird ${id}</b><br>interior<br><i>click to inspect neighbors</i>`;
    return `<b>Bird ${id}</b> (candidate)<br>causal effect (KL, 1-step): ${Viz.fmtNum(c.causal_effect)}<br>authority τ=2: ${Viz.fmtNum(c.authority["2"])}<br>authority τ=4: ${Viz.fmtNum(c.authority["4"])}<br>authority τ=8: ${Viz.fmtNum(c.authority["8"])}<br><i>click to inspect neighbors</i>`;
  }

  function drawBars() {
    const wrap = document.getElementById("t2Bars");
    wrap.innerHTML = "";
    const topK = new Set(topKIds());
    const sorted = D.candidates.slice().sort((a, b) => value(b) - value(a));
    const maxAbs = Math.max(...sorted.map((c) => Math.abs(value(c))), 1e-6);
    const barMaxPx = 140;
    sorted.forEach((c) => {
      const v = value(c);
      const w = Math.abs(v) / maxAbs * barMaxPx;
      const positive = v >= 0;
      const inTopK = topK.has(c.id);
      const color = mode === "causal" ? "var(--accent)" : (positive ? "var(--good)" : "var(--bad)");
      const row = document.createElement("div");
      row.style.cssText = "display:flex;align-items:center;gap:5px;font-size:10px;padding:1.5px 2px;cursor:pointer;border-radius:4px;" +
        (selected === c.id ? "background:#eef2ff;" : inTopK ? "background:#f4f1fb;" : "");
      row.innerHTML = `<div style="width:32px;color:var(--muted);font-weight:${inTopK ? 700 : 400};">${inTopK ? "★" : ""}#${c.id}</div>
        <div style="width:${barMaxPx}px;background:#f1f1ef;border-radius:2px;overflow:hidden;">
          <div style="width:${Math.max(w, v !== 0 ? 1.5 : 0)}px;height:8px;background:${color};"></div>
        </div>
        <div style="font-variant-numeric:tabular-nums;width:56px;">${Viz.fmtNum(v)}</div>`;
      row.addEventListener("mouseenter", () => { selected = c.id; drawStage(); drawBars(); drawBreakdown(); });
      row.addEventListener("click", () => { selected = c.id; drawStage(); drawBars(); drawBreakdown(); });
      wrap.appendChild(row);
    });
  }

  function drawBreakdown() {
    const wrap = document.getElementById("t2Breakdown");
    const card = document.getElementById("t2BreakdownCard");
    if (selected === null) { card.style.display = "none"; return; }
    const c = byId[selected];
    if (!c) { card.style.display = "none"; return; }
    card.style.display = "";
    if (mode !== "causal") {
      wrap.innerHTML = `<p class="footnote">Per-interior-bird split is defined for direct causal effect (it comes from summing a per-target KL breakdown). Switch to "Direct causal effect" to see it for bird #${c.id}.</p>`;
      return;
    }
    const total = c.causal_effect;
    wrap.innerHTML = `<p class="footnote">Bird #${c.id}'s 1-step causal effect (total ${Viz.fmtNum(total)}), split by which interior bird receives it:</p>` +
      c.per_interior_bird.map((pb) => {
        const pct = total > 0 ? Math.max(2, Math.abs(pb.kl) / total * 100) : 0;
        return `<div style="display:flex;align-items:center;gap:5px;font-size:10px;margin:1.5px 0;">
          <div style="width:46px;color:var(--muted);">bird ${pb.bird}</div>
          <div style="flex:1;background:#eee;border-radius:2px;overflow:hidden;"><div style="width:${pct}%;height:7px;background:var(--core-stroke);"></div></div>
          <div style="width:52px;text-align:right;font-variant-numeric:tabular-nums;">${Viz.fmtNum(pb.kl)}</div>
        </div>`;
      }).join("");
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">2. Causal access — which exterior states can move the collective toward a chosen target?</h2>
      <p class="qCaption">Active perturbations estimate task-directed authority. Prediction ≠ causation ≠ useful control.</p>
      <div class="panelBody">
        <div class="stageWrap">
          <div class="stageBox"><svg class="stageSvg" id="t2Svg"></svg></div>
          <div class="methodSelect" id="t2Toggles"></div>
          <div class="card" id="t2BreakdownCard" style="display:none;">
            <h3>Per-interior-bird split</h3>
            <div id="t2Breakdown"></div>
          </div>
        </div>
        <div class="sideWrap">
          <div class="card targetBadge">
            <span class="arrow">${arrows[D.h_star]}</span>
            <span class="lbl">Target heading h*</span>
          </div>
          <div class="card">
            <h3 id="t2BarsTitle">Sorted target authority (τ=2)</h3>
            <p class="footnote" style="margin:0 0 4px;">★ = top ${TOP_K} candidates by the current metric — the set an actuator policy choosing by this criterion alone would pick.</p>
            <div id="t2Bars" style="max-height:300px;overflow-y:auto;"></div>
          </div>
          <div class="card">
            <div class="metric"><span>ρ(causal effect, authority)</span><b>${D.provenance.rho_kl_authority_this_state.toFixed(2)}</b></div>
            <div class="metric"><span>pooled across 8 audited states</span><b>${D.provenance.rho_kl_authority_pooled_8_states.toFixed(2)}</b></div>
            <p class="footnote">Correlation well below 1: candidates ranked highly by causal influence are not reliably the ones with the most signed, target-directed authority. Notice the ★ top-${TOP_K} sets barely overlap between the two toggles.</p>
          </div>
        </div>
      </div>
    `;
    const toggles = document.getElementById("t2Toggles");
    const modeBtns = [["causal", "Direct causal effect (1-step)"], ["authority", "Target authority"]];
    modeBtns.forEach(([key, label]) => {
      const b = document.createElement("button");
      b.className = "methodChip" + (mode === key ? " active" : "");
      b.textContent = label;
      b.addEventListener("click", () => {
        mode = key;
        toggles.querySelectorAll(".methodChip").forEach((x) => x.classList.remove("active"));
        b.classList.add("active");
        tauWrap.style.display = mode === "authority" ? "flex" : "none";
        document.getElementById("t2BarsTitle").textContent = mode === "causal" ? "Sorted direct causal effect (|KL|, 1-step)" : `Sorted target authority (τ=${tau})`;
        drawStage(); drawBars(); drawBreakdown();
      });
      toggles.appendChild(b);
    });
    const tauWrap = document.createElement("span");
    tauWrap.style.cssText = "display:flex;gap:4px;align-items:center;margin-left:8px;";
    tauWrap.innerHTML = '<span style="font-size:10.5px;color:var(--muted);">τ:</span>';
    ["2", "4", "8"].forEach((t) => {
      const b = document.createElement("button");
      b.className = "methodChip" + (t === tau ? " active" : "");
      b.textContent = t;
      b.addEventListener("click", () => {
        tau = t;
        tauWrap.querySelectorAll(".methodChip").forEach((x) => x.classList.remove("active"));
        b.classList.add("active");
        document.getElementById("t2BarsTitle").textContent = `Sorted target authority (τ=${tau})`;
        drawStage(); drawBars();
      });
      tauWrap.appendChild(b);
    });
    toggles.appendChild(tauWrap);
    drawStage();
    drawBars();
    drawBreakdown();
  }

  window.Tabs = window.Tabs || {};
  window.Tabs.tab2 = {
    legend: [
      { shape: "dot", color: "#d7d7d3", label: "ordinary bird" },
      { shape: "dot", color: "var(--core)", label: "interior" },
      { shape: "dot", color: "#eee8fa", label: "eligible exterior candidate" },
      { shape: "dot", color: "var(--controlif)", label: "top-k by current metric" },
      { shape: "dot", color: "var(--target)", label: "target heading" },
    ],
    render,
    onActivate() { Viz.TL.bind("tab2", null); },
    provenanceHtml() {
      const p = D.provenance;
      return Viz.provRow("Episode source", p.episode_source) +
        Viz.provRow("Metric source", p.metric_source) +
        Viz.provRow("Lattice source", p.lattice_source) +
        Viz.provRow("Replay note", p.replay_note) +
        Viz.provRow("Seed selection", p.seed_selection_note) +
        Viz.provRow("Causal effect formula", p.formulas.causal_effect) +
        Viz.provRow("Target authority formula", p.formulas.target_authority) +
        Viz.provRow("On tau / timesteps", p.tau_note) +
        Viz.provRow("Scope note", p.scope_note) +
        Viz.provRow("Seed / target / step", `seed ${D.seed}, h* = ${arrows[D.h_star]}, t0=${D.t0}, step ${D.step}`);
    },
  };
})();
