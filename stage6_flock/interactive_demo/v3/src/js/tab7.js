/* Tab 7 -- Readiness & winner's curse. "Does sustained forcing generically
   move the flock, and is the apparent per-actuator headroom reproducible?"
   Static analytic snapshot (Stage 6.12 pooled/state-clustered readiness +
   Stage 6.12C stable-selectivity audit) -- no timeline. */
(function () {
  "use strict";
  const D = TAB7_DATA;

  function bar(label, v, max, color, sub) {
    const w = Math.max(2, Math.abs(v) / max * 160);
    const neg = v < 0;
    return `<div style="display:flex;align-items:center;gap:6px;font-size:10.5px;margin:2px 0;">
      <div style="width:120px;color:var(--muted);text-align:right;" title="${sub||''}">${label}</div>
      <div style="width:160px;background:#f1f1ef;border-radius:2px;overflow:hidden;position:relative;">
        <div style="width:${w}px;height:9px;background:${neg ? 'var(--bad)' : color};margin-left:${neg?160-w:0}px;"></div>
      </div>
      <div style="width:60px;font-variant-numeric:tabular-nums;">${Viz.fmtNum(v)}</div>
    </div>`;
  }

  function renderReadiness() {
    const r = D.readiness;
    const el = document.getElementById("t7Readiness");
    const ci = r.overall_G_sus_ci90;
    el.innerHTML = `
      <div class="metric"><span>Pooled G_sus mean (${r.n_states} states, random/fixed forcing)</span><b>${Viz.fmtNum(r.overall_G_sus_mean)}</b></div>
      <div class="metric"><span>90% CI (state-clustered)</span><b>[${Viz.fmtNum(ci[0])}, ${Viz.fmtNum(ci[1])}]</b></div>
      <p class="footnote">CI spans zero: sustained random forcing does not generically move the flock. But the pooled
      number hides per-state heterogeneity -- see the per-cell readiness labels below, and compare to the oracle
      panel: a large per-actuator headroom re-appears once you stop pooling across states.</p>
      <div style="max-height:110px;overflow-y:auto;margin-top:4px;">
        ${Object.entries(r.readiness_label_counts).map(([k,v]) => `<div class="metric" style="font-size:10px;"><span>${k}</span><b>${v}</b></div>`).join("")}
      </div>`;
  }

  function renderOracles() {
    const wrap = document.getElementById("t7Oracles");
    const maxV = Math.max(...D.oracle_states.map(s => s.A_clairvoyant), 0.01);
    wrap.innerHTML = D.oracle_states.map(s => `
      <div style="border-bottom:1px solid var(--border);padding:4px 0;">
        <div style="font-size:10px;color:var(--muted);margin-bottom:2px;">${s.state_id}</div>
        ${bar("random median", s.random_median, maxV, "var(--exterior-stroke)")}
        ${bar("A: clairvoyant max", s.A_clairvoyant, maxV, "var(--bad)", "mathematical identity under permutation -- never evidence")}
        ${bar("B: state-stable mean", s.B_state_stable, maxV, "var(--fiedler)", "Stage 6.12C's reported '6.9x' number")}
        ${bar("C: cross-validated", s.C_cross_validated, maxV, "var(--good)", "train/test split -- the only oracle with any claim to reproducibility")}
        <div style="font-size:9.5px;color:var(--muted);margin-top:1px;">excess of B over its own permutation null: <b style="color:${s.excess_B<0?'var(--bad)':'var(--good)'}">${Viz.fmtNum(s.excess_B)}</b> (null 90% CI [${Viz.fmtNum(s.null_B_ci90[0])}, ${Viz.fmtNum(s.null_B_ci90[1])}])</div>
      </div>`).join("");
  }

  function renderVariance() {
    const wrap = document.getElementById("t7Variance");
    wrap.innerHTML = D.variance_states.map(s => {
      const a = Math.max(0, s.var_actuator_frac) * 100, st = s.var_stream_frac * 100, res = s.var_residual_frac * 100;
      return `<div style="display:flex;align-items:center;gap:4px;font-size:9.5px;margin:2px 0;">
        <div style="width:110px;color:var(--muted);">${s.state_id.replace('s612c_','')}</div>
        <div style="flex:1;height:11px;display:flex;border-radius:2px;overflow:hidden;">
          <div style="width:${a}%;background:var(--liveparent);" title="actuator ${a.toFixed(1)}%"></div>
          <div style="width:${st}%;background:var(--accent);" title="stream ${st.toFixed(1)}%"></div>
          <div style="width:${res}%;background:var(--exterior);" title="residual ${res.toFixed(1)}%"></div>
        </div>
      </div>`;
    }).join("") + `<div style="font-size:9.5px;color:var(--muted);margin-top:4px;">
      <span style="color:var(--liveparent);">■</span> actuator identity &nbsp;
      <span style="color:var(--accent);">■</span> physics stream (opportunity) &nbsp;
      <span style="color:var(--exterior-stroke);">■</span> residual/interaction</div>`;
  }

  function renderHeatmap() {
    const h = D.heatmap;
    const wrap = document.getElementById("t7Heatmap");
    const nStream = h.matrix[0].length;
    const allVals = h.matrix.flat();
    const lo = Math.min(...allVals), hi = Math.max(...allVals);
    const color = (v) => {
      const t = (v - lo) / (hi - lo || 1);
      const g = Math.round(230 - t * 150), b = Math.round(230 - t * 60);
      return `rgb(${230},${g},${b})`;
    };
    let html = `<div style="font-size:9.5px;color:var(--muted);margin-bottom:4px;">${h.state_id} -- rows = candidates (sorted by mean), columns = the 8 confirmatory physics streams. Different winners in different columns is the point.</div>`;
    html += `<table style="border-collapse:collapse;font-size:9px;">`;
    h.candidates.forEach((cand, i) => {
      html += `<tr><td style="padding:1px 4px;color:var(--muted);text-align:right;">#${cand}</td>`;
      h.matrix[i].forEach(v => { html += `<td style="width:20px;height:14px;background:${color(v)};border:1px solid #fff;" title="${Viz.fmtNum(v)}"></td>`; });
      html += `<td style="padding:1px 4px;font-variant-numeric:tabular-nums;color:var(--muted);">${Viz.fmtNum(h.per_candidate_mean[i])}</td></tr>`;
    });
    html += `</table>`;
    wrap.innerHTML = html;
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">7. Readiness &amp; winner's curse — is the apparent per-actuator headroom reproducible?</h2>
      <p class="qCaption">Stage 6.12's pooled null hides state heterogeneity; Stage 6.12C's stable-selectivity audit shows the
      apparent headroom collapses once a genuine train/test split is used, and is indistinguishable from a permutation null
      that destroys stable actuator identity.</p>
      <div class="panelBody">
        <div class="stageWrap">
          <div class="card"><h3>Three oracle definitions, per state (J_conservative)</h3><div id="t7Oracles"></div></div>
        </div>
        <div class="sideWrap">
          <div class="card"><h3>Stage 6.12 control-readiness</h3><div id="t7Readiness"></div></div>
          <div class="card"><h3>Variance decomposition (per state)</h3><div id="t7Variance"></div></div>
          <div class="card"><h3>Candidate x stream heatmap</h3><div id="t7Heatmap"></div></div>
        </div>
      </div>`;
    renderReadiness(); renderOracles(); renderVariance(); renderHeatmap();
  }

  window.Tabs = window.Tabs || {};
  window.Tabs.tab7 = {
    legend: [
      { shape: "dot", color: "var(--exterior-stroke)", label: "random baseline" },
      { shape: "dot", color: "var(--bad)", label: "A: clairvoyant max (never evidence)" },
      { shape: "dot", color: "var(--fiedler)", label: "B: state-stable mean (reported oracle)" },
      { shape: "dot", color: "var(--good)", label: "C: cross-validated (reproducible-if-real)" },
    ],
    render,
    onActivate() { Viz.TL.bind("tab7", null); },
    provenanceHtml() {
      return Viz.provRow("Readiness source", D.provenance.readiness_source) +
        Viz.provRow("Selectivity source", D.provenance.selectivity_source) +
        Viz.provRow("Heatmap source", D.provenance.heatmap_source) +
        Viz.provRow("Note", D.provenance.note);
    },
  };
})();
