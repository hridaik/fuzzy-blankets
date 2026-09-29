/* Tab 10 -- Closure C: timing susceptibility. Is variation across
   intervention ONSET time materially larger than variation across actuator
   identity at a fixed onset? Deliberately small/descriptive -- no learned
   adaptive controller, just the quantitative comparison. */
(function () {
  "use strict";
  const D = TAB10_DATA;

  function renderPerState() {
    const wrap = document.getElementById("t10PerState");
    const rows = (D.closureC.per_state || []);
    if (!rows.length) { wrap.innerHTML = `<p class="footnote">No timing rollouts available.</p>`; return; }
    wrap.innerHTML = rows.map(r => {
      const onsets = Object.keys(r.onset_means).sort((a,b) => +a - +b);
      const vals = onsets.map(o => r.onset_means[o]);
      const maxAbs = Math.max(...vals.map(Math.abs), 1e-6, r.mean_within_onset_actuator_spread || 0);
      return `<div style="border-bottom:1px solid var(--border);padding:5px 0;">
        <div style="font-size:10px;color:var(--muted);">${r.state_id}</div>
        <div style="display:flex;gap:8px;align-items:flex-end;height:50px;margin:3px 0;">
          ${onsets.map(o => {
            const v = r.onset_means[o];
            const h = Math.max(2, Math.abs(v) / maxAbs * 40);
            return `<div style="text-align:center;">
              <div style="height:${h}px;width:22px;background:${v>=0?'var(--accent)':'var(--bad)'};margin:0 auto;"></div>
              <div style="font-size:9px;color:var(--muted);">t+${o}</div>
            </div>`;
          }).join("")}
        </div>
        <div class="footnote">onset range ${Viz.fmtNum(r.onset_range)} vs mean within-onset actuator spread
          ${r.mean_within_onset_actuator_spread !== null ? Viz.fmtNum(r.mean_within_onset_actuator_spread) : "n/a"}
          -- <b style="color:${r.between_onset_ge_within_actuator ? 'var(--good)':'var(--bad)'}">
          onset ${r.between_onset_ge_within_actuator ? "&ge;" : "&lt;"} actuator spread</b></div>
      </div>`;
    }).join("");
  }

  function renderSummary() {
    const wrap = document.getElementById("t10Summary");
    const c = D.closureC;
    if (!c.onset_range_ci) { wrap.innerHTML = `<p class="footnote">No summary available.</p>`; return; }
    wrap.innerHTML = `
      <div class="metric"><span>Mean onset-range of &Delta;J_conservative</span><b>${Viz.fmtNum(c.onset_range_ci.mean)}</b></div>
      <div class="footnote">90% CI [${Viz.fmtNum(c.onset_range_ci.lo)}, ${Viz.fmtNum(c.onset_range_ci.hi)}], n=${c.onset_range_ci.n} states</div>
      <div class="metric" style="margin-top:6px;"><span>Mean within-onset actuator spread</span><b>${Viz.fmtNum(c.within_onset_spread_ci.mean)}</b></div>
      <div class="footnote">90% CI [${Viz.fmtNum(c.within_onset_spread_ci.lo)}, ${Viz.fmtNum(c.within_onset_spread_ci.hi)}], n=${c.within_onset_spread_ci.n} states</div>
      <div class="metric" style="margin-top:6px;"><span>States where onset variation &ge; actuator variation</span><b>${c.n_states_onset_dominates} / ${(D.closureC.per_state||[]).length}</b></div>`;
  }

  function renderOnsetAvailability() {
    const wrap = document.getElementById("t10Onsets");
    const rows = D.onset_summary || [];
    let html = `<table style="border-collapse:collapse;font-size:9px;width:100%;"><tr style="color:var(--muted);">
      <td>state</td><td>onset</td><td>status</td><td>n_target</td><td>boundary</td><td>live parent</td></tr>`;
    rows.forEach(r => {
      const av = r.class_availability || {};
      html += `<tr><td>${(r.state_id||'').replace('sclosure_','s')}</td><td>t+${r.onset_offset}</td><td>${r.status}</td>
        <td>${r.n_target||''}</td><td>${av.boundary_member ?? ''}</td><td>${av.live_exterior_parent ?? ''}</td></tr>`;
    });
    html += `</table>`;
    wrap.innerHTML = html;
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">10. Closure C — timing susceptibility</h2>
      <p class="qCaption">Is outcome variation across intervention ONSET time materially larger than variation across
      actuator identity at a fixed onset? First 4 states, onsets {0,4,8,12} real steps, live_exterior_parent and
      boundary_member policies only. Deliberately small -- not an adaptive-controller experiment.</p>
      <div class="panelBody">
        <div class="stageWrap">
          <div class="card"><h3>Effect vs onset, per state</h3><div id="t10PerState"></div></div>
        </div>
        <div class="sideWrap">
          <div class="card"><h3>Onset vs actuator variance summary</h3><div id="t10Summary"></div></div>
          <div class="card"><h3>Class availability / live-edge topology over time</h3><div id="t10Onsets" style="max-height:220px;overflow-y:auto;"></div></div>
        </div>
      </div>`;
    renderPerState(); renderSummary(); renderOnsetAvailability();
  }

  window.Tabs = window.Tabs || {};
  window.Tabs.tab10 = {
    legend: [
      { shape: "dot", color: "var(--accent)", label: "positive onset-mean ΔJ" },
      { shape: "dot", color: "var(--bad)", label: "negative onset-mean ΔJ" },
    ],
    render,
    onActivate() { Viz.TL.bind("tab10", null); },
    provenanceHtml() {
      return Viz.provRow("Source", D.provenance.source) + Viz.provRow("Method", D.provenance.method) +
        Viz.provRow("n rollouts", D.n_rollouts) +
        Viz.provRow("Note", "Not an adaptive-controller experiment -- quantitative comparison only, per task spec.");
    },
  };
})();
