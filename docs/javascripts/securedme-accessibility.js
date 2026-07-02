(function () {
  "use strict";

  var widgetId = "se-a11y-widget";
  var storageKey = "securedme:a11y:v1";

  var defaults = {
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
    oversizedWidget: false
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

  function loadState() {
    if (!canStore()) {
      return Object.assign({}, defaults);
    }

    try {
      return Object.assign({}, defaults, JSON.parse(window.localStorage.getItem(storageKey) || "{}"));
    } catch (error) {
      return Object.assign({}, defaults);
    }
  }

  function saveState() {
    if (canStore()) {
      window.localStorage.setItem(storageKey, JSON.stringify(state));
    }
  }

  function setClass(name, active) {
    document.documentElement.classList.toggle(name, Boolean(active));
  }

  function applyState() {
    document.documentElement.classList.remove("se-a11y-text-1", "se-a11y-text-2", "se-a11y-text-3");

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
    updateWidget();
  }

  function resetState() {
    state = Object.assign({}, defaults, { open: true });
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
    var base = Object.assign({}, defaults, { open: true, profile: profile });

    if (profile === "teacher") {
      base.readableFont = true;
      base.highlightLinks = true;
      base.pauseAnimation = true;
    }

    if (profile === "lowVision") {
      base.textScale = 2;
      base.contrastPlus = true;
      base.smartContrast = true;
      base.oversizedWidget = true;
    }

    if (profile === "dyslexia") {
      base.readableFont = true;
      base.textSpacing = true;
      base.readingGuide = true;
    }

    if (profile === "motionSafe") {
      base.pauseAnimation = true;
      base.smartContrast = true;
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

  function panelMarkup() {
    return [
      '<button class="se-a11y-launcher" type="button" aria-controls="se-a11y-panel" aria-expanded="false">',
      '  <span class="se-a11y-launcher__mark" aria-hidden="true"></span>',
      '  <span class="se-a11y-launcher__text">Access</span>',
      '</button>',
      '<section class="se-a11y-panel" id="se-a11y-panel" role="dialog" aria-label="Accessibility menu" aria-hidden="true">',
      '  <header class="se-a11y-panel__header">',
      '    <div>',
      '      <p class="se-a11y-panel__kicker">CTRL+U</p>',
      '      <h2>Accessibility Menu</h2>',
      '    </div>',
      '    <button class="se-a11y-close" type="button" aria-label="Close accessibility menu">Close</button>',
      '  </header>',
      '  <div class="se-a11y-language" aria-label="Language status">',
      '    <span>US</span>',
      '    <strong>English / Francais</strong>',
      '  </div>',
      '  <h3>Profiles</h3>',
      '  <div class="se-a11y-grid se-a11y-grid--profiles">',
      '    <button type="button" data-profile="teacher">Teacher Focus</button>',
      '    <button type="button" data-profile="lowVision">Low Vision</button>',
      '    <button type="button" data-profile="dyslexia">Dyslexia Support</button>',
      '    <button type="button" data-profile="motionSafe">Motion Safe</button>',
      '  </div>',
      '  <h3>Adjustments</h3>',
      '  <div class="se-a11y-grid">',
      '    <button type="button" data-action="textScale">Bigger Text <span data-text-scale>0/3</span></button>',
      '    <button type="button" data-toggle="textSpacing">Text Spacing</button>',
      '    <button type="button" data-toggle="contrastPlus">Contrast +</button>',
      '    <button type="button" data-toggle="smartContrast">Smart Contrast</button>',
      '    <button type="button" data-toggle="highlightLinks">Highlight Links</button>',
      '    <button type="button" data-toggle="readableFont">Readable Font</button>',
      '    <button type="button" data-toggle="readingGuide">Reading Guide</button>',
      '    <button type="button" data-toggle="pauseAnimation">Pause Animation</button>',
      '    <button type="button" data-toggle="oversizedWidget">Oversized Widget</button>',
      '    <button type="button" data-action="reset">Reset All</button>',
      '  </div>',
      '  <footer class="se-a11y-panel__footer">',
      '    <strong>SecuredMe Education</strong>',
      '    <span>Self-hosted accessibility support. Dark/Light mode is the top-right button.</span>',
      '  </footer>',
      '</section>',
      '<div class="se-a11y-guide" aria-hidden="true"></div>'
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
  }

  function moveGuide(event) {
    if (!state.readingGuide) {
      return;
    }

    var guide = document.querySelector(".se-a11y-guide");
    if (guide) {
      guide.style.transform = "translateY(" + Math.max(0, event.clientY - 16) + "px)";
    }
  }

  function bindGlobalShortcuts() {
    if (window.__securedmeA11yBound) {
      return;
    }

    window.__securedmeA11yBound = true;

    document.addEventListener("keydown", function (event) {
      var key = event.key.toLowerCase();

      if (event.ctrlKey && key === "u") {
        event.preventDefault();
        setOpen(!state.open);
      }

      if (key === "escape" && state.open) {
        setOpen(false);
      }
    });

    document.addEventListener("mousemove", moveGuide);
  }

  function start() {
    bindGlobalShortcuts();

    var widget = document.getElementById(widgetId) || makeWidget();
    bindWidget(widget);
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
