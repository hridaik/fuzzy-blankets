/* Tab 6 -- Translation. "Can the same online idea operate when the
   collective itself moves through space?" v3: ForwardMaterialTrace611
   (frozen, Jaccard>=0.30) is the PRIMARY and ONLY identity/membership
   layer driving this view -- re-run on the confirmatory seed manifests
   (stage6_12C_kinematic_contact_confirmation/, final_translating_flock_closure/)
   under the frozen K=1/d=8/release=24 protocol. v1 (LineageTracker611,
   the original Stage 6.11 tracker whose "3/5 successful blind adaptive
   controls" claim was withdrawn) is not shown here -- see
   interactive_demo/v3/src/data_prep/EXEMPLAR_SELECTION.md for why it was
   dropped rather than kept as a secondary toggle. Torus, minimum-image
   wrapping. */
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

  /* Scanning-phase candidate styling (v3): candidate_preview/candidate_frontrunner
     are PROVISIONAL detect_propose() output, replayed via the exact same
     window-building + ForwardMaterialTrace611 loop world_sampling_612c.py's
     (and world_sampling_closure.py's) try_world uses during real
     qualification -- see prep_tab6_translation_v3.py's scanning_frames
     docstring.

     Only the FRONT-RUNNER (the cluster ForwardMaterialTrace611 is currently
     dwelling on) is painted onto individual birds, in a different hue
     (--candidate-frontrunner, teal) from confirmed material_members
     (--core, blue) so "provisional" is never confused with "confirmed".
     The rest of candidate_preview -- every OTHER cluster detect_propose
     (Louvain community detection over the whole arena) proposes that step
     -- is deliberately NOT painted per-bird: measured at build time, that
     set typically covers ~90%+ of all 400 birds each step (it is close to
     a full partition of the entire flock into its ordinary social
     structure, not a short list of plausible target candidates), so
     highlighting it individually would tint almost the whole world and
     defeat the "where to look" purpose this fix exists for. That count is
     still surfaced honestly -- in the live-metrics panel and in each
     bird's hover tooltip -- just not painted onto nearly every bird. See
     EXEMPLAR_SELECTION.md, "Third-pass addition" section. */
  function candidateStyle(id, f) {
    if (f.phase !== "scanning") return null;
    if (f.candidate_frontrunner && f.candidate_frontrunner.includes(id)) {
      return { fill: "var(--candidate-frontrunner)", stroke: "var(--candidate-frontrunner-stroke)", strokeWidth: 1.5, ring: "var(--candidate-frontrunner)" };
    }
    return null;
  }

  function drawWorld(svg, f, L) {
    Viz.clearSvg(svg);
    const size = 360, pad = 10;
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    const scale = (size - 2 * pad) / L;
    const memberSet = new Set(f.material_members), actSet = new Set(f.actuators);
    for (let id = 0; id < D.seeds[String(seed)].N; id++) {
      const [rx, ry] = f.r[id];
      const x = pad + (rx / L) * (size - 2 * pad), y = size - pad - (ry / L) * (size - 2 * pad);
      let fill = "#d7d7d3", stroke = "#aaaaa4", sw = 0.9, ring = null, halo = null, dashed = false;
      const cs = candidateStyle(id, f);
      if (cs) { fill = cs.fill; stroke = cs.stroke; sw = cs.strokeWidth; ring = cs.ring || ring; dashed = !!cs.dashed; }
      if (memberSet.has(id)) { fill = "var(--core)"; stroke = "var(--core-stroke)"; sw = 1.5; }
      if (actSet.has(id)) { fill = "var(--actuator)"; stroke = "var(--actuator-stroke)"; sw = 1.9; }
      if (f.entered.includes(id)) halo = "var(--recruited)";
      if (f.left.includes(id)) ring = "var(--departed)";
      if (inspectId === id) ring = "#111";
      Viz.drawBird(svg, x, y, f.z[id], Math.max(2.6, scale * 0.32), { fill, stroke, strokeWidth: sw, ring, halo, dashed, id,
        onClick: (bid) => { inspectId = inspectId === bid ? null : bid; drawStage(Viz.TL.t); },
        onHover: (bid, ev) => Viz.showTip(ev, birdTip(bid, f)), onLeave: Viz.hideTip });
    }
  }

  function drawComoving(svg, f, L) {
    Viz.clearSvg(svg);
    const size = 360, pad = 10;
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    const scale = (size - 2 * pad) / L;
    const memberSet = new Set(f.material_members), actSet = new Set(f.actuators);
    const cx = size / 2, cy = size / 2;
    svg.appendChild(Viz.el("circle", { cx, cy, r: 2, fill: "#0003" }));
    const project = (id) => {
      if (!f.centre) return [cx, cy];
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
      let fill = "#d7d7d3", stroke = "#aaaaa4", sw = 0.9, ring = null, halo = null, dashed = false;
      const cs = candidateStyle(id, f);
      if (cs) { fill = cs.fill; stroke = cs.stroke; sw = cs.strokeWidth; ring = cs.ring || ring; dashed = !!cs.dashed; }
      if (memberSet.has(id)) { fill = "var(--core)"; stroke = "var(--core-stroke)"; sw = 1.5; }
      if (actSet.has(id)) { fill = "var(--actuator)"; stroke = "var(--actuator-stroke)"; sw = 1.9; }
      if (f.entered.includes(id)) halo = "var(--recruited)";
      if (f.left.includes(id)) ring = "var(--departed)";
      if (inspectId === id) ring = "#111";
      Viz.drawBird(svg, x, y, f.z[id], Math.max(2.6, scale * 0.32), { fill, stroke, strokeWidth: sw, ring, halo, dashed, id,
        onClick: (bid) => { inspectId = inspectId === bid ? null : bid; drawStage(Viz.TL.t); },
        onHover: (bid, ev) => Viz.showTip(ev, birdTip(bid, f)), onLeave: Viz.hideTip });
    }
  }

  function birdTip(id, f) {
    const roles = [];
    if (f.material_members.includes(id)) roles.push("material-traced member (ForwardMaterialTrace611)");
    if (f.actuators.includes(id)) roles.push("actuated now");
    if (f.entered.includes(id)) roles.push("entered this step");
    if (f.left.includes(id)) roles.push("left this step");
    if (f.phase === "scanning" && f.candidate_frontrunner && f.candidate_frontrunner.includes(id)) roles.push("candidate front-runner (ForwardMaterialTrace611 currently dwelling on this cluster, pre-qualification)");
    else if (f.phase === "scanning" && f.candidate_preview && f.candidate_preview.some((c) => c.includes(id))) roles.push("proposed candidate (detect_propose, not yet the front-runner)");
    return `<b>Bird ${id}</b><br>Heading ${arrows[f.z[id]]}<br>${roles.length ? roles.join(", ") : "exterior"}<br><i>click to inspect neighbors (co-moving frame)</i>`;
  }

  function drawStage(t) {
    const f = frameAt(t);
    const prevF = t > 0 ? frameAt(t - 1) : { material_members: [] };
    const { entered, left } = Viz.membershipDiff(prevF.material_members, f.material_members);
    f.entered = entered; f.left = left;
    const L = data().L;
    drawWorld(document.getElementById("t6World"), f, L);
    drawComoving(document.getElementById("t6Comoving"), f, L);
    const scanNote = f.phase === "scanning"
      ? `<div class="metric" style="color:var(--muted);">pre-qualification — no target locked, no material trace yet</div>
         <div class="metric"><span>candidate clusters proposed (detect_propose)</span><b>${(f.candidate_preview || []).length}</b></div>
         <div class="metric"><span>front-runner cluster size</span><b>${(f.candidate_frontrunner || []).length || "—"}</b></div>` : "";
    document.getElementById("t6Metrics").innerHTML = `
      <div class="metric"><span>traced material members</span><b>${f.material_members.length}</b></div>
      <div class="metric"><span>phase</span><b>${f.phase}</b></div>
      <div class="metric"><span>actuators</span><b>${f.actuators.length}</b></div>
      ${scanNote}
    `;
    drawRetention(f);
    drawForwardTrace(f);
  }

  /* ForwardMaterialTrace611 -- PRIMARY identity readout (v3). Frozen,
     material-overlap-only tracker (Jaccard>=0.30), calibrated independently
     of any control outcome, zero erroneous cross-population transfers
     across 72 full-episode holdout traces. split_flag/merge_flag are
     ADVISORY heuristics -- never validated against an independently
     confirmed physical split/merge ground truth, and never called
     "confirmed" here (stage6_12B_contact_persistence/
     IDENTITY_SEMANTICS_CORRECTION.md). */
  function drawForwardTrace(f) {
    const el = document.getElementById("t6ForwardTrace");
    const ft = f.forward_material_trace;
    if (!ft) {
      el.innerHTML = f.phase === "scanning"
        ? `<p class="footnote">Pre-qualification scanning phase: no target is LOCKED and no material_members are set yet — this matches the real qualification process, which also has no committed membership before t0. What you ARE seeing: ${(f.candidate_preview || []).length} candidate cluster(s) this step, proposed by the exact same <code>detect_propose</code> call the qualification process itself uses (not a reimplementation). The teal-highlighted <b>front-runner</b> cluster (${(f.candidate_frontrunner || []).length || 0} birds) is whichever candidate a fresh ForwardMaterialTrace611 instance is currently dwelling on toward eventual qualification — it can still lose out to a different candidate before t0 commits.</p>`
        : `<p class="footnote">No forward-material-trace data for this frame.</p>`;
      return;
    }
    const statusColor = { continuing: "#15803d", unresolved: "#b45309", dead: "#b91c1c" }[ft.status] || "#555";
    const flags = [];
    if (ft.split_flag) flags.push(`<span style="color:#b45309;font-weight:600;">SPLIT (advisory)</span>`);
    if (ft.merge_flag) flags.push(`<span style="color:#7c3aed;font-weight:600;">MERGE (advisory)</span>`);
    const unresolvedNote = ft.status === "unresolved"
      ? `<div class="metric" style="color:#b45309;">IDENTITY UNRESOLVED (${ft.steps_unresolved} consecutive step(s) with no qualifying candidate) — membership held, not switched</div>`
      : (ft.status === "dead" ? `<div class="metric" style="color:#b91c1c;">IDENTITY DEAD — missed-detection horizon exceeded, no re-acquisition</div>` : "");
    el.innerHTML = `
      <div class="metric"><span>status</span><b style="color:${statusColor};">${ft.status}${flags.length ? " · " + flags.join(" ") : ""}</b></div>
      <div class="metric"><span>traced target size</span><b>${ft.n_members}</b></div>
      <div class="metric"><span>candidates / accepting</span><b>${ft.n_candidates} / ${ft.n_accepting_candidates}</b></div>
      <div class="metric"><span>frac at target heading (trace)</span><b>${ft.frac_trace_at_target !== null ? (ft.frac_trace_at_target * 100).toFixed(0) + "%" : "—"}</b></div>
      ${unresolvedNote}
      <p class="footnote" style="margin-top:4px;"><b>WHY THIS CANDIDATE WAS CHOSEN:</b> ${ft.reason}</p>
      ${(ft.split_flag || ft.merge_flag) ? `<p class="footnote" style="margin-top:4px;color:#b45309;"><b>Note:</b> this flag is an advisory Jaccard-overlap heuristic, not a confirmed physical split/merge — no physical-split ground truth has been independently validated in this repository. The display follows the tracker's own continuation rule (largest absolute retained share of the previous target), never a different population.</p>` : ""}
    `;
  }

  /* Material-retention diagnostic: R_old is the headline ("material
     retention from previous target"); R_new/Jaccard/retained/lost/gained
     are inspectable below it. Computed frame-to-frame directly from
     ForwardMaterialTrace611's own accepted-membership sequence. */
  function drawRetention(f) {
    const el = document.getElementById("t6Retention");
    const mr = f.material_retention;
    if (!mr) {
      el.innerHTML = `<p class="footnote">No previous frame (t=0).</p>`;
      return;
    }
    const pct = (x) => (x === null || x === undefined) ? "—" : (x * 100).toFixed(0) + "%";
    const zeroFlag = mr.overlap_zero
      ? `<div class="metric" style="color:#b91c1c;font-weight:600;">⚠ zero overlap with previous target — complete material replacement</div>`
      : "";
    el.innerHTML = `
      <div class="metric"><span>R_old (material retention from previous target)</span><b>${pct(mr.R_old)}</b></div>
      <div class="metric"><span>R_new (inherited fraction of current)</span><b>${pct(mr.R_new)}</b></div>
      <div class="metric"><span>Jaccard overlap</span><b>${pct(mr.jaccard)}</b></div>
      <div class="metric"><span>retained / lost / gained</span><b>${mr.n_retained} / ${mr.n_lost} / ${mr.n_gained}</b></div>
      ${zeroFlag}
    `;
  }

  /* Control-outcome summary -- honest framing per EXEMPLAR_SELECTION.md:
     actuator selection method, kinematic score if applicable, and the
     realized delta vs. a CRN-paired no-control baseline. Never implies a
     working controller; the caption for each exemplar states its own
     status (clean/positive, split-flagged/negative, mild/noise-level,
     kinematic-top-but-negative). */
  function drawControlSummary() {
    const el = document.getElementById("t6ControlSummary");
    const cs = data().control_summary;
    const djc = cs.delta_J_conservative, dja = cs.delta_J_assoc;
    const sign = (x) => x > 0 ? "#15803d" : (x < 0 ? "#b91c1c" : "#555");
    el.innerHTML = `
      <div class="metric"><span>actuator</span><b>${cs.actuator}${cs.actuator_class ? " (" + cs.actuator_class.replace(/_/g, " ") + ")" : ""}</b></div>
      <div class="metric"><span>selection</span><b>${cs.actuator_selection}</b></div>
      ${cs.kinematic_score !== null && cs.kinematic_score !== undefined ? `<div class="metric"><span>kinematic predicted-contact score</span><b>${cs.kinematic_score.toFixed(1)}</b></div>` : ""}
      <div class="metric"><span>ΔJ_conservative (vs. paired no-control)</span><b style="color:${sign(djc)};">${djc >= 0 ? "+" : ""}${djc.toFixed(4)}</b></div>
      <div class="metric"><span>ΔJ_assoc</span><b style="color:${sign(dja)};">${dja >= 0 ? "+" : ""}${dja.toFixed(4)}</b></div>
      <div class="metric"><span>event</span><b>${cs.event_corrected}</b></div>
      <p class="footnote" style="margin-top:6px;">${cs.caption}</p>
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
      const pts = trace.filter((p) => p.frac !== null && p.frac !== undefined).map((p) => `${X(p.t)},${Y(p.frac)}`).join(" ");
      svg.appendChild(Viz.el("polyline", { points: pts, fill: "none", stroke: "var(--seriesA)", "stroke-width": 1.6 }));
    }
    /* Material-discontinuity markers: a red tick for every frame whose
       material_retention.overlap_zero is true -- i.e. the traced target
       membership shares NO bird with the previous frame's traced target
       membership. Raw series only, no severity judgement. */
    d.frames.forEach((fr) => {
      if (fr.material_retention && fr.material_retention.overlap_zero) {
        svg.appendChild(Viz.el("line", { x1: X(fr.t), y1: padT, x2: X(fr.t), y2: h - padB, stroke: "#b91c1c", "stroke-width": 1.3, opacity: 0.7 }));
      }
    });
    svg.appendChild(Viz.el("text", { x: padL, y: 10, "font-size": 8.5, fill: "var(--muted)" })).textContent = "target-heading fraction (material trace)";
    svg.appendChild(Viz.el("text", { x: w - 8, y: h - 4, "font-size": 8, fill: "var(--muted)", "text-anchor": "end" })).textContent = "control (orange) / release (green) shaded";
  }

  function renderSeeds() {
    const wrap = document.getElementById("t6Seeds");
    wrap.innerHTML = "";
    D.seed_order.forEach((s) => {
      const b = document.createElement("button");
      b.className = "methodChip" + (s === seed ? " active" : "");
      b.textContent = `${s} — ${D.seeds[String(s)].outcome_label}`;
      b.addEventListener("click", () => {
        seed = s; inspectId = null; Viz.TL.pause();
        Viz.TL.bind("tab6", timelineCfg());
        renderSeeds(); drawFracTrace(); updateTargetBadge(); drawControlSummary();
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
    const phases = [];
    if (ev.scanning_start && d.n_scan > 0) phases.push({ key: "scanning", label: "Scanning (pre-qualification)", t: ev.scanning_start.t });
    if (ev.qualified_and_target_set) phases.push({ key: "control", label: "Control (actuating)", t: ev.qualified_and_target_set.t });
    if (ev.release_begin) phases.push({ key: "release", label: "Release", t: ev.release_begin.t });
    return { tMin: 0, tMax: d.frames.length - 1, phases, onTick: (t) => { drawStage(t); updateTargetBadge(); } };
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">6. Translation — can the same online idea operate when the collective moves through space?</h2>
      <p class="qCaption">ForwardMaterialTrace611 (frozen, Jaccard≥0.30) — PRIMARY identity readout, re-run under the frozen K=1/d=8/release=24 protocol on confirmatory seeds (stage6_12C_kinematic_contact_confirmation/, final_translating_flock_closure/). Torus, minimum-image wrapping. Scanning (pre-qualification, genuine replay of the qualification rng) → control (actuating) → release. Honest spread of outcomes chosen to each illustrate a different reason (strong success, visually-confirmed split, no actuator of the relevant class available, ordinary failure, predictor reversal) — not cherry-picked successes; see the Control outcome panel and Summary below. This tab shows the frozen K=1 SINGLE-actuator protocol only; see Tab 5 for adaptive/multi-actuator online control.</p>
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
              <div class="stageBox"><svg class="stageSvg" id="t6World"></svg></div>
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
            <span class="lbl">Target heading</span>
          </div>
          <div class="card"><h3>Live metrics</h3><div id="t6Metrics"></div></div>
          <div class="card"><h3>Control outcome (this exemplar)</h3><div id="t6ControlSummary"></div></div>
          <div class="card"><h3>Material retention (vs. previous frame)</h3><div id="t6Retention"></div>
          </div>
          <div class="card"><h3>ForwardMaterialTrace611 — primary identity readout</h3><div id="t6ForwardTrace"></div></div>
          <div class="card">
            <h3>Summary</h3>
            <p class="footnote">Observe a collective. Infer how it is separated from its surroundings with a frozen, validated material-association tracker. Across the whole programme, no static actuator-selection strategy (historical authority, kinematic predicted contact, organizational role, directed causal topology) was found to reliably outperform random/matched selection — control opportunity here looks predominantly stochastic/trajectory-conditioned. See stage6_flock/TRANSLATING_FLOCK_FINAL_SYNTHESIS.md.</p>
            <p class="footnote" style="margin-top:6px;"><b>Why only one actuator, active only briefly?</b> This is the FROZEN K=1, d=8-of-32-step confirmatory protocol that Stage 6.12C / the final closure actually validated — not a limitation of this demo. A K=2 (two-actuator) secondary arm was also run and found similarly unreliable (90% CI spans zero, K2_SECONDARY.md). Genuine multi-actuator, adaptive, online control strategies are covered in Tab 5, under a different (non-confirmatory) protocol.</p>
          </div>
        </div>
      </div>
    `;
    renderSeeds();
    drawFracTrace();
    updateTargetBadge();
    drawControlSummary();
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
      { shape: "dot", color: "var(--core)", label: "material-traced member (ForwardMaterialTrace611)" },
      { shape: "dot", color: "var(--actuator)", label: "actuated now" },
      { shape: "dot", color: "var(--candidate-frontrunner)", label: "scanning: candidate front-runner (provisional, not yet confirmed — the cluster ForwardMaterialTrace611 is currently dwelling on)" },
      { shape: "ring", color: "var(--recruited)", label: "entered this step" },
      { shape: "ring", color: "var(--departed)", label: "left this step" },
    ],
    render,
    onActivate() { Viz.TL.bind("tab6", timelineCfg()); },
    provenanceHtml() {
      const p = D.provenance;
      return Viz.provRow("Source", p.source) + Viz.provRow("Identity version", p.identity_version) +
        Viz.provRow("Geometry", p.geometry) + Viz.provRow("Protocol", p.protocol) +
        Viz.provRow("Exemplar selection", p.exemplar_selection) +
        Viz.provRow("Programme finding", p.programme_finding) +
        Viz.provRow("Split/merge semantics", p.split_merge_semantics) +
        Viz.provRow("Current exemplar", `${seed} — ${data().outcome_label}`);
    },
  };
})();
