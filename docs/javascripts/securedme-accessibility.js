(function () {
  "use strict";

  var widgetId = "se-a11y-widget";
  var storageKey = "securedme:a11y:v2";
  var legacyStorageKey = "securedme:a11y:v1";
  var sprintTick = null;
  var sectionObserver = null;
  var currentSectionId = "";

  var neuroKeys = [
    "focusFrame",
    "quietNav",
    "calmLayout",
    "stimulusControl",
    "contentChunking",
    "currentSection",
    "readingPacer",
    "predictableMode",
    "literalLabels",
    "glossaryBoost",
    "checklistMode",
    "doneMarker",
    "resumePoint",
    "lowDemandMode",
    "highAgencyMode",
    "oversizedTargets"
  ];

  var defaults = {
    version: 2,
    open: false,
    profile: "",
    textScale: 0,
    textSpacing: false,
    contrastPlus: false,
    smartContrast: false,
    highlightLinks: false,
    readableFont: false,
    readingGuide: false,
    pauseAnimation: false,
    oversizedWidget: false,
    focusFrame: false,
    quietNav: false,
    calmLayout: false,
    stimulusControl: false,
    contentChunking: false,
    currentSection: false,
    readingPacer: "off",
    predictableMode: false,
    literalLabels: false,
    glossaryBoost: false,
    checklistMode: false,
    doneMarker: false,
    resumePoint: false,
    lowDemandMode: false,
    highAgencyMode: false,
    oversizedTargets: false,
    sprintMinutes: 15,
    sprintRunning: false,
    sprintEndAt: 0,
    microBreaks: true,
    microBreakActive: false,
    completedSections: {},
    lastSection: ""
  };

  var state = loadState();

  function canStore() {
    try {
      window.localStorage.setItem("__se_a11y_test__", "1");
      window.localStorage.removeItem("__se_a11y_test__");
      return true;
    } catch (error) {
      return false;
    }
  }

  function normalizeState(value) {
    var next = Object.assign({}, defaults, value || {});
    next.version = 2;
    next.textScale = Math.max(0, Math.min(3, Number(next.textScale) || 0));
    next.sprintMinutes = [5, 15, 25].indexOf(Number(next.sprintMinutes)) >= 0 ? Number(next.sprintMinutes) : 15;
    next.completedSections = typeof next.completedSections === "object" && next.completedSections ? next.completedSections : {};
    next.readingPacer = ["off", "horizontal", "vertical"].indexOf(next.readingPacer) >= 0 ? next.readingPacer : "off";
    return next;
  }

  function loadState() {
    if (!canStore()) {
      return Object.assign({}, defaults);
    }

    try {
      var stored = window.localStorage.getItem(storageKey);
      if (stored) {
        return normalizeState(JSON.parse(stored));
      }

      var legacy = window.localStorage.getItem(legacyStorageKey);
      if (legacy) {
        return normalizeState(JSON.parse(legacy));
      }
    } catch (error) {
      return Object.assign({}, defaults);
    }

    return Object.assign({}, defaults);
  }

  function saveState() {
    if (canStore()) {
      window.localStorage.setItem(storageKey, JSON.stringify(state));
    }
  }

  function setClass(name, active) {
    document.documentElement.classList.toggle(name, Boolean(active));
  }

  function sectionKey(id) {
    return window.location.pathname + "#" + id;
  }

  function getActiveSection() {
    if (currentSectionId) {
      return currentSectionId;
    }

    var first = document.querySelector(".md-typeset h2[id], .md-typeset h3[id], .md-typeset h1[id]");
    return first ? first.id : "";
  }

  function clearSectionMarks() {
    document.querySelectorAll(".se-a11y-current-section, .se-a11y-section-done").forEach(function (node) {
      node.classList.remove("se-a11y-current-section", "se-a11y-section-done");
    });
  }

  function applySectionMarks() {
    clearSectionMarks();

    if (state.currentSection && currentSectionId) {
      var current = document.getElementById(currentSectionId);
      if (current) {
        current.classList.add("se-a11y-current-section");
      }
    }

    if (state.doneMarker || state.checklistMode) {
      document.querySelectorAll(".md-typeset h2[id], .md-typeset h3[id]").forEach(function (heading) {
        heading.classList.toggle("se-a11y-section-done", Boolean(state.completedSections[sectionKey(heading.id)]));
      });
    }
  }

  function applyState() {
    document.documentElement.classList.remove(
      "se-a11y-text-1",
      "se-a11y-text-2",
      "se-a11y-text-3",
      "se-a11y-pacer-horizontal",
      "se-a11y-pacer-vertical"
    );

    if (state.textScale > 0) {
      document.documentElement.classList.add("se-a11y-text-" + state.textScale);
    }

    setClass("se-a11y-text-spacing", state.textSpacing);
    setClass("se-a11y-contrast-plus", state.contrastPlus);
    setClass("se-a11y-smart-contrast", state.smartContrast);
    setClass("se-a11y-highlight-links", state.highlightLinks);
    setClass("se-a11y-readable-font", state.readableFont);
    setClass("se-a11y-reading-guide", state.readingGuide);
    setClass("se-a11y-pause-animation", state.pauseAnimation);
    setClass("se-a11y-oversized-widget", state.oversizedWidget);
    setClass("se-a11y-focus-frame", state.focusFrame);
    setClass("se-a11y-quiet-nav", state.quietNav);
    setClass("se-a11y-calm-layout", state.calmLayout);
    setClass("se-a11y-stimulus-control", state.stimulusControl);
    setClass("se-a11y-content-chunking", state.contentChunking);
    setClass("se-a11y-current-section-mode", state.currentSection);
    setClass("se-a11y-predictable-mode", state.predictableMode);
    setClass("se-a11y-literal-labels", state.literalLabels);
    setClass("se-a11y-glossary-boost", state.glossaryBoost);
    setClass("se-a11y-checklist-mode", state.checklistMode);
    setClass("se-a11y-done-marker", state.doneMarker);
    setClass("se-a11y-resume-point", state.resumePoint);
    setClass("se-a11y-low-demand", state.lowDemandMode);
    setClass("se-a11y-high-agency", state.highAgencyMode);
    setClass("se-a11y-oversized-targets", state.oversizedTargets);

    if (state.readingPacer !== "off") {
      document.documentElement.classList.add("se-a11y-pacer-" + state.readingPacer);
    }

    applySectionMarks();
    updateSprintState();
    updateWidget();
  }

  function resetState() {
    state = Object.assign({}, defaults, { open: true });
    saveState();
    applyState();
  }

  function resetNeuroTools() {
    neuroKeys.forEach(function (key) {
      state[key] = defaults[key];
    });
    state.microBreaks = defaults.microBreaks;
    state.microBreakActive = false;
    state.sprintRunning = false;
    state.sprintEndAt = 0;
    state.profile = "";
    saveState();
    applyState();
  }

  function setOpen(open) {
    state.open = Boolean(open);
    saveState();
    updateWidget();
  }

  function toggleValue(key) {
    state[key] = !state[key];
    state.profile = "";
    saveState();
    applyState();
  }

  function applyProfile(profile) {
    var base = Object.assign({}, defaults, {
      open: true,
      profile: profile,
      completedSections: state.completedSections || {},
      lastSection: state.lastSection || ""
    });

    if (profile === "teacher") {
      base.readableFont = true;
      base.highlightLinks = true;
      base.pauseAnimation = true;
      base.currentSection = true;
    }

    if (profile === "lowVision") {
      base.textScale = 2;
      base.contrastPlus = true;
      base.smartContrast = true;
      base.oversizedWidget = true;
      base.oversizedTargets = true;
    }

    if (profile === "dyslexia") {
      base.readableFont = true;
      base.textSpacing = true;
      base.readingGuide = true;
      base.readingPacer = "horizontal";
      base.contentChunking = true;
    }

    if (profile === "motionSafe") {
      base.pauseAnimation = true;
      base.smartContrast = true;
      base.predictableMode = true;
    }

    if (profile === "neuroFocus") {
      base.focusFrame = true;
      base.currentSection = true;
      base.contentChunking = true;
      base.quietNav = true;
    }

    if (profile === "adhdSprint") {
      base.focusFrame = true;
      base.currentSection = true;
      base.sprintMinutes = 15;
      base.microBreaks = true;
      base.lowDemandMode = true;
      base.readingPacer = "horizontal";
    }

    if (profile === "autismCalm") {
      base.predictableMode = true;
      base.literalLabels = true;
      base.calmLayout = true;
      base.stimulusControl = true;
      base.pauseAnimation = true;
      base.quietNav = true;
    }

    if (profile === "sensorySafe") {
      base.calmLayout = true;
      base.stimulusControl = true;
      base.pauseAnimation = true;
      base.smartContrast = true;
      base.lowDemandMode = true;
    }

    if (profile === "deepWork") {
      base.focusFrame = true;
      base.quietNav = true;
      base.currentSection = true;
      base.highAgencyMode = true;
      base.sprintMinutes = 25;
    }

    state = base;
    saveState();
    applyState();
  }

  function cycleTextScale() {
    state.textScale = state.textScale >= 3 ? 0 : state.textScale + 1;
    state.profile = "";
    saveState();
    applyState();
  }

  function cyclePacer() {
    var order = ["off", "horizontal", "vertical"];
    var next = order[(order.indexOf(state.readingPacer) + 1) % order.length];
    state.readingPacer = next;
    state.readingGuide = next !== "off";
    state.profile = "";
    saveState();
    applyState();
  }

  function cycleSprintMinutes() {
    var order = [5, 15, 25];
    state.sprintMinutes = order[(order.indexOf(state.sprintMinutes) + 1) % order.length];
    if (state.sprintRunning) {
      state.sprintEndAt = Date.now() + state.sprintMinutes * 60 * 1000;
    }
    saveState();
    updateWidget();
  }

  function toggleSprint() {
    state.microBreakActive = false;
    if (state.sprintRunning) {
      state.sprintRunning = false;
      state.sprintEndAt = 0;
    } else {
      state.sprintRunning = true;
      state.sprintEndAt = Date.now() + state.sprintMinutes * 60 * 1000;
    }
    saveState();
    updateWidget();
  }

  function updateSprintState() {
    if (!state.sprintRunning) {
      return;
    }

    if (Date.now() >= state.sprintEndAt) {
      state.sprintRunning = false;
      state.sprintEndAt = 0;
      state.microBreakActive = Boolean(state.microBreaks);
      saveState();
    }
  }

  function sprintLabel() {
    updateSprintState();
    if (state.sprintRunning && state.sprintEndAt) {
      var remaining = Math.max(0, state.sprintEndAt - Date.now());
      var minutes = Math.floor(remaining / 60000);
      var seconds = Math.floor((remaining % 60000) / 1000);
      return minutes + ":" + String(seconds).padStart(2, "0");
    }
    if (state.microBreakActive) {
      return "Break";
    }
    return state.sprintMinutes + " min";
  }

  function markCurrentSectionDone() {
    var id = getActiveSection();
    if (!id) {
      return;
    }
    state.completedSections[sectionKey(id)] = true;
    state.doneMarker = true;
    saveState();
    applyState();
  }

  function resumeLastSection() {
    if (!state.lastSection) {
      return;
    }
    if (state.lastSection.indexOf(window.location.pathname + "#") !== 0) {
      window.location.href = state.lastSection;
      return;
    }
    var target = state.lastSection.split("#")[1];
    var node = target ? document.getElementById(target) : null;
    if (node) {
      node.scrollIntoView({ block: "start", behavior: state.pauseAnimation || state.predictableMode ? "auto" : "smooth" });
    }
  }

  function panelMarkup() {
    return [
      '<button class="se-a11y-launcher" type="button" aria-controls="se-a11y-panel" aria-expanded="false">',
      '  <span class="se-a11y-launcher__mark" aria-hidden="true"></span>',
      '  <span class="se-a11y-launcher__text">Access</span>',
      '</button>',
      '<section class="se-a11y-panel" id="se-a11y-panel" role="dialog" aria-label="Accessibility menu" aria-hidden="true">',
      '  <header class="se-a11y-panel__header">',
      '    <div>',
      '      <p class="se-a11y-panel__kicker">CTRL+U | ESC | CTRL+ALT+S</p>',
      '      <h2>Access Console</h2>',
      '      <p>Self-hosted comfort tools. No tracking. No diagnosis.</p>',
      '    </div>',
      '    <button class="se-a11y-close" type="button" aria-label="Close accessibility menu">Close</button>',
      '  </header>',
      '  <div class="se-a11y-language" aria-label="Language status">',
      '    <span>US</span>',
      '    <strong>English / Francais</strong>',
      '  </div>',
      '  <section class="se-a11y-section" aria-labelledby="se-a11y-profiles">',
      '    <h3 id="se-a11y-profiles">Profiles</h3>',
      '    <div class="se-a11y-grid se-a11y-grid--profiles">',
      '      <button type="button" data-profile="teacher">Teacher Focus</button>',
      '      <button type="button" data-profile="lowVision">Low Vision</button>',
      '      <button type="button" data-profile="dyslexia">Dyslexia Support</button>',
      '      <button type="button" data-profile="motionSafe">Motion Safe</button>',
      '      <button type="button" data-profile="neuroFocus">Neuro Focus</button>',
      '      <button type="button" data-profile="adhdSprint">ADHD Sprint</button>',
      '      <button type="button" data-profile="autismCalm">Autism Calm</button>',
      '      <button type="button" data-profile="sensorySafe">Sensory Safe</button>',
      '      <button type="button" data-profile="deepWork">Deep Work / Hyperfocus</button>',
      '    </div>',
      '  </section>',
      '  <section class="se-a11y-section" aria-labelledby="se-a11y-core">',
      '    <h3 id="se-a11y-core">Core Adjustments</h3>',
      '    <div class="se-a11y-grid">',
      '      <button type="button" data-action="textScale">Bigger Text <span data-text-scale>0/3</span></button>',
      '      <button type="button" data-toggle="textSpacing">Text Spacing</button>',
      '      <button type="button" data-toggle="contrastPlus">Contrast +</button>',
      '      <button type="button" data-toggle="smartContrast">Smart Contrast</button>',
      '      <button type="button" data-toggle="highlightLinks">Highlight Links</button>',
      '      <button type="button" data-toggle="readableFont">Readable Font</button>',
      '      <button type="button" data-toggle="pauseAnimation">Pause Animation</button>',
      '      <button type="button" data-toggle="oversizedWidget">Oversized Widget</button>',
      '    </div>',
      '  </section>',
      '  <section class="se-a11y-section" aria-labelledby="se-a11y-neuro">',
      '    <h3 id="se-a11y-neuro">Neurodivergent Comfort</h3>',
      '    <div class="se-a11y-grid">',
      '      <button type="button" data-toggle="focusFrame">Focus Frame</button>',
      '      <button type="button" data-toggle="quietNav">Quiet Nav</button>',
      '      <button type="button" data-toggle="calmLayout">Calm Layout</button>',
      '      <button type="button" data-toggle="stimulusControl">Stimulus Control</button>',
      '      <button type="button" data-toggle="contentChunking">Content Chunking</button>',
      '      <button type="button" data-toggle="currentSection">Current Section</button>',
      '      <button type="button" data-action="readingPacer">Reading Pacer <span data-pacer-state>Off</span></button>',
      '      <button type="button" data-toggle="predictableMode">Predictable Mode</button>',
      '      <button type="button" data-toggle="literalLabels">Literal Labels</button>',
      '      <button type="button" data-toggle="glossaryBoost">Glossary Boost</button>',
      '    </div>',
      '  </section>',
      '  <section class="se-a11y-section" aria-labelledby="se-a11y-focus">',
      '    <h3 id="se-a11y-focus">Focus + Hyperactivity</h3>',
      '    <div class="se-a11y-grid">',
      '      <button type="button" data-action="sprintToggle">Sprint Timer <span data-sprint-label>15 min</span></button>',
      '      <button type="button" data-action="sprintMinutes">Sprint Length <span data-sprint-minutes>15</span></button>',
      '      <button type="button" data-toggle="microBreaks">Micro Breaks</button>',
      '      <button type="button" data-toggle="checklistMode">Checklist Mode</button>',
      '      <button type="button" data-action="markDone">Done Marker</button>',
      '      <button type="button" data-toggle="resumePoint">Resume Point</button>',
      '      <button type="button" data-action="resume">Resume Last</button>',
      '      <button type="button" data-toggle="lowDemandMode">Low Demand Mode</button>',
      '      <button type="button" data-toggle="highAgencyMode">High Agency Mode</button>',
      '      <button type="button" data-toggle="oversizedTargets">Oversized Targets+</button>',
      '    </div>',
      '  </section>',
      '  <section class="se-a11y-section" aria-labelledby="se-a11y-reset">',
      '    <h3 id="se-a11y-reset">Reset</h3>',
      '    <div class="se-a11y-grid se-a11y-grid--reset">',
      '      <button type="button" data-action="resetNeuro">Reset Neuro Tools</button>',
      '      <button type="button" data-action="reset">Reset All</button>',
      '    </div>',
      '  </section>',
      '  <footer class="se-a11y-panel__footer">',
      '    <strong>SecuredMe Education</strong>',
      '    <span>Dark/Light mode is separate. These controls stay local to this browser.</span>',
      '  </footer>',
      '</section>',
      '<div class="se-a11y-guide" aria-hidden="true"></div>',
      '<div class="se-a11y-break" role="status" aria-live="polite">Sprint complete. Take a micro break, then choose the next small step.</div>'
    ].join("");
  }

  function makeWidget() {
    var widget = document.createElement("div");
    widget.id = widgetId;
    widget.className = "se-a11y-widget";
    widget.innerHTML = panelMarkup();
    document.body.appendChild(widget);
    bindWidget(widget);
    return widget;
  }

  function bindWidget(widget) {
    if (widget.dataset.bound === "true") {
      return;
    }

    widget.dataset.bound = "true";

    widget.addEventListener("click", function (event) {
      var launcher = event.target.closest(".se-a11y-launcher");
      var close = event.target.closest(".se-a11y-close");
      var profile = event.target.closest("[data-profile]");
      var toggle = event.target.closest("[data-toggle]");
      var action = event.target.closest("[data-action]");

      if (launcher) {
        setOpen(!state.open);
      } else if (close) {
        setOpen(false);
      } else if (profile) {
        applyProfile(profile.dataset.profile);
      } else if (toggle) {
        toggleValue(toggle.dataset.toggle);
      } else if (action && action.dataset.action === "textScale") {
        cycleTextScale();
      } else if (action && action.dataset.action === "readingPacer") {
        cyclePacer();
      } else if (action && action.dataset.action === "sprintToggle") {
        toggleSprint();
      } else if (action && action.dataset.action === "sprintMinutes") {
        cycleSprintMinutes();
      } else if (action && action.dataset.action === "markDone") {
        markCurrentSectionDone();
      } else if (action && action.dataset.action === "resume") {
        resumeLastSection();
      } else if (action && action.dataset.action === "resetNeuro") {
        resetNeuroTools();
      } else if (action && action.dataset.action === "reset") {
        resetState();
      }
    });
  }

  function updateWidget() {
    var widget = document.getElementById(widgetId);
    if (!widget) {
      return;
    }

    var launcher = widget.querySelector(".se-a11y-launcher");
    var panel = widget.querySelector(".se-a11y-panel");

    widget.dataset.open = state.open ? "true" : "false";
    launcher.setAttribute("aria-expanded", state.open ? "true" : "false");
    panel.setAttribute("aria-hidden", state.open ? "false" : "true");

    widget.querySelectorAll("[data-profile]").forEach(function (button) {
      var active = button.dataset.profile === state.profile;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });

    widget.querySelectorAll("[data-toggle]").forEach(function (button) {
      var active = Boolean(state[button.dataset.toggle]);
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });

    widget.querySelectorAll("[data-text-scale]").forEach(function (label) {
      label.textContent = state.textScale + "/3";
    });

    widget.querySelectorAll("[data-pacer-state]").forEach(function (label) {
      label.textContent = state.readingPacer.charAt(0).toUpperCase() + state.readingPacer.slice(1);
    });

    widget.querySelectorAll("[data-sprint-label]").forEach(function (label) {
      label.textContent = sprintLabel();
    });

    widget.querySelectorAll("[data-sprint-minutes]").forEach(function (label) {
      label.textContent = String(state.sprintMinutes);
    });

    document.querySelectorAll(".se-a11y-break").forEach(function (notice) {
      notice.dataset.active = state.microBreakActive ? "true" : "false";
    });
  }

  function moveGuide(event) {
    if (!state.readingGuide && state.readingPacer === "off") {
      return;
    }

    var guide = document.querySelector(".se-a11y-guide");
    if (!guide) {
      return;
    }

    if (state.readingPacer === "vertical") {
      guide.style.transform = "translateX(" + Math.max(0, event.clientX - 1) + "px)";
    } else {
      guide.style.transform = "translateY(" + Math.max(0, event.clientY - 16) + "px)";
    }
  }

  function observeSections() {
    if (sectionObserver) {
      sectionObserver.disconnect();
    }

    var headings = document.querySelectorAll(".md-typeset h1[id], .md-typeset h2[id], .md-typeset h3[id]");
    if (!headings.length || typeof IntersectionObserver === "undefined") {
      currentSectionId = getActiveSection();
      applySectionMarks();
      return;
    }

    sectionObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          currentSectionId = entry.target.id;
          if (state.resumePoint) {
            state.lastSection = sectionKey(currentSectionId);
            saveState();
          }
          applySectionMarks();
          updateWidget();
        }
      });
    }, { rootMargin: "-12% 0px -72% 0px", threshold: 0.01 });

    headings.forEach(function (heading) {
      sectionObserver.observe(heading);
    });
  }

  function bindGlobalShortcuts() {
    if (window.__securedmeA11yBound) {
      return;
    }

    window.__securedmeA11yBound = true;

    document.addEventListener("keydown", function (event) {
      var key = event.key.toLowerCase();

      if (event.ctrlKey && !event.altKey && key === "u") {
        event.preventDefault();
        setOpen(!state.open);
      }

      if (event.ctrlKey && event.altKey && key === "s") {
        event.preventDefault();
        toggleSprint();
      }

      if (key === "escape" && state.open) {
        setOpen(false);
      }
    });

    document.addEventListener("mousemove", moveGuide);
  }

  function startSprintTicker() {
    if (sprintTick) {
      return;
    }

    sprintTick = window.setInterval(function () {
      if (state.sprintRunning) {
        updateSprintState();
        updateWidget();
      }
    }, 1000);
  }

  function start() {
    bindGlobalShortcuts();
    startSprintTicker();

    var widget = document.getElementById(widgetId) || makeWidget();
    bindWidget(widget);
    observeSections();
    applyState();
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(start);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
}());
