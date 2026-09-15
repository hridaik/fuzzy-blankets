/* App shell: tab switching, progress rail, legend, Next button, provenance
   drawer wiring. Individual tabs register themselves on window.Tabs[id]. */
(function () {
  "use strict";
  const TAB_ORDER = ["tab1", "tab2", "tab3", "tab4", "tab5", "tab6"];
  const TAB_META = {
    tab1: { num: 1, title: "Boundary", rail: "OBSERVE" },
    tab2: { num: 2, title: "Causal access", rail: "INFER" },
    tab3: { num: 3, title: "Control", rail: "PROBE" },
    tab4: { num: 4, title: "Collective landscape", rail: "CONTROL" },
    tab5: { num: 5, title: "Adaptive", rail: "ADAPT" },
    tab6: { num: 6, title: "Translation", rail: "MOVE" },
  };
  // NOTE: the rail word for tab3/tab4 intentionally follows the brief's fixed
  // OBSERVE/INFER/PROBE/CONTROL/ADAPT/MOVE sequence positionally (one word
  // per tab, left to right), not a per-tab semantic re-derivation.

  let activeTab = "tab1";

  function renderRail() {
    const rail = document.getElementById("progressRail");
    rail.innerHTML = "";
    const activeIdx = TAB_ORDER.indexOf(activeTab);
    TAB_ORDER.forEach((id, i) => {
      const step = document.createElement("div");
      step.className = "railStep" + (i === activeIdx ? " active" : i < activeIdx ? " done" : "");
      step.innerHTML = `<span class="railDot"></span><span class="railLabel">${TAB_META[id].rail}</span>`;
      rail.appendChild(step);
      if (i < TAB_ORDER.length - 1) {
        const arrow = document.createElement("span");
        arrow.className = "railArrow"; arrow.textContent = "→";
        rail.appendChild(arrow);
      }
    });
  }

  function renderTabNav() {
    const nav = document.getElementById("tabNav");
    nav.innerHTML = "";
    TAB_ORDER.forEach((id) => {
      const b = document.createElement("button");
      b.className = "tabBtn" + (id === activeTab ? " active" : "");
      b.textContent = `${TAB_META[id].num}. ${TAB_META[id].title}`;
      b.addEventListener("click", () => switchTab(id));
      nav.appendChild(b);
    });
  }

  function renderLegend() {
    const tab = window.Tabs[activeTab];
    const legend = document.getElementById("legend");
    legend.innerHTML = "";
    (tab.legend || []).forEach((item) => {
      const span = document.createElement("span");
      span.className = "swatch";
      let glyph = "";
      if (item.shape === "ring") glyph = `<span class="ring" style="border-color:${item.color}"></span>`;
      else if (item.shape === "tri") glyph = `<span class="tri" style="border-bottom-color:${item.color}"></span>`;
      else glyph = `<span class="dot" style="background:${item.color}"></span>`;
      span.innerHTML = glyph + `<span>${item.label}</span>`;
      legend.appendChild(span);
    });
  }

  function renderNextButton() {
    const container = document.getElementById("nextRowContainer");
    container.innerHTML = "";
    const idx = TAB_ORDER.indexOf(activeTab);
    if (idx < TAB_ORDER.length - 1) {
      const row = document.createElement("div");
      row.className = "nextRow";
      const nextId = TAB_ORDER[idx + 1];
      const btn = document.createElement("button");
      btn.className = "nextBtn";
      btn.textContent = `Next: ${TAB_META[nextId].num}. ${TAB_META[nextId].title} →`;
      btn.addEventListener("click", () => switchTab(nextId));
      row.appendChild(btn);
      container.appendChild(row);
    }
  }

  function switchTab(id) {
    if (window.Tabs[activeTab] && window.Tabs[activeTab].onDeactivate) window.Tabs[activeTab].onDeactivate();
    Viz.TL.pause();
    document.querySelectorAll(".tabPanel").forEach((p) => { p.hidden = p.id !== "panel-" + id; });
    activeTab = id;
    const tab = window.Tabs[id];
    if (!tab.rendered) { tab.render(document.getElementById("panel-" + id)); tab.rendered = true; }
    renderRail(); renderTabNav(); renderLegend(); renderNextButton();
    if (tab.onActivate) tab.onActivate();
    else Viz.TL.bind(id, null);
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("dataDrawerBtn").addEventListener("click", () => {
      const tab = window.Tabs[activeTab];
      Viz.Prov.open(tab.provenanceHtml ? tab.provenanceHtml() : "<p>No provenance registered.</p>");
    });
    switchTab("tab1");
  });

  window.App = { switchTab, TAB_ORDER, TAB_META };
})();
