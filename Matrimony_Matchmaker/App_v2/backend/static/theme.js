/* =========================================================================
 * static/theme.js — Modern Light / Dark theme for Shubh Vivah Matchmaker
 * =========================================================================
 *
 * PURPOSE
 *   This file switches the app between light mode and dark mode using the
 *   same CSS variables your templates already use:
 *
 *     --card
 *     --cream
 *     --ink
 *     --muted
 *     --line
 *     --maroon
 *     --maroon-dk
 *     --rose
 *     --rose-soft
 *     --gold
 *     --gold-soft
 *     --green
 *     --success
 *
 *   It injects a floating theme toggle button and stores the user choice
 *   in localStorage.
 *
 * NOTE
 *   This version keeps the existing details-modal fix intact.
 *   Only the dark-mode colors inside the match cards / match widgets are fixed.
 * ========================================================================= */

(function () {
  "use strict";

  var STORAGE_KEY = "sv-theme";

  var CSS = `
    /* =========================================================
       LIGHT THEME
       ========================================================= */
    :root[data-theme="light"] {
      --cream: #f4f6fb;
      --card: #ffffff;
      --ink: #1c2230;
      --muted: #6b7488;
      --line: #e7eaf2;

      --maroon: #4f46e5;
      --maroon-dk: #4338ca;

      --rose: #7c5cff;
      --rose-soft: #eef0ff;

      --gold: #0ea5a4;
      --gold-soft: #d6f5f3;

      --green: #16a34a;
      --success: #16a34a;

      color-scheme: light;
    }

    /* =========================================================
       DARK THEME
       ========================================================= */
    :root[data-theme="dark"] {
      --cream: #0e1118;
      --card: #171b27;
      --ink: #e8ebf5;
      --muted: #9aa3b8;
      --line: #2a3142;

      --maroon: #8b8fff;
      --maroon-dk: #7378ff;

      --rose: #b39aff;
      --rose-soft: rgba(139, 143, 255, 0.15);

      --gold: #2dd4bf;
      --gold-soft: rgba(45, 212, 191, 0.16);

      --green: #34d399;
      --success: #34d399;

      color-scheme: dark;
    }

    /* =========================================================
       GENERAL DARK MODE SUPPORT
       ========================================================= */
    [data-theme="dark"] body {
      background: var(--cream);
      color: var(--ink);
    }

    [data-theme="dark"] input,
    [data-theme="dark"] select,
    [data-theme="dark"] textarea,
    [data-theme="dark"] .pan-input {
      background: #10141d !important;
      color: var(--ink) !important;
      border-color: var(--line) !important;
    }

    [data-theme="dark"] input::placeholder,
    [data-theme="dark"] textarea::placeholder {
      color: #6d7688;
    }

    [data-theme="dark"] select option {
      background: #171b27;
      color: var(--ink);
    }

    /* Elements previously using hard-coded light colors */
    [data-theme="dark"] .popup,
    [data-theme="dark"] .chip,
    [data-theme="dark"] .conv,
    [data-theme="dark"] .bubble,
    [data-theme="dark"] .msg {
      background: var(--card);
      color: var(--ink);
    }

    [data-theme="dark"] .chip.verified {
      background: rgba(52, 211, 153, 0.14);
      color: #34d399;
      border-color: rgba(52, 211, 153, 0.40);
    }

    [data-theme="dark"] .chip.unverified {
      background: rgba(245, 158, 11, 0.14);
      color: #fbbf24;
      border-color: rgba(245, 158, 11, 0.40);
    }

    /* =========================================================
       DETAILS MODAL / PROFILE POPUP — KEEP AS WORKING
       ========================================================= */
    [data-theme="dark"] .modal,
    [data-theme="dark"] .modal-content,
    [data-theme="dark"] .details-modal,
    [data-theme="dark"] .profile-modal,
    [data-theme="dark"] .popup.profile-popup,
    [data-theme="dark"] .profile-popup {
      background: #111827 !important;
      color: var(--ink) !important;
      border: 1px solid #374151 !important;
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45) !important;
    }

    [data-theme="dark"] .modal h1,
    [data-theme="dark"] .modal h2,
    [data-theme="dark"] .modal h3,
    [data-theme="dark"] .modal-content h1,
    [data-theme="dark"] .modal-content h2,
    [data-theme="dark"] .modal-content h3,
    [data-theme="dark"] .details-modal h1,
    [data-theme="dark"] .details-modal h2,
    [data-theme="dark"] .details-modal h3,
    [data-theme="dark"] .profile-modal h1,
    [data-theme="dark"] .profile-modal h2,
    [data-theme="dark"] .profile-modal h3,
    [data-theme="dark"] .profile-popup h1,
    [data-theme="dark"] .profile-popup h2,
    [data-theme="dark"] .profile-popup h3 {
      color: #a5b4fc !important;
    }

    [data-theme="dark"] .modal p,
    [data-theme="dark"] .modal span,
    [data-theme="dark"] .modal div,
    [data-theme="dark"] .modal label,
    [data-theme="dark"] .modal strong,
    [data-theme="dark"] .modal-content p,
    [data-theme="dark"] .modal-content span,
    [data-theme="dark"] .modal-content div,
    [data-theme="dark"] .modal-content label,
    [data-theme="dark"] .modal-content strong,
    [data-theme="dark"] .details-modal p,
    [data-theme="dark"] .details-modal span,
    [data-theme="dark"] .details-modal div,
    [data-theme="dark"] .details-modal label,
    [data-theme="dark"] .details-modal strong,
    [data-theme="dark"] .profile-modal p,
    [data-theme="dark"] .profile-modal span,
    [data-theme="dark"] .profile-modal div,
    [data-theme="dark"] .profile-modal label,
    [data-theme="dark"] .profile-modal strong,
    [data-theme="dark"] .profile-popup p,
    [data-theme="dark"] .profile-popup span,
    [data-theme="dark"] .profile-popup div,
    [data-theme="dark"] .profile-popup label,
    [data-theme="dark"] .profile-popup strong {
      color: var(--ink) !important;
    }

    [data-theme="dark"] .profile-card {
      background: #1b2231 !important;
      color: var(--ink) !important;
      border: 1px solid #374151 !important;
      box-shadow: none !important;
    }

    [data-theme="dark"] .profile-card h3 {
      color: #a5b4fc !important;
    }

    [data-theme="dark"] #profileDetails,
    [data-theme="dark"] #profileDetails *,
    [data-theme="dark"] #preferenceDetails,
    [data-theme="dark"] #preferenceDetails * {
      color: var(--ink) !important;
    }

    [data-theme="dark"] .close,
    [data-theme="dark"] .close-btn,
    [data-theme="dark"] .modal-close,
    [data-theme="dark"] .details-close {
      color: #cbd5e1 !important;
    }

    /* =========================================================
       MATCH LIST / MATCH CARDS — FIX ONLY THESE TEXT COLORS
       ========================================================= */

    /* Outer match cards stay dark */
    [data-theme="dark"] .match-card,
    [data-theme="dark"] .match-item,
    [data-theme="dark"] .candidate-card,
    [data-theme="dark"] .profile-tile,
    [data-theme="dark"] .recommendation-card {
      background: #151b2a !important;
      color: var(--ink) !important;
      border-color: #263149 !important;
    }

    /* Name / title text on dark card */
    [data-theme="dark"] .match-card h2,
    [data-theme="dark"] .match-card h3,
    [data-theme="dark"] .match-card h4,
    [data-theme="dark"] .match-item h2,
    [data-theme="dark"] .match-item h3,
    [data-theme="dark"] .match-item h4,
    [data-theme="dark"] .candidate-card h2,
    [data-theme="dark"] .candidate-card h3,
    [data-theme="dark"] .candidate-card h4,
    [data-theme="dark"] .profile-tile h2,
    [data-theme="dark"] .profile-tile h3,
    [data-theme="dark"] .profile-tile h4,
    [data-theme="dark"] .recommendation-card h2,
    [data-theme="dark"] .recommendation-card h3,
    [data-theme="dark"] .recommendation-card h4 {
      color: #f3f4f6 !important;
    }

    /* Only normal text on the dark card — NOT every nested div */
    [data-theme="dark"] .match-card p,
    [data-theme="dark"] .match-card span,
    [data-theme="dark"] .match-item p,
    [data-theme="dark"] .match-item span,
    [data-theme="dark"] .candidate-card p,
    [data-theme="dark"] .candidate-card span,
    [data-theme="dark"] .profile-tile p,
    [data-theme="dark"] .profile-tile span,
    [data-theme="dark"] .recommendation-card p,
    [data-theme="dark"] .recommendation-card span {
      color: var(--ink) !important;
    }

    /* Softer metadata */
    [data-theme="dark"] .match-meta,
    [data-theme="dark"] .match-location,
    [data-theme="dark"] .match-subtitle,
    [data-theme="dark"] .candidate-meta,
    [data-theme="dark"] .profile-subtext {
      color: var(--muted) !important;
    }

    /* ---------------------------------------------------------
       LIGHT SCORE / MATCH BOXES INSIDE DARK MATCH CARDS
       This is the actual fix for the white-on-light problem.
       --------------------------------------------------------- */
    [data-theme="dark"] .score-box,
    [data-theme="dark"] .metric-box,
    [data-theme="dark"] .stat-box,
    [data-theme="dark"] .match-score-box,
    [data-theme="dark"] .compat-box,
    [data-theme="dark"] .match-stat,
    [data-theme="dark"] .score-card {
      background: #f3ece8 !important;
      color: #4b5563 !important;
      border-color: #e4d8d1 !important;
    }

    /* Make sure ALL text inside those light widgets becomes dark */
    [data-theme="dark"] .score-box *,
    [data-theme="dark"] .metric-box *,
    [data-theme="dark"] .stat-box *,
    [data-theme="dark"] .match-score-box *,
    [data-theme="dark"] .compat-box *,
    [data-theme="dark"] .match-stat *,
    [data-theme="dark"] .score-card * {
      color: #4b5563 !important;
    }

    /* Labels inside those widgets */
    [data-theme="dark"] .score-box h4,
    [data-theme="dark"] .score-box .label,
    [data-theme="dark"] .metric-box h4,
    [data-theme="dark"] .metric-box .label,
    [data-theme="dark"] .stat-box h4,
    [data-theme="dark"] .stat-box .label,
    [data-theme="dark"] .match-score-box h4,
    [data-theme="dark"] .match-score-box .label,
    [data-theme="dark"] .compat-box h4,
    [data-theme="dark"] .compat-box .label,
    [data-theme="dark"] .match-stat h4,
    [data-theme="dark"] .match-stat .label,
    [data-theme="dark"] .score-card h4,
    [data-theme="dark"] .score-card .label {
      color: #7b7b86 !important;
    }

    /* Numeric values remain accent-colored */
    [data-theme="dark"] .score-box .value,
    [data-theme="dark"] .metric-box .value,
    [data-theme="dark"] .stat-box .value,
    [data-theme="dark"] .match-score-box .value,
    [data-theme="dark"] .compat-box .value,
    [data-theme="dark"] .match-stat .value,
    [data-theme="dark"] .score-card .value {
      color: #7c5cff !important;
    }

    /* Secondary/light buttons inside match cards */
    [data-theme="dark"] .match-card .btn-light,
    [data-theme="dark"] .match-card .btn-secondary,
    [data-theme="dark"] .match-card .details-btn,
    [data-theme="dark"] .match-card button.secondary,
    [data-theme="dark"] .match-item .btn-light,
    [data-theme="dark"] .match-item .btn-secondary,
    [data-theme="dark"] .candidate-card .btn-light,
    [data-theme="dark"] .candidate-card .btn-secondary {
      color: #6366f1 !important;
    }

    /* =========================================================
       FLOATING TOGGLE BUTTON
       ========================================================= */
    #sv-theme-toggle {
      position: fixed;
      right: 18px;
      bottom: 18px;
      z-index: 2147483000;
      width: 48px;
      height: 48px;
      border-radius: 50%;
      border: 1px solid var(--line);
      background: var(--card);
      color: var(--ink);
      font-size: 20px;
      line-height: 1;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 10px 28px -10px rgba(0, 0, 0, 0.45);
      transition: transform 0.25s ease, background 0.25s ease;
    }

    #sv-theme-toggle:hover {
      transform: translateY(-3px) scale(1.05);
    }

    #sv-theme-toggle:active {
      transform: scale(0.94);
    }

    @media print {
      #sv-theme-toggle {
        display: none;
      }
    }
  `;

  function injectStyle() {
    if (document.getElementById("sv-theme-style")) return;

    var style = document.createElement("style");
    style.id = "sv-theme-style";
    style.textContent = CSS;
    (document.head || document.documentElement).appendChild(style);
  }

  function currentTheme() {
    var saved = null;

    try {
      saved = localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      saved = null;
    }

    if (saved === "light" || saved === "dark") {
      return saved;
    }

    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }

    return "light";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);

    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {}

    var btn = document.getElementById("sv-theme-toggle");
    if (btn) {
      btn.textContent = theme === "dark" ? "☀️" : "🌙";
      btn.setAttribute(
        "aria-label",
        theme === "dark" ? "Switch to light theme" : "Switch to dark theme"
      );
      btn.title = btn.getAttribute("aria-label");
    }
  }

  function addToggle() {
    if (document.getElementById("sv-theme-toggle")) return;

    var btn = document.createElement("button");
    btn.id = "sv-theme-toggle";
    btn.type = "button";

    btn.onclick = function () {
      var next =
        document.documentElement.getAttribute("data-theme") === "dark"
          ? "light"
          : "dark";

      applyTheme(next);
    };

    document.body.appendChild(btn);
    applyTheme(document.documentElement.getAttribute("data-theme") || currentTheme());
  }

  document.documentElement.setAttribute("data-theme", currentTheme());
  injectStyle();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", addToggle);
  } else {
    addToggle();
  }
})();