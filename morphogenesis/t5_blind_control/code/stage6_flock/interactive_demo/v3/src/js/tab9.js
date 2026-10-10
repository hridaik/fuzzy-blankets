/* Tab 9 -- Closure A: organizational roles. Class-level DeltaJ_conservative
   comparison (core / boundary / live exterior parent / near exterior
   non-parent), with the A_minus_j interior-actuation correction applied.
   Static analytic snapshot -- no timeline. */
(function () {
  "use strict";
  const D = TAB9_DATA;
  const CLASS_LABEL = { core_member: "Core member", boundary_member: "Boundary member",
    live_exterior_parent: "Live exterior parent", near_exterior_non_parent: "Near exterior non-parent" };
  const CLASS_COLOR = { core_member: "var(--core)", boundary_member: "var(--controlif)",
    live_exterior_parent: "var(--liveparent)", near_exterior_non_parent: "var(--nonparent)" };
  let useMinusJ = true;

  function ciRow(cls, ci) {
    if (!ci || ci.n === 0) return `<div class="metric"><span style="color:${CLASS_COLOR[cls]};">■</span> ${CLASS_LABEL[cls]}</div><div class="footnote">no actuators available in any state</div>`;
    return `<div class="metric"><span style="color:${CLASS_COLOR[cls]};">■</span> ${CLASS_LABEL[cls]} (n=${ci.n} states)</div>
      <div class="footnote">mean ${Viz.fmtNum(ci.mean)}, 90% CI [${Viz.fmtNum(ci.lo)}, ${Viz.fmtNum(ci.hi)}]</div>`;
  }

  function renderClasses() {
    const wrap = document.getElementById("t9Classes");
    const src = useMinusJ ? D.closureA.class_level_ci_minus_j : D.closureA.class_level_ci;
    // class_level_ci is {cls: {state_paired: ci, n_states_with_class}}; class_level_ci_minus_j is {cls: ci} directly
    wrap.innerHTML = ["core_member", "boundary_member", "live_exterior_parent", "near_exterior_non_parent"].map(cls => {
      const entry = src[cls];
      const ci = useMinusJ ? entry : (entry && entry.state_paired);
      return ciRow(cls, ci);
    }).join("");
  }

  function cmpRow(cmp) {
    if (!cmp || cmp.n_states === 0) return `<p class="footnote">${cmp ? cmp.cls_a + " vs " + cmp.cls_b : ""}: no co-occurring states.</p>`;
    const sig = cmp.diff_ci && (cmp.diff_ci.lo > 0 || cmp.diff_ci.hi < 0);
    return `<div class="metric"><span>${CLASS_LABEL[cmp.cls_a] || cmp.cls_a} &minus; ${CLASS_LABEL[cmp.cls_b] || cmp.cls_b}</span>
        <b style="color:${sig ? 'var(--good)' : 'var(--ink)'}">${Viz.fmtNum(cmp.mean_diff)}</b></div>
      <div class="footnote">n=${cmp.n_states} co-occurring states, 90% CI [${Viz.fmtNum(cmp.diff_ci.lo)}, ${Viz.fmtNum(cmp.diff_ci.hi)}]${sig ? " -- excludes zero" : " -- spans zero"}</div>`;
  }

  function renderComparisons() {
    const wrap = document.getElementById("t9Comparisons");
    const c = D.closureA.comparisons;
    wrap.innerHTML = cmpRow(c.boundary_vs_core) + cmpRow(c.boundary_vs_live_parent) + cmpRow(c.live_parent_vs_near_nonparent);
  }

  function renderInteriorExterior() {
    const ie = D.closureA.interior_vs_exterior_minus_j;
    const wrap = document.getElementById("t9InteriorExterior");
    if (!ie || ie.n_states === 0) { wrap.innerHTML = `<p class="footnote">No states with both interior and exterior classes available.</p>`; return; }
    wrap.innerHTML = `<div class="metric"><span>Interior (core+boundary) &minus; Exterior (live parent + non-parent), A_minus_j-corrected</span>
        <b>${Viz.fmtNum(ie.diff_ci.mean)}</b></div>
      <div class="footnote">n=${ie.n_states} states, 90% CI [${Viz.fmtNum(ie.diff_ci.lo)}, ${Viz.fmtNum(ie.diff_ci.hi)}]</div>`;
  }

  function renderAvailability() {
    const wrap = document.getElementById("t9Availability");
    const states = Object.keys(D.class_availability);
    let html = `<table style="border-collapse:collapse;font-size:9.5px;width:100%;"><tr style="color:var(--muted);">
      <td>state</td><td>core</td><td>boundary</td><td>live parent</td><td>non-parent</td></tr>`;
    states.forEach(s => {
      const a = D.class_availability[s];
      html += `<tr><td>${s.replace('sclosure_','s')}</td><td>${a.core_member}</td><td>${a.boundary_member}</td><td>${a.live_exterior_parent}</td><td>${a.near_exterior_non_parent}</td></tr>`;
    });
    html += `</table>`;
    wrap.innerHTML = html;
  }

  function render(container) {
    container.innerHTML = `
      <h2 class="qHeader">9. Closure A — organizational role / membership privilege</h2>
      <p class="qCaption">Does being inside the collective, on its organizational boundary, or an actual live exterior
      causal parent create a reproducible intervention channel, even though no single exterior bird's IDENTITY does?
      Interior/boundary actuators are scored with the A_minus_j correction (excludes the forced bird's own trivially-
      aligned heading from the alignment fraction) -- see INTERIOR_ACTUATION_METHOD_NOTE.md.</p>
      <div class="panelBody">
        <div class="stageWrap">
          <div class="card"><h3>Class-level mean &Delta;J_conservative (state-paired, 90% CI)</h3><div id="t9Classes"></div></div>
          <div class="card"><h3>Key paired comparisons (co-occurring states only)</h3><div id="t9Comparisons"></div></div>
          <div class="card"><h3>Interior vs exterior (pooled)</h3><div id="t9InteriorExterior"></div></div>
        </div>
        <div class="sideWrap">
          <div class="card"><h3>Class availability by state (at t0)</h3><div id="t9Availability"></div>
            <p class="footnote">At R=0.9 the expected live degree is &lt;1: boundary/live-parent status is a
            comparatively rare, transient event even for a visibly cohesive flock -- 5/8 states show zero of each
            at the single instant t0. Comparisons above use only states where the relevant classes co-occur.</p>
          </div>
          <div class="methodSelect" id="t9Toggles"></div>
        </div>
      </div>`;
    const toggles = document.getElementById("t9Toggles");
    [[true, "A_minus_j corrected"], [false, "Raw (uncorrected)"]].forEach(([val, label]) => {
      const b = document.createElement("button");
      b.className = "methodChip" + (useMinusJ === val ? " active" : "");
      b.textContent = label;
      b.addEventListener("click", () => {
        useMinusJ = val;
        toggles.querySelectorAll(".methodChip").forEach(x => x.classList.remove("active"));
        b.classList.add("active");
        renderClasses();
      });
      toggles.appendChild(b);
    });
    renderClasses(); renderComparisons(); renderInteriorExterior(); renderAvailability();
  }

  window.Tabs = window.Tabs || {};
  window.Tabs.tab9 = {
    legend: [
      { shape: "dot", color: "var(--core)", label: "core member" },
      { shape: "dot", color: "var(--controlif)", label: "boundary member" },
      { shape: "dot", color: "var(--liveparent)", label: "live exterior causal parent" },
      { shape: "dot", color: "var(--nonparent)", label: "near exterior non-parent" },
    ],
    render,
    onActivate() { Viz.TL.bind("tab9", null); },
    provenanceHtml() {
      return Viz.provRow("Source", D.provenance.source) + Viz.provRow("Method", D.provenance.method) +
        Viz.provRow("n rollouts", D.n_rollouts) +
        Viz.provRow("Independent unit", "STATE, not rollout or actuator -- see STATISTICAL_ANALYSIS.md");
    },
  };
})();
