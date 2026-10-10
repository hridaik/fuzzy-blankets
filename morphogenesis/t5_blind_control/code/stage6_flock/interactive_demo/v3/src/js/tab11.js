/* Tab 11 -- Final translating-flock synthesis. One concise view: what
   worked, what failed, what was an artifact, what remains unresolved, why
   the programme moves to morphogenesis. No single success percentage. */
(function () {
  "use strict";
  const D = TAB11_DATA;
  const STATUS_COLOR = {
    "established": "var(--good)",
    "falsified": "var(--bad)",
    "weak positive, heterogeneous": "var(--warn)",
    "established, duration-dependent": "var(--warn)",
  };
  function colorFor(status) {
    return STATUS_COLOR[status] || "var(--muted)";
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">11. Final translating-flock synthesis</h2>
      <p class="qCaption">${D.why_morphogenesis_next}</p>
      <div class="panelBody">
        <div class="stageWrap">
          <div id="t11Axes"></div>
        </div>
        <div class="sideWrap">
          <div class="card"><h3>Final decision</h3><p class="footnote" style="font-size:11px;">${D.final_decision}</p></div>
          <div class="card"><h3>Full writeup</h3>
            <p class="footnote">stage6_flock/TRANSLATING_FLOCK_FINAL_SYNTHESIS.md<br>
            final_translating_flock_closure/FINAL_CLOSURE_FINDINGS.md<br>
            final_translating_flock_closure/MORPHOGENESIS_HANDOFF.md</p>
          </div>
        </div>
      </div>`;
    const axesWrap = document.getElementById("t11Axes");
    axesWrap.innerHTML = D.axes.map(a => `
      <div class="card" style="margin-bottom:8px;">
        <h3 style="display:flex;justify-content:space-between;align-items:center;">
          <span>${a.axis}</span>
          <span style="font-size:9.5px;color:${colorFor(a.status)};text-transform:none;letter-spacing:0;font-weight:600;">${a.status}</span>
        </h3>
        <p class="footnote" style="font-size:11px;color:var(--ink);">${a.text}</p>
      </div>`).join("");
  }

  window.Tabs = window.Tabs || {};
  window.Tabs.tab11 = {
    legend: [
      { shape: "dot", color: "var(--good)", label: "established" },
      { shape: "dot", color: "var(--warn)", label: "weak / heterogeneous / duration-dependent" },
      { shape: "dot", color: "var(--bad)", label: "falsified" },
    ],
    render,
    onActivate() { Viz.TL.bind("tab11", null); },
    provenanceHtml() {
      return Viz.provRow("Source", D.provenance.source) +
        Viz.provRow("Note", "This tab is a curated digest of the written findings docs, not a new statistic.");
    },
  };
})();
