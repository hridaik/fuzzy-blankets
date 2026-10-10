/* Tab 5 -- Adaptive. "What changes when the collective and its interface
   must be inferred online?" One Stage-6.10 20x20 closed-loop episode:
   observe -> detect I_t -> infer causal interface -> steer -> release. */
(function () {
  "use strict";
  const D = TAB5_DATA;
  const arrows = ["↑", "↓", "←", "→"];
  const emByT = {}; D.emergence.forEach((e) => { emByT[e.t] = e; });
  let showOracle = false;
  let inspectId = null;

  function stateAt(t) {
    if (t < 8) return { stage: "unstructured", I: [], BC: [], actuators: [] };
    if (t < 60) { const e = emByT[t]; return { stage: "emergence", I: e ? e.I : [], BC: [], actuators: [] }; }
    if (t < 84) { const c = D.control[t - 60]; return { stage: "control", I: c.I, BC: c.B_do, actuators: c.actuators, rec: c }; }
    const r = D.release[t - 84]; return { stage: "release", I: r.I, BC: [], actuators: [], rec: r };
  }

  function drawStage(t) {
    const svg = document.getElementById("t5Svg");
    Viz.clearSvg(svg);
    const size = 400;
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    document.getElementById("t5ScanBadge").style.display = t < 8 ? "block" : "none";
    const s = stateAt(t);
    const prevS = t > 0 ? stateAt(t - 1) : { I: [] };
    const { entered, left } = Viz.membershipDiff(prevS.I, s.I);
    const enteredSet = new Set(entered), leftSet = new Set(left);
    const heads = D.frames[Math.min(t, D.frames.length - 1)];
    const interiorSet = new Set(s.I);
    const bcSet = new Set(s.BC);
    const actSet = new Set(s.actuators);
    const candidateOnly = s.stage === "emergence"; // not yet a confirmed interior -- draw as a dashed candidate
    const r = Math.max(2.4, size / D.lattice.L * 0.30);
    if (inspectId !== null) Viz.drawNeighborLines(svg, D.lattice.positions, D.lattice.L, size, inspectId, D.lattice.neighbors);
    for (let id = 0; id < D.lattice.nn; id++) {
      const [x, y] = Viz.latticeXY(D.lattice.positions, D.lattice.L, id, size);
      const h = +heads[id];
      let fill = "#d7d7d3", stroke = "#aaaaa4", sw = 0.8, ring = null, halo = null;
      if (interiorSet.has(id)) {
        if (candidateOnly) { fill = "#dce9f8"; stroke = "var(--core-stroke)"; sw = 1.3; }
        else { fill = "var(--core)"; stroke = "var(--core-stroke)"; sw = 1.4; }
      }
      if (bcSet.has(id)) ring = "var(--controlif)";
      if (actSet.has(id)) { fill = "var(--actuator)"; stroke = "var(--actuator-stroke)"; sw = 1.8; }
      if (enteredSet.has(id)) halo = "var(--recruited)";
      if (leftSet.has(id)) ring = "var(--departed)";
      if (inspectId === id) ring = "#111";
      Viz.drawBird(svg, x, y, h, r, { fill, stroke, strokeWidth: sw, ring, halo, id,
        dashed: candidateOnly && interiorSet.has(id),
        onClick: (bid) => { inspectId = inspectId === bid ? null : bid; drawStage(t); },
        onHover: (bid, ev) => Viz.showTip(ev, birdTip(bid, h, interiorSet, bcSet, actSet, enteredSet, leftSet)),
        onLeave: Viz.hideTip });
    }
    updateSide(t, s);
    updateProcessStrip(s.stage, s.rec);
    document.getElementById("t5TargetBadge").style.display = t >= D.episode.t0 ? "" : "none";
  }

  function birdTip(id, h, interiorSet, bcSet, actSet, enteredSet, leftSet) {
    const roles = [];
    if (interiorSet.has(id)) roles.push("tracked interior");
    if (bcSet.has(id)) roles.push("causal interface candidate");
    if (actSet.has(id)) roles.push("actuated now");
    if (enteredSet.has(id)) roles.push("entered this step");
    if (leftSet.has(id)) roles.push("left this step");
    return `<b>Bird ${id}</b><br>Heading ${arrows[h]}<br>${roles.length ? roles.join(", ") : "exterior"}<br><i>click to inspect neighbors</i>`;
  }

  function updateSide(t, s) {
    document.getElementById("t5Metrics").innerHTML = `
      <div class="metric"><span>current |I|</span><b>${s.I.length}</b></div>
      <div class="metric"><span>current phase</span><b>${phaseLabel(t)}</b></div>
      <div class="metric"><span>B^C (control interface)</span><b>${s.BC.length}</b></div>
      <div class="metric"><span>actuators</span><b>${s.actuators.length}</b></div>
    `;
    const series = D.control.map((c) => c.H).concat(D.release.map((r) => r.H));
    const idx = t < 60 ? 0 : Math.min(t - 60, series.length - 1);
    const overlay = showOracle ? { series: D.no_control.H, color: "var(--oracle)" } : null;
    Viz.drawSpark(document.getElementById("t5Spark"), series, idx, "var(--seriesA)", { min: 0, max: 1, overlay });
  }

  function phaseLabel(t) {
    let cur = D.phases[0];
    for (const p of D.phases) if (p.t_start <= t) cur = p;
    return cur.label;
  }

  function updateProcessStrip(stage, rec) {
    const map = { unstructured: "OBSERVE", emergence: "INFER", control: "ACT", release: "OBSERVE" };
    let highlight = map[stage] || "OBSERVE";
    document.querySelectorAll(".processStep").forEach((el) => {
      el.classList.toggle("active", el.dataset.key === highlight);
    });
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">5. Adaptive — what changes when the collective and its interface must be inferred online?</h2>
      <p class="qCaption">The interior and the control interface are both re-inferred every step, not fixed once.</p>
      <div class="processStrip" id="t5Process">
        ${["OBSERVE", "DETECT", "INFER", "ACT"].map((k) => `<span class="processStep" data-key="${k}">${k}</span>`).join(" → ")}
      </div>
      <div class="panelBody">
        <div class="stageWrap">
          <div class="stageBox"><svg class="stageSvg" id="t5Svg"></svg><div class="scanBadge" id="t5ScanBadge">Scanning…</div></div>
          <div class="timelineSlot" id="tab5TimelineSlot"></div>
          <div class="scanCaption" id="t5ScanCaption">Dashed light-blue = a rolling candidate interior proposed by the blind detector, not yet confirmed.</div>
        </div>
        <div class="sideWrap">
          <div class="card targetBadge" id="t5TargetBadge" style="display:none;">
            <span class="arrow">${arrows[D.episode.h_star]}</span>
            <span class="lbl">Target heading (from t0=${D.episode.t0})</span>
          </div>
          <div class="card">
            <h3>Live metrics</h3>
            <div id="t5Metrics"></div>
            <svg id="t5Spark" class="spark" viewBox="0 0 260 26" style="width:100%;height:26px;margin-top:4px;"></svg>
            <label style="font-size:10.5px;color:var(--muted);display:flex;gap:5px;align-items:center;margin-top:4px;">
              <input type="checkbox" id="t5OracleToggle"> reference: no-control counterfactual
            </label>
            <p class="footnote">Target-heading fraction H(I_t), control window onward.</p>
          </div>
          <div class="card">
            <h3>Episode</h3>
            <div class="metric"><span>seed / turn</span><b>${D.episode.seed} / ${D.episode.turn.split(" ")[0]}°</b></div>
            <div class="metric"><span>final H (I0-tracked)</span><b>${D.episode.final_H.toFixed(2)}</b></div>
            <p class="footnote">${D.provenance.caveat}</p>
          </div>
        </div>
      </div>
    `;
    document.getElementById("t5OracleToggle").addEventListener("change", (ev) => { showOracle = ev.target.checked; drawStage(Viz.TL.t); });
  }

  window.Tabs = window.Tabs || {};
  window.Tabs.tab5 = {
    legend: [
      { shape: "dot", color: "#d7d7d3", label: "ordinary bird" },
      { shape: "dot", color: "var(--core)", label: "interior" },
      { shape: "ring", color: "var(--controlif)", label: "control interface B^C" },
      { shape: "dot", color: "var(--actuator)", label: "actuated now" },
      { shape: "ring", color: "var(--recruited)", label: "entered this step" },
      { shape: "ring", color: "var(--departed)", label: "left this step" },
      { shape: "dot", color: "var(--target)", label: "target heading" },
      { shape: "ring", color: "var(--oracle)", label: "reference/oracle (no-control)" },
    ],
    render,
    onActivate() {
      Viz.TL.bind("tab5", {
        tMin: 0, tMax: D.frames.length - 1,
        phases: D.phases.map((p) => ({ key: p.key, label: p.label, t: p.t_start })),
        onTick: drawStage,
      });
    },
    provenanceHtml() {
      const p = D.provenance;
      return Viz.provRow("Stage", p.stage) + Viz.provRow("Sources", (p.sources || []).join(", ")) +
        Viz.provRow("Selection rule", p.selection_rule) + Viz.provRow("Selection note", p.selection_note) +
        Viz.provRow("Caveat", p.caveat) + Viz.provRow("Replay note", p.replay_note) +
        Viz.provRow("Detector note", p.detector_note) +
        Viz.provRow("Scope", D.task && D.task.scope_line);
    },
  };
})();
