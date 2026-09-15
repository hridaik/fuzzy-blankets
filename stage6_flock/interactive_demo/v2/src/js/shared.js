/* Shared utilities: bird glyph rendering, timeline controller, legend,
   provenance drawer, tab/rail wiring, tooltip. One role palette used by
   every tab (see css/main.css tokens + ROLE_COLOR below). */
(function () {
  "use strict";
  const SVGNS = "http://www.w3.org/2000/svg";

  // h=0 up, h=1 down, h=2 left, h=3 right -- identical convention to the v1 demo's UV table.
  const UV = [[0, 1], [0, -1], [-1, 0], [1, 0]];

  const ROLE_COLOR = {
    ordinary: { fill: "#d7d7d3", stroke: "#aaaaa4" },
    interior: { fill: "var(--core)", stroke: "var(--core-stroke)" },
    predictive: { fill: "none", stroke: "var(--predictive)" },
    fiedler: { fill: "none", stroke: "var(--fiedler)" },
    dynamical: { fill: "none", stroke: "var(--shell-stroke)" },
    controlif: { fill: "none", stroke: "var(--controlif)" },
    actuator: { fill: "var(--actuator)", stroke: "var(--actuator-stroke)" },
    target: { fill: "var(--target)", stroke: "var(--target)" },
    oracle: { fill: "none", stroke: "var(--oracle)" },
  };

  function el(tag, attrs) {
    const e = document.createElementNS(SVGNS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }

  /* Triangle bird glyph, apex pointing along heading h (0..3, UV table above).
     r = half-size. Returns the <g> so callers can attach handlers/dataset. */
  function drawBird(svg, x, y, h, r, opts) {
    opts = opts || {};
    const [dx, dy] = UV[h];
    const px = -dy, py = dx; // perpendicular, screen space (y already flipped below)
    // Scaled a bit under the full cell radius so two triangles facing each
    // other across one lattice spacing show a visible gap, not a touch.
    const apex = [x + dx * r * 1.12, y - dy * r * 1.12];
    const back1 = [x - dx * r * 0.60 + px * r * 0.72, y + dy * r * 0.60 - py * r * 0.72];
    const back2 = [x - dx * r * 0.60 - px * r * 0.72, y + dy * r * 0.60 + py * r * 0.72];
    const g = el("g", { class: "bird" });
    if (opts.halo) {
      const halo = el("circle", { cx: x, cy: y, r: r * 1.9, fill: "none",
        stroke: opts.halo, "stroke-width": 1.6, "stroke-opacity": 0.55 });
      g.appendChild(halo);
    }
    if (opts.ring) {
      const ring = el("circle", { cx: x, cy: y, r: r * 1.55, fill: "none",
        stroke: opts.ring, "stroke-width": 2.1 });
      g.appendChild(ring);
    }
    const triAttrs = {
      points: `${apex[0]},${apex[1]} ${back1[0]},${back1[1]} ${back2[0]},${back2[1]}`,
      fill: opts.fill || "#d7d7d3", stroke: opts.stroke || "#aaaaa4",
      "stroke-width": opts.strokeWidth || 1, "stroke-linejoin": "round",
    };
    if (opts.dashed) triAttrs["stroke-dasharray"] = "1.6,1.4";
    const tri = el("polygon", triAttrs);
    g.appendChild(tri);
    if (opts.id !== undefined) g.dataset.id = opts.id;
    if (opts.onClick) { g.style.cursor = "pointer"; g.addEventListener("click", (ev) => opts.onClick(opts.id, ev)); }
    if (opts.onHover) { g.style.cursor = "pointer"; g.addEventListener("mousemove", (ev) => opts.onHover(opts.id, ev)); }
    if (opts.onLeave) g.addEventListener("mouseleave", opts.onLeave);
    svg.appendChild(g);
    return g;
  }

  function clearSvg(svg) { while (svg.firstChild) svg.removeChild(svg.firstChild); }

  /* Dashed lines from bird `id` to each of its structural neighbors --
     the "click an interior bird to see what it interacts with" behavior,
     shared across every tab with a static lattice + neighbors map. */
  function drawNeighborLines(svg, positions, L, size, id, neighbors) {
    const nbrs = (neighbors && neighbors[String(id)]) || [];
    const [sx, sy] = latticeXY(positions, L, id, size);
    nbrs.forEach((n) => {
      const [nx, ny] = latticeXY(positions, L, n, size);
      svg.appendChild(el("line", { x1: sx, y1: sy, x2: nx, y2: ny, stroke: "#94a3b8", "stroke-width": 1.3, "stroke-dasharray": "3,2" }));
    });
  }

  /* Recruited-this-step / departed-this-step sets from two consecutive
     interior membership lists -- pure set difference on already-provided
     per-frame data, no new inference. */
  function membershipDiff(prevList, curList) {
    const prev = new Set(prevList || []), cur = new Set(curList || []);
    const entered = [...cur].filter((id) => !prev.has(id));
    const left = [...prev].filter((id) => !cur.has(id));
    return { entered, left };
  }

  function fmtNum(v) {
    if (v === 0) return "0";
    const a = Math.abs(v);
    if (a < 0.001) return v.toExponential(1);
    if (a < 1) return v.toFixed(4);
    return v.toFixed(3);
  }

  /* Identical convention to the v1 demo's birdXY(): positions[id] = [row,col]
     on an LxL fixed lattice, padded 9% on each side, mapped into a size x size
     square viewBox. */
  function latticeXY(positions, L, id, size) {
    const [row, col] = positions[id];
    const pad = size * 0.09, inner = size - 2 * pad;
    return [pad + (col + 0.5) / L * inner, pad + (row + 0.5) / L * inner];
  }

  /* Draws only up to tIdx (inclusive) -- the trace grows into view as
     playback advances rather than showing the whole future at t=0. */
  function drawSpark(svg, series, tIdx, color, opts) {
    opts = opts || {};
    clearSvg(svg);
    const w = 260, h = 26;
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    const n = series.length;
    if (n < 2) return;
    const lo = opts.min !== undefined ? opts.min : Math.min(...series);
    const hi = opts.max !== undefined ? opts.max : Math.max(...series, lo + 1e-9);
    const y = (v) => h - ((v - lo) / (hi - lo || 1)) * h;
    const tt = Math.max(0, Math.min(tIdx, n - 1));
    if (opts.overlay) {
      const ov = opts.overlay.series;
      const ovTt = Math.max(0, Math.min(tt, ov.length - 1));
      const ovVisible = ov.slice(0, ovTt + 1);
      if (ovVisible.length >= 2) {
        const pts = ovVisible.map((v, i) => `${(i / (n - 1)) * w},${y(v)}`).join(" ");
        svg.appendChild(el("polyline", { points: pts, fill: "none", stroke: opts.overlay.color, "stroke-width": 1.3, "stroke-dasharray": "2.5,2" }));
      }
    }
    const visible = series.slice(0, tt + 1);
    if (visible.length >= 2) {
      const pts = visible.map((v, i) => `${(i / (n - 1)) * w},${y(v)}`).join(" ");
      svg.appendChild(el("polyline", { points: pts, fill: "none", stroke: color, "stroke-width": 1.6 }));
    }
    svg.appendChild(el("circle", { cx: (tt / (n - 1)) * w, cy: y(series[tt]), r: 2.6, fill: color }));
  }

  // -------------------------------------------------------------- tooltip
  let tipEl = null;
  function showTip(ev, html) {
    if (!tipEl) { tipEl = document.createElement("div"); tipEl.className = "tooltipBox"; document.body.appendChild(tipEl); }
    tipEl.innerHTML = html;
    tipEl.style.left = (ev.clientX + 14) + "px";
    tipEl.style.top = (ev.clientY + 14) + "px";
    tipEl.style.display = "block";
  }
  function hideTip() { if (tipEl) tipEl.style.display = "none"; }

  // ------------------------------------------------------------ timeline
  // One shared footer#timeline bound to whichever tab is active. Each tab
  // registers a config on activation; time position persists per tab id.
  const tabTimes = {};
  const TL = {
    cfg: null,
    tabId: null,
    playing: false,
    timer: null,
    speed: 1,
    bind(tabId, cfg) {
      this.pause();
      this.tabId = tabId;
      this.cfg = cfg; // {tMin, tMax, phases:[{key,label,t}], onTick(t)}
      const footer = document.getElementById("timeline");
      // The single footer DOM node is physically relocated into the active
      // tab's own slot (right under its stage), so playback controls always
      // sit with the visualization they control instead of pinned to the
      // page bottom. Tabs with no timeline (2, 4) park it in a hidden
      // graveyard node instead of destroying/rebuilding it.
      const slot = document.getElementById(tabId + "TimelineSlot");
      if (!cfg || !slot) {
        document.getElementById("timelineGraveyard").appendChild(footer);
        footer.hidden = true;
        return;
      }
      slot.appendChild(footer);
      footer.hidden = false;
      const slider = document.getElementById("timeSlider");
      slider.min = cfg.tMin; slider.max = cfg.tMax; slider.step = 1;
      const t0 = tabTimes[tabId] !== undefined ? tabTimes[tabId] : cfg.tMin;
      this.renderPhaseMarks();
      this.setT(Math.max(cfg.tMin, Math.min(cfg.tMax, t0)));
    },
    renderPhaseMarks() {
      const wrap = document.getElementById("phaseMarks");
      wrap.innerHTML = "";
      if (!this.cfg || !this.cfg.phases) return;
      const { tMin, tMax } = this.cfg;
      const span = Math.max(1, tMax - tMin);
      this.cfg.phases.forEach((p) => {
        const m = document.createElement("div");
        m.className = "phaseMark";
        m.style.left = (((p.t - tMin) / span) * 100) + "%";
        m.title = p.label;
        wrap.appendChild(m);
      });
    },
    setT(t) {
      if (!this.cfg) return;
      t = Math.max(this.cfg.tMin, Math.min(this.cfg.tMax, t));
      tabTimes[this.tabId] = t;
      document.getElementById("timeSlider").value = t;
      document.getElementById("tDisplay").textContent = "t = " + t;
      const badge = document.getElementById("phaseBadge");
      const phase = this.currentPhase(t);
      if (phase) { badge.textContent = phase.label; badge.className = ""; badge.classList.add(phase.key); badge.style.display = ""; }
      else badge.style.display = "none";
      this.cfg.onTick(t);
    },
    currentPhase(t) {
      if (!this.cfg.phases) return null;
      let cur = null;
      for (const p of this.cfg.phases) { if (p.t <= t) cur = p; }
      return cur || this.cfg.phases[0];
    },
    get t() { return tabTimes[this.tabId] || 0; },
    play() {
      if (!this.cfg || this.playing) return;
      this.playing = true;
      document.getElementById("playBtn").textContent = "❚❚";
      const step = () => {
        if (!this.playing) return;
        let t = this.t + 1;
        if (t > this.cfg.tMax) t = this.cfg.tMin;
        this.setT(t);
        this.timer = setTimeout(step, 220 / this.speed);
      };
      this.timer = setTimeout(step, 220 / this.speed);
    },
    pause() {
      this.playing = false;
      if (this.timer) clearTimeout(this.timer);
      const btn = document.getElementById("playBtn");
      if (btn) btn.textContent = "▶";
    },
    toggle() { this.playing ? this.pause() : this.play(); },
    reset() { this.pause(); if (this.cfg) this.setT(this.cfg.tMin); },
    stepBack() { this.pause(); this.setT(this.t - 1); },
    stepFwd() { this.pause(); this.setT(this.t + 1); },
    setSpeed(s) { this.speed = s; if (this.playing) { this.pause(); this.play(); } },
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("restartBtn").addEventListener("click", () => TL.reset());
    document.getElementById("stepBackBtn").addEventListener("click", () => TL.stepBack());
    document.getElementById("stepFwdBtn").addEventListener("click", () => TL.stepFwd());
    document.getElementById("playBtn").addEventListener("click", () => TL.toggle());
    document.getElementById("timeSlider").addEventListener("input", (ev) => { TL.pause(); TL.setT(+ev.target.value); });
    document.getElementById("speedSel").addEventListener("change", (ev) => TL.setSpeed(+ev.target.value));
    const stage = document.getElementById("main");
    stage.addEventListener("keydown", (ev) => {
      if (ev.key === "ArrowLeft") { TL.stepBack(); ev.preventDefault(); }
      if (ev.key === "ArrowRight") { TL.stepFwd(); ev.preventDefault(); }
    });
  });

  // ------------------------------------------------------- provenance drawer
  const Prov = {
    open(html) {
      document.getElementById("provBody").innerHTML = html;
      document.getElementById("provDrawer").classList.add("open");
      document.getElementById("provOverlay").classList.add("open");
    },
    close() {
      document.getElementById("provDrawer").classList.remove("open");
      document.getElementById("provOverlay").classList.remove("open");
    },
  };
  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("provOverlay").addEventListener("click", Prov.close);
    document.getElementById("provCloseBtn").addEventListener("click", Prov.close);
  });

  function provRow(k, v) {
    if (v === undefined || v === null || v === "") return "";
    return `<div class="provRow"><div class="k">${k}</div><div>${v}</div></div>`;
  }

  window.Viz = { UV, ROLE_COLOR, el, drawBird, clearSvg, drawSpark, latticeXY, drawNeighborLines, membershipDiff, fmtNum, showTip, hideTip, TL, Prov, provRow };
})();
