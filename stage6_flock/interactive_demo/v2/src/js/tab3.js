/* Tab 3 -- Control. "Does interface structure matter when steering a known
   collective?" Seed-16 flock, target = clockwise turn, 9 frozen V1-V3
   control policies sharing one interior + identification time. */
(function () {
  "use strict";
  const D = TAB3_DATA;
  let methodId = D.default_method;
  let showMore = false;
  let inspectId = null;
  const arrows = ["↑", "↓", "←", "→"];

  function m() { return D.methods[methodId]; }

  function drawStage(t) {
    const svg = document.getElementById("t3Svg");
    Viz.clearSvg(svg);
    const size = 400;
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    const tl = D.timeline;
    const identified = t >= tl.identify;
    const inControl = t >= tl.control_start && t < tl.control_end;
    const released = t >= tl.release_end;
    document.getElementById("t3ScanBadge").style.display = identified ? "none" : "block";
    const method = m();
    const z = method.headings[Math.min(t, method.headings.length - 1)];
    const r = Math.max(4, size / D.lattice.L * 0.30);
    const interiorSet = new Set(D.roles.interior);
    const dynSet = new Set(D.roles.dynamical_shell);
    const actSet = new Set(method.actuators);

    if (inspectId !== null) Viz.drawNeighborLines(svg, D.lattice.positions, D.lattice.L, size, inspectId, D.neighbors);

    for (let id = 0; id < D.lattice.nn; id++) {
      const [x, y] = Viz.latticeXY(D.lattice.positions, D.lattice.L, id, size);
      let fill = "#d7d7d3", stroke = "#aaaaa4", sw = 1, halo = null, ring = null;
      const inInterior = identified && interiorSet.has(id);
      if (inInterior) { fill = "var(--core)"; stroke = "var(--core-stroke)"; sw = 2; }
      if (identified && dynSet.has(id)) halo = "var(--shell-stroke)";
      const actuatedNow = inControl && !released && actSet.has(id);
      if (actuatedNow) { fill = "var(--actuator)"; stroke = "var(--actuator-stroke)"; sw = 2.2; }
      if (inspectId === id) ring = "#111";
      Viz.drawBird(svg, x, y, z[id], r, { fill, stroke, strokeWidth: sw, halo, ring, id,
        onClick: (bid) => { inspectId = inspectId === bid ? null : bid; drawStage(t); },
        onHover: (bid, ev) => Viz.showTip(ev, birdTip(bid, actuatedNow, z[id])), onLeave: Viz.hideTip });
    }
    if (released) {
      svg.appendChild(Viz.el("text", { x: 10, y: size - 10, "font-size": 9.5, fill: "var(--good)", "font-weight": 700 })).textContent = "released";
    }
    updateMetrics(t);
    document.getElementById("t3ScanCaption").style.display = identified ? "none" : "";
    document.getElementById("t3TargetBadge").style.display = t >= tl.control_start ? "" : "none";
  }

  function birdTip(id, actuated, h) {
    const roles = [];
    if (D.roles.interior.includes(id)) roles.push("interior");
    if (D.roles.dynamical_shell.includes(id)) roles.push("dynamical shell");
    if (actuated) roles.push("actuated now");
    return `<b>Bird ${id}</b><br>Heading ${arrows[h]}<br>${roles.length ? roles.join(", ") : "exterior"}<br><i>click to inspect neighbors</i>`;
  }

  function updateMetrics(t) {
    const met = m().metrics;
    const idx = Math.min(t, met.Hstar.length - 1);
    document.getElementById("t3Metrics").innerHTML = `
      <div class="metric"><span>H* target fraction</span><b>${met.Hstar[idx].toFixed(2)}</b></div>
      <div class="metric"><span>coherence</span><b>${met.coherence[idx].toFixed(2)}</b></div>
      <div class="metric"><span>actuator count</span><b>${met.n_actuators_t[idx]}</b></div>
      <div class="metric"><span>coverage / double coverage</span><b>${met.coverage[idx]} / ${met.double_coverage[idx]}</b></div>
    `;
    Viz.drawSpark(document.getElementById("t3Spark"), met.Hstar, idx, "var(--seriesA)", { min: 0, max: 1 });
  }

  function drawEnsemble() {
    const wrap = document.getElementById("t3Ensemble");
    wrap.innerHTML = "";
    D.method_order.forEach((mid) => {
      const md = D.methods[mid];
      if (!md.ensemble || !md.ensemble.available) return;
      const p = md.ensemble.success_probability;
      const row = document.createElement("div");
      row.style.cssText = "display:flex;align-items:center;gap:5px;font-size:10px;padding:1.5px 0;" + (mid === methodId ? "font-weight:700;" : "");
      row.innerHTML = `<div style="width:88px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${md.label}">${md.short}</div>
        <div style="width:100px;background:#eee;border-radius:3px;overflow:hidden;">
          <div style="width:${Math.max(1, p * 100)}px;height:8px;background:${mid === methodId ? 'var(--accent)' : '#9aa1ab'};"></div>
        </div>
        <div style="font-variant-numeric:tabular-nums;">${(p * 100).toFixed(0)}%</div>`;
      wrap.appendChild(row);
    });
  }

  function drawBirdSteps() {
    const wrap = document.getElementById("t3BirdSteps");
    wrap.innerHTML = "";
    const rows = D.method_order.map((mid) => ({ mid, md: D.methods[mid], bs: D.methods[mid].summary.bird_steps }));
    const maxBS = Math.max(...rows.map((r) => r.bs), 1);
    rows.forEach(({ mid, md, bs }) => {
      const row = document.createElement("div");
      row.style.cssText = "display:flex;align-items:center;gap:5px;font-size:10px;padding:1.5px 0;" + (mid === methodId ? "font-weight:700;" : "");
      row.innerHTML = `<div style="width:88px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${md.label}">${md.short}</div>
        <div style="width:100px;background:#eee;border-radius:3px;overflow:hidden;">
          <div style="width:${Math.max(1, bs / maxBS * 100)}px;height:8px;background:${mid === methodId ? 'var(--warn)' : '#c9b18c'};"></div>
        </div>
        <div style="font-variant-numeric:tabular-nums;">${bs}</div>`;
      wrap.appendChild(row);
    });
  }

  function renderMethodChips() {
    const wrap = document.getElementById("t3Methods");
    wrap.innerHTML = "";
    const render1 = (mid) => {
      const md = D.methods[mid];
      const b = document.createElement("button");
      b.className = "methodChip" + (mid === methodId ? " active" : "");
      b.textContent = md.short + (md.diagnostic ? " ⚠" : "");
      b.title = md.subtitle;
      b.addEventListener("click", () => { methodId = mid; inspectId = null; renderMethodChips(); drawStage(Viz.TL.t); drawEnsemble(); drawBirdSteps(); document.getElementById("t3Why").textContent = md.why || ""; });
      wrap.appendChild(b);
    };
    D.method_order.filter((id) => D.methods[id].tier === "primary").forEach(render1);
    const moreBtn = document.createElement("button");
    moreBtn.className = "moreToggle";
    moreBtn.textContent = showMore ? "− fewer comparisons" : "+ more comparisons";
    moreBtn.addEventListener("click", () => { showMore = !showMore; renderMethodChips(); });
    wrap.appendChild(moreBtn);
    if (showMore) D.method_order.filter((id) => D.methods[id].tier === "more").forEach(render1);
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">3. Control — does interface structure matter when steering a known collective?</h2>
      <p class="qCaption">Control is evaluated after release. Same interior, same target; only the actuator-selection policy differs.</p>
      <div class="panelBody">
        <div class="stageWrap">
          <div class="stageBox"><svg class="stageSvg" id="t3Svg"></svg><div class="scanBadge" id="t3ScanBadge">Scanning… observation window</div></div>
          <div class="timelineSlot" id="tab3TimelineSlot"></div>
          <div class="scanCaption" id="t3ScanCaption">Observing the fixed lattice before the interior is identified at t=${D.timeline.identify}.</div>
          <div class="methodSelect" id="t3Methods"></div>
          <p class="footnote" id="t3Why"></p>
        </div>
        <div class="sideWrap">
          <div class="card targetBadge" id="t3TargetBadge" style="display:none;">
            <span class="arrow">${arrows[D.target_heading]}</span>
            <span class="lbl">Target heading</span>
          </div>
          <div class="card">
            <h3>Live metrics</h3>
            <div id="t3Metrics"></div>
            <svg id="t3Spark" class="spark" viewBox="0 0 260 26" style="width:100%;height:26px;margin-top:4px;"></svg>
          </div>
          <div class="card">
            <h3>Ensemble (frozen replicate studies)</h3>
            <div id="t3Ensemble"></div>
            <p class="footnote">Each bar: success probability across a small replicate ensemble already computed for that method (not re-run here) -- this single trajectory is illustrative, not the full evidence.</p>
          </div>
          <div class="card">
            <h3>Bird-steps (actuators × control duration)</h3>
            <div id="t3BirdSteps"></div>
            <p class="footnote">Total actuation cost across the control window -- a cheap policy keeps this low while still meeting the target.</p>
          </div>
        </div>
      </div>
    `;
    renderMethodChips();
    document.getElementById("t3Why").textContent = m().why || "";
    drawEnsemble();
    drawBirdSteps();
  }

  window.Tabs = window.Tabs || {};
  window.Tabs.tab3 = {
    legend: [
      { shape: "dot", color: "#d7d7d3", label: "ordinary bird" },
      { shape: "dot", color: "var(--core)", label: "interior" },
      { shape: "ring", color: "var(--shell-stroke)", label: "dynamical shell" },
      { shape: "dot", color: "var(--actuator)", label: "actuated now" },
      { shape: "dot", color: "var(--target)", label: "target heading" },
    ],
    render,
    onActivate() {
      Viz.TL.bind("tab3", {
        tMin: 0, tMax: m().headings.length - 1,
        phases: [
          { key: "observe", label: "Observe", t: 0 },
          { key: "identified", label: "Identified", t: D.timeline.identify },
          { key: "control", label: "Control", t: D.timeline.control_start },
          { key: "release", label: "Release", t: D.timeline.release_end },
        ],
        onTick: drawStage,
      });
    },
    provenanceHtml() {
      const p = D.provenance;
      return Viz.provRow("Source", p.source) + Viz.provRow("Generator", p.generator) +
        Viz.provRow("Seed / target", `seed ${p.seed}, target ${p.target}`) +
        Viz.provRow("Note", p.note) +
        Viz.provRow("Current method", `${m().label} — ${m().subtitle}`) +
        Viz.provRow("Ensemble source", m().ensemble && m().ensemble.source) +
        Viz.provRow("Bird-steps", "actuators(t) summed over the control window -- summary.bird_steps, already computed by the frozen scenario export, not recomputed here.");
    },
  };
})();
