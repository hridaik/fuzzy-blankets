/* Tab 6 -- Translation. "Can the same online idea operate when the
   collective itself moves through space?" Original Stage 6.11 v1
   identity/readout, all five seeds, world + co-moving torus frames. */
(function () {
  "use strict";
  const D = TAB6_DATA;
  const arrows = ["↑", "↓", "←", "→"];
  const NEIGHBOR_RADIUS = 2.4; // torus units; ~2 layers at this density (N=400, L=24)
  let seed = D.default_seed;
  let inspectId = null;

  function data() { return D.seeds[String(seed)]; }
  function frameAt(t) { const f = data().frames; return f[Math.min(t, f.length - 1)]; }

  function torusDelta(a, b, L) { return (((a - b + L / 2) % L) + L) % L - L / 2; }

  /* Continuous-space neighbors within NEIGHBOR_RADIUS, torus-aware --
     computed on demand for the click-to-inspect interaction; no new
     science, a geometric lookup on already-provided positions. */
  function continuousNeighbors(f, id, L) {
    const [ax, ay] = f.r[id];
    const out = [];
    for (let j = 0; j < f.r.length; j++) {
      if (j === id) continue;
      const dx = torusDelta(f.r[j][0], ax, L), dy = torusDelta(f.r[j][1], ay, L);
      if (Math.hypot(dx, dy) <= NEIGHBOR_RADIUS) out.push(j);
    }
    return out;
  }

  function drawWorld(svg, f, L) {
    Viz.clearSvg(svg);
    const size = 360, pad = 10;
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    const scale = (size - 2 * pad) / L;
    const interiorSet = new Set(f.interior), bcSet = new Set(f.B_C), actSet = new Set(f.actuators);
    const detected = f.phase !== "uncontrolled";
    for (let id = 0; id < D.seeds[String(seed)].N; id++) {
      const [rx, ry] = f.r[id];
      const x = pad + (rx / L) * (size - 2 * pad), y = size - pad - (ry / L) * (size - 2 * pad);
      let fill = "#d7d7d3", stroke = "#aaaaa4", sw = 0.9, ring = null, halo = null;
      if (detected && interiorSet.has(id)) { fill = "var(--core)"; stroke = "var(--core-stroke)"; sw = 1.5; }
      if (bcSet.has(id)) ring = "var(--controlif)";
      if (actSet.has(id)) { fill = "var(--actuator)"; stroke = "var(--actuator-stroke)"; sw = 1.9; }
      if (f.entered.includes(id)) halo = "var(--recruited)";
      if (f.left.includes(id)) ring = "var(--departed)";
      if (inspectId === id) ring = "#111";
      Viz.drawBird(svg, x, y, f.z[id], Math.max(2.6, scale * 0.32), { fill, stroke, strokeWidth: sw, ring, halo, id,
        onClick: (bid) => { inspectId = inspectId === bid ? null : bid; drawStage(Viz.TL.t); },
        onHover: (bid, ev) => Viz.showTip(ev, birdTip(bid, f)), onLeave: Viz.hideTip });
    }
  }

  function drawComoving(svg, f, L) {
    Viz.clearSvg(svg);
    const size = 360, pad = 10;
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    const scale = (size - 2 * pad) / L;
    const interiorSet = new Set(f.interior), bcSet = new Set(f.B_C), actSet = new Set(f.actuators);
    const detected = f.phase !== "uncontrolled";
    const cx = size / 2, cy = size / 2;
    svg.appendChild(Viz.el("circle", { cx, cy, r: 2, fill: "#0003" }));
    const project = (id) => {
      const dx = torusDelta(f.r[id][0], f.centre[0], L), dy = torusDelta(f.r[id][1], f.centre[1], L);
      return [cx + dx * scale, cy - dy * scale];
    };
    if (inspectId !== null) {
      const [sx, sy] = project(inspectId);
      continuousNeighbors(f, inspectId, L).forEach((n) => {
        const [nx, ny] = project(n);
        svg.appendChild(Viz.el("line", { x1: sx, y1: sy, x2: nx, y2: ny, stroke: "#94a3b8", "stroke-width": 1.2, "stroke-dasharray": "3,2" }));
      });
    }
    for (let id = 0; id < D.seeds[String(seed)].N; id++) {
      const [x, y] = project(id);
      if (x < -10 || x > size + 10 || y < -10 || y > size + 10) continue;
      let fill = "#d7d7d3", stroke = "#aaaaa4", sw = 0.9, ring = null, halo = null;
      if (detected && interiorSet.has(id)) { fill = "var(--core)"; stroke = "var(--core-stroke)"; sw = 1.5; }
      if (bcSet.has(id)) ring = "var(--controlif)";
      if (actSet.has(id)) { fill = "var(--actuator)"; stroke = "var(--actuator-stroke)"; sw = 1.9; }
      if (f.entered.includes(id)) halo = "var(--recruited)";
      if (f.left.includes(id)) ring = "var(--departed)";
      if (inspectId === id) ring = "#111";
      Viz.drawBird(svg, x, y, f.z[id], Math.max(2.6, scale * 0.32), { fill, stroke, strokeWidth: sw, ring, halo, id,
        onClick: (bid) => { inspectId = inspectId === bid ? null : bid; drawStage(Viz.TL.t); },
        onHover: (bid, ev) => Viz.showTip(ev, birdTip(bid, f)), onLeave: Viz.hideTip });
    }
  }

  function birdTip(id, f) {
    const roles = [];
    if (f.interior.includes(id)) roles.push("interior");
    if (f.B_C.includes(id)) roles.push("control interface B^C");
    if (f.actuators.includes(id)) roles.push("actuated now");
    if (f.entered.includes(id)) roles.push("entered this step");
    if (f.left.includes(id)) roles.push("left this step");
    return `<b>Bird ${id}</b><br>Heading ${arrows[f.z[id]]}<br>${roles.length ? roles.join(", ") : "exterior"}<br><i>click to inspect neighbors (co-moving frame)</i>`;
  }

  function drawStage(t) {
    const f = frameAt(t);
    const prevF = t > 0 ? frameAt(t - 1) : { interior: [] };
    const { entered, left } = Viz.membershipDiff(prevF.interior, f.interior);
    f.entered = entered; f.left = left;
    const L = data().L;
    document.getElementById("t6ScanBadge").style.display = f.phase === "uncontrolled" ? "block" : "none";
    drawWorld(document.getElementById("t6World"), f, L);
    drawComoving(document.getElementById("t6Comoving"), f, L);
    document.getElementById("t6Metrics").innerHTML = `
      <div class="metric"><span>current |I|</span><b>${f.interior.length}</b></div>
      <div class="metric"><span>phase</span><b>${f.phase}</b></div>
      <div class="metric"><span>B^C / actuators</span><b>${f.B_C.length} / ${f.actuators.length}</b></div>
    `;
  }

  function drawFracTrace() {
    const svg = document.getElementById("t6Frac");
    Viz.clearSvg(svg);
    const w = 480, h = 90, padL = 30, padB = 16, padT = 6;
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    const d = data();
    const finalT = d.final_t;
    const trace = d.frac_interior_at_target_trace;
    const ev = {};
    d.events.forEach((e) => { ev[e.event] = e; });
    const tStart = ev.qualified_and_target_set ? ev.qualified_and_target_set.t : null;
    const tRelease = ev.release_begin ? ev.release_begin.t : null;
    const tEnd = ev.episode_end ? ev.episode_end.t : finalT;
    const X = (t) => padL + (t / finalT) * (w - padL - 8);
    const Y = (v) => h - padB - v * (h - padT - padB);
    if (tStart !== null) {
      const ctrlEnd = tRelease !== null ? tRelease : tEnd;
      svg.appendChild(Viz.el("rect", { x: X(tStart), y: padT, width: Math.max(0, X(ctrlEnd) - X(tStart)), height: h - padT - padB, fill: "var(--warn)", opacity: 0.08 }));
    }
    if (tRelease !== null) {
      svg.appendChild(Viz.el("rect", { x: X(tRelease), y: padT, width: Math.max(0, X(tEnd) - X(tRelease)), height: h - padT - padB, fill: "var(--good)", opacity: 0.08 }));
    }
    svg.appendChild(Viz.el("line", { x1: padL, y1: h - padB, x2: w - 8, y2: h - padB, stroke: "#ccc" }));
    if (trace.length > 1) {
      const pts = trace.map((p) => `${X(p.t)},${Y(p.frac)}`).join(" ");
      svg.appendChild(Viz.el("polyline", { points: pts, fill: "none", stroke: "var(--seriesA)", "stroke-width": 1.6 }));
    }
    svg.appendChild(Viz.el("text", { x: padL, y: 10, "font-size": 8.5, fill: "var(--muted)" })).textContent = "target-heading fraction";
    svg.appendChild(Viz.el("text", { x: w - 8, y: h - 4, "font-size": 8, fill: "var(--muted)", "text-anchor": "end" })).textContent = "control (orange) / release (green) shaded";
  }

  function renderSeeds() {
    const wrap = document.getElementById("t6Seeds");
    wrap.innerHTML = "";
    D.seed_order.forEach((s) => {
      const b = document.createElement("button");
      b.className = "methodChip" + (s === seed ? " active" : "");
      b.textContent = `${s} — ${D.seeds[String(s)].v1_outcome}`;
      b.addEventListener("click", () => {
        seed = s; inspectId = null; Viz.TL.pause();
        Viz.TL.bind("tab6", timelineCfg());
        renderSeeds(); drawFracTrace(); updateTargetBadge();
      });
      wrap.appendChild(b);
    });
  }

  function updateTargetBadge() {
    const f = frameAt(Viz.TL.t || 0);
    const el = document.getElementById("t6TargetBadge");
    const h = f.target_heading;
    if (h === null || h === undefined) { el.querySelector(".arrow").textContent = "—"; }
    else { el.querySelector(".arrow").textContent = arrows[h]; }
  }

  function timelineCfg() {
    const d = data();
    const ev = {}; d.events.forEach((e) => { ev[e.event] = e; });
    const phases = [{ key: "scanning", label: "Scanning", t: 0 }];
    if (ev.qualified_and_target_set) phases.push({ key: "control", label: "Target set", t: ev.qualified_and_target_set.t });
    if (ev.release_begin) phases.push({ key: "release", label: "Release", t: ev.release_begin.t });
    return { tMin: 0, tMax: d.frames.length - 1, phases, onTick: (t) => { drawStage(t); updateTargetBadge(); } };
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">6. Translation — can the same online idea operate when the collective moves through space?</h2>
      <p class="qCaption">Original Stage 6.11 v1 identity/readout. Torus, minimum-image wrapping. Unstructured → emergence → detected → target → control → release.</p>
      <div class="methodSelect" id="t6Seeds"></div>
      <div class="panelBody">
        <div class="stageWrap">
          <div class="narrowToggle">
            <button class="methodChip active" id="t6ToggleWorld">World</button>
            <button class="methodChip" id="t6ToggleComoving">Co-moving</button>
          </div>
          <div class="worldPair">
            <div id="t6WorldPane">
              <div class="frameLabel">World frame</div>
              <div class="stageBox"><svg class="stageSvg" id="t6World"></svg><div class="scanBadge" id="t6ScanBadge">Scanning…</div></div>
            </div>
            <div id="t6ComovingPane">
              <div class="frameLabel">Co-moving frame</div>
              <div class="stageBox"><svg class="stageSvg" id="t6Comoving"></svg></div>
            </div>
          </div>
          <div class="timelineSlot" id="tab6TimelineSlot"></div>
          <div class="card">
            <h3>Target-heading fraction, full run</h3>
            <svg id="t6Frac" viewBox="0 0 480 90" style="width:100%;height:auto;"></svg>
          </div>
        </div>
        <div class="sideWrap">
          <div class="card targetBadge" id="t6TargetBadge">
            <span class="arrow">—</span>
            <span class="lbl">Target heading (once detected)</span>
          </div>
          <div class="card"><h3>Live metrics</h3><div id="t6Metrics"></div></div>
          <div class="card">
            <p class="footnote">${D.provenance.footnote}</p>
          </div>
          <div class="card">
            <h3>Summary</h3>
            <p class="footnote">Observe a collective. Infer how it is separated from its surroundings. Learn where intervention has authority. Update those estimates as the system changes.</p>
          </div>
        </div>
      </div>
    `;
    renderSeeds();
    drawFracTrace();
    updateTargetBadge();
    document.getElementById("t6ToggleWorld").addEventListener("click", (ev) => {
      document.getElementById("t6WorldPane").classList.remove("hiddenNarrow");
      document.getElementById("t6ComovingPane").classList.add("hiddenNarrow");
      ev.target.classList.add("active"); document.getElementById("t6ToggleComoving").classList.remove("active");
    });
    document.getElementById("t6ToggleComoving").addEventListener("click", (ev) => {
      document.getElementById("t6ComovingPane").classList.remove("hiddenNarrow");
      document.getElementById("t6WorldPane").classList.add("hiddenNarrow");
      ev.target.classList.add("active"); document.getElementById("t6ToggleWorld").classList.remove("active");
    });
    document.getElementById("t6ComovingPane").classList.add("hiddenNarrow");
  }

  window.Tabs = window.Tabs || {};
  window.Tabs.tab6 = {
    legend: [
      { shape: "dot", color: "#d7d7d3", label: "ordinary bird" },
      { shape: "dot", color: "var(--core)", label: "interior" },
      { shape: "ring", color: "var(--controlif)", label: "control interface B^C" },
      { shape: "dot", color: "var(--actuator)", label: "actuated now" },
      { shape: "ring", color: "var(--recruited)", label: "entered this step" },
      { shape: "ring", color: "var(--departed)", label: "left this step" },
      { shape: "dot", color: "var(--target)", label: "target heading" },
    ],
    render,
    onActivate() { Viz.TL.bind("tab6", timelineCfg()); },
    provenanceHtml() {
      const p = D.provenance;
      return Viz.provRow("Source", p.source) + Viz.provRow("Identity version", p.identity_version) +
        Viz.provRow("Geometry", p.geometry) +
        Viz.provRow("Audit caveat", p.audit_caveat) + Viz.provRow("Audit location (cited, not shown)", p.audit_location) +
        Viz.provRow("Current seed", `${seed} — v1 outcome: ${data().v1_outcome}`);
    },
  };
})();
