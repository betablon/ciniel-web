/* ─────────────────────────────────────────────────────────────
   Ciniel — ciniel.app

   Three behaviours, all optional. Every page here is legible, navigable
   and complete with JavaScript switched off; this file only adds the
   pinned film tour, the nav's scrolled state, and the legal pages'
   one-language-at-a-time fold.
   ───────────────────────────────────────────────────────────── */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* ── nav: solid ground once the hero is behind it ──────── */

  var nav = document.getElementById("nav");
  if (nav) {
    var onNav = function () {
      nav.classList.toggle("is-stuck", window.scrollY > 24);
    };
    window.addEventListener("scroll", onNav, { passive: true });
    onNav();
  }

  /* ── legal pages: one language at a time ───────────────
     The Impressum carries the same notice twice, in English and German,
     because both have to be on the page. Reading it should not mean
     scrolling past a translation you can't use — so with scripting on,
     the two jump links become a switch and only one half is shown. The
     divider between them exists purely to separate the stacked
     languages, so it goes away with them.                            */

  var langSwitch = document.querySelector("[data-lang-switch]");
  if (langSwitch) {
    var panels = Array.prototype.slice.call(document.querySelectorAll("[data-lang-panel]"));
    var opts   = Array.prototype.slice.call(langSwitch.querySelectorAll("[data-lang-to]"));
    var rule   = document.querySelector("[data-lang-rule]");

    var showLang = function (lang) {
      panels.forEach(function (p) {
        p.hidden = p.getAttribute("data-lang-panel") !== lang;
      });
      opts.forEach(function (a) {
        var on = a.getAttribute("data-lang-to") === lang;
        a.classList.toggle("is-on", on);
        if (on) { a.setAttribute("aria-current", "true"); }
        else    { a.removeAttribute("aria-current"); }
      });
      if (rule) rule.hidden = true;
      document.documentElement.lang = lang;
    };

    opts.forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();               // no jump: the panel is already at the top
        var lang = a.getAttribute("data-lang-to");
        showLang(lang);
        if (history.replaceState) history.replaceState(null, "", "#" + lang);
      });
    });

    // A hash wins — someone was linked straight to one language. Otherwise
    // follow the browser, and fall back to English.
    var fromHash = function () {
      var h = location.hash;
      return h === "#de" || h === "#en" ? h.slice(1) : null;
    };

    showLang(
      fromHash() || (/^de\b/i.test(navigator.language || "") ? "de" : "en")
    );

    // Arriving at #de from a link elsewhere is a same-document navigation:
    // nothing reloads and this script never runs again, so the page would
    // sit there in the wrong language. Back and forward land here too.
    window.addEventListener("hashchange", function () {
      var lang = fromHash();
      if (lang) showLang(lang);
    });
  }

  /* ── the film tour ─────────────────────────────────────
     The device is pinned with `position: sticky` and the phone's own
     content is translated in proportion to how far the pinned section
     has travelled. Nothing intercepts the wheel: page scrolling stays
     exactly as the browser does it, which is the difference between
     this reading as expensive and reading as a hijack.

     The CSS unpins the whole thing below 900px and under
     prefers-reduced-motion, so this only runs where it applies.     */

  var tour = document.querySelector("[data-tour]");
  if (!tour) return;

  var track  = tour.querySelector(".tour__track");
  var screen = tour.querySelector("[data-screen]");
  var caps   = Array.prototype.slice.call(tour.querySelectorAll("[data-cap]"));
  var rails  = Array.prototype.slice.call(tour.querySelectorAll("[data-rail] li"));
  var hint   = tour.querySelector("[data-hint]");
  if (!track || !screen || !caps.length) return;

  // Where each claim takes over, as a fraction of the pinned scroll. Tuned
  // against the stitched page so the copy changes as its section reaches the
  // middle of the phone, not as it enters the bottom: poster, then About and
  // Cast and Details, then Your Watch and Screening, then Ratings onward.
  // Re-tune these if the screenshot is ever re-shot at a different length.
  var BANDS = [0, 0.33, 0.62, 0.82];

  var wide = window.matchMedia("(min-width: 901px)");
  var travel = 0;
  var active = -1;
  var ticking = false;

  function measure() {
    // Measured, never hard-coded: the screenshot's real height only
    // settles once it has decoded, and a stale constant either stops the
    // content short or scrolls past its end.
    var frame = screen.parentElement;
    travel = Math.max(0, screen.offsetHeight - frame.clientHeight);
  }

  function paint() {
    ticking = false;

    if (!wide.matches || reduced.matches) {
      screen.style.transform = "";
      return;
    }

    var rect = track.getBoundingClientRect();
    var span = rect.height - window.innerHeight;
    var p = span > 0 ? (-rect.top) / span : 0;
    if (p < 0) p = 0;
    if (p > 1) p = 1;

    screen.style.transform = "translate3d(0," + (-p * travel).toFixed(1) + "px,0)";

    var next = 0;
    for (var i = 0; i < BANDS.length; i++) { if (p >= BANDS[i]) next = i; }
    if (next !== active) {
      active = next;
      caps.forEach(function (el, i) { el.classList.toggle("is-on", i === active); });
      rails.forEach(function (el, i) { el.classList.toggle("is-on", i === active); });
    }
    if (hint) hint.style.opacity = p > 0.02 ? "0" : "1";
  }

  function request() {
    if (!ticking) { ticking = true; window.requestAnimationFrame(paint); }
  }

  function remeasure() { measure(); paint(); }

  remeasure();
  window.addEventListener("scroll", request, { passive: true });
  window.addEventListener("resize", remeasure);
  if (typeof ResizeObserver === "function") new ResizeObserver(remeasure).observe(screen);

  Array.prototype.forEach.call(screen.querySelectorAll("img"), function (img) {
    if (!img.complete) img.addEventListener("load", remeasure, { once: true });
  });

  // Both media queries can flip without a resize event (a rotated phone
  // reports one; a changed accessibility setting does not).
  ["addEventListener", "addListener"].some(function (m) {
    if (typeof wide[m] !== "function") return false;
    wide[m]("change", remeasure);
    reduced[m]("change", remeasure);
    return true;
  });
})();
