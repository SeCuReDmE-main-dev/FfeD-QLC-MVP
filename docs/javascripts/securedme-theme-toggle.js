(function () {
  "use strict";

  var buttonId = "se-theme-toggle";
  var storageKey = "securedme:theme:v1";
  var lightPaletteId = "__palette_0";
  var darkPaletteId = "__palette_1";

  function canStore() {
    try {
      window.localStorage.setItem("__se_test__", "1");
      window.localStorage.removeItem("__se_test__");
      return true;
    } catch (error) {
      return false;
    }
  }

  function storeScheme(scheme) {
    if (!canStore()) {
      return;
    }

    window.localStorage.setItem(storageKey, scheme);
  }

  function readStoredScheme() {
    if (!canStore()) {
      return "";
    }

    return window.localStorage.getItem(storageKey) || "";
  }

  function currentScheme() {
    var bodyScheme = document.body.getAttribute("data-md-color-scheme");
    if (bodyScheme === "slate" || bodyScheme === "default") {
      return bodyScheme;
    }

    var darkInput = document.getElementById(darkPaletteId);
    if (darkInput && darkInput.checked) {
      return "slate";
    }

    var storedScheme = readStoredScheme();
    if (storedScheme === "slate" || storedScheme === "default") {
      return storedScheme;
    }

    return "default";
  }

  function materialPaletteInput(scheme) {
    return document.getElementById(scheme === "slate" ? darkPaletteId : lightPaletteId);
  }

  function setFallbackScheme(scheme) {
    document.body.setAttribute("data-md-color-scheme", scheme);
    document.body.setAttribute("data-md-color-primary", "indigo");
    document.body.setAttribute("data-md-color-accent", scheme === "slate" ? "cyan" : "deep-purple");
  }

  function setScheme(scheme) {
    var input = materialPaletteInput(scheme);

    if (input) {
      input.checked = true;
      input.dispatchEvent(new Event("change", { bubbles: true }));
      input.dispatchEvent(new Event("input", { bubbles: true }));
    } else {
      setFallbackScheme(scheme);
    }

    storeScheme(scheme);
    window.setTimeout(syncButton, 0);
  }

  function applyStoredScheme() {
    var storedScheme = readStoredScheme();
    var bodyScheme = document.body.getAttribute("data-md-color-scheme");

    if ((storedScheme === "slate" || storedScheme === "default") && bodyScheme !== storedScheme) {
      setScheme(storedScheme);
    }
  }

  function syncButton() {
    var button = document.getElementById(buttonId);
    if (!button) {
      return;
    }

    var scheme = currentScheme();
    var darkActive = scheme === "slate";
    var label = darkActive ? "Light" : "Dark";
    var activeText = darkActive ? "Dark active" : "Light active";

    button.dataset.mode = scheme;
    button.setAttribute("aria-pressed", darkActive ? "true" : "false");
    button.setAttribute("aria-label", "Switch to " + (darkActive ? "light" : "dark") + " Education mode");
    button.setAttribute("title", "Switch to " + (darkActive ? "light" : "dark") + " Education mode");
    button.querySelector(".se-theme-toggle__label").textContent = label;
    button.querySelector(".se-theme-toggle__state").textContent = activeText;
  }

  function makeButton() {
    var button = document.createElement("button");
    button.id = buttonId;
    button.type = "button";
    button.className = "se-theme-toggle";
    button.innerHTML = [
      '<span class="se-theme-toggle__icon" aria-hidden="true"></span>',
      '<span class="se-theme-toggle__label">Dark</span>',
      '<span class="se-theme-toggle__state">Light active</span>'
    ].join("");

    button.addEventListener("click", function () {
      setScheme(currentScheme() === "slate" ? "default" : "slate");
    });

    return button;
  }

  function mountButton() {
    var existing = document.getElementById(buttonId);
    if (existing) {
      syncButton();
      return;
    }

    var button = makeButton();
    var palette = document.querySelector('.md-header__option[data-md-component="palette"]');
    var source = document.querySelector(".md-header__source");
    var search = document.querySelector(".md-search");
    var header = document.querySelector(".md-header__inner") || document.querySelector(".md-header");

    if (source && source.parentNode) {
      source.insertAdjacentElement("beforebegin", button);
    } else if (search && search.parentNode) {
      search.insertAdjacentElement("afterend", button);
    } else if (palette && palette.parentNode) {
      palette.insertAdjacentElement("afterend", button);
    } else if (header) {
      header.appendChild(button);
    } else {
      document.body.appendChild(button);
    }

    syncButton();
  }

  function bindGlobalSync() {
    if (window.__securedmeThemeToggleBound) {
      return;
    }

    window.__securedmeThemeToggleBound = true;

    document.addEventListener("change", function (event) {
      if (event.target && event.target.name === "__palette") {
        storeScheme(currentScheme());
        syncButton();
      }
    }, true);

    if (window.MutationObserver && document.body) {
      var observer = new MutationObserver(function (mutations) {
        var shouldSync = mutations.some(function (mutation) {
          return mutation.attributeName === "data-md-color-scheme";
        });

        if (shouldSync) {
          storeScheme(currentScheme());
          syncButton();
        }
      });

      observer.observe(document.body, { attributes: true });
      window.__securedmeThemeToggleObserver = observer;
    }
  }

  function start() {
    bindGlobalSync();
    applyStoredScheme();
    mountButton();
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(start);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
}());
