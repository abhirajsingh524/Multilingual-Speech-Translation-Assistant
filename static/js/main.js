/* =============================================================================
   MSTA — main.js
   Global micro-interactions and UI utilities
   ============================================================================= */

'use strict';

/* ── Theme toggle (light/dark) ───────────────────────────────────────────── */
const THEME_KEY = 'msta-theme';
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.querySelector('.theme-toggle-icon');

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  if (themeIcon) themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

const savedTheme = localStorage.getItem(THEME_KEY);
if (savedTheme) applyTheme(savedTheme);

if (themeToggle) {
  themeToggle.addEventListener('click', function () {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    applyTheme(next);
    localStorage.setItem(THEME_KEY, next);
  });
}

/* ── Audio file name display ─────────────────────────────────────────────── */
const audioInput = document.getElementById('audio-input');
if (audioInput) {
  audioInput.addEventListener('change', function () {
    const label = document.getElementById('file-name');
    const hint  = document.getElementById('audio-hint');
    if (!label) return;

    if (this.files.length) {
      const file = this.files[0];
      label.textContent = file.name;
      // Show file size
      if (hint) {
        const mb = (file.size / 1024 / 1024).toFixed(1);
        hint.textContent = mb + ' MB';
      }
      // Visual feedback on the upload zone
      const zone = label.closest('.file-upload-label');
      if (zone) {
        zone.style.borderColor = 'var(--brand-400)';
        zone.style.background  = 'var(--brand-50)';
      }
    } else {
      label.textContent = 'Choose audio file';
      if (hint) hint.textContent = 'MP3, WAV, M4A, OGG · max 25 MB';
      const zone = label.closest('.file-upload-label');
      if (zone) { zone.style.borderColor = ''; zone.style.background = ''; }
    }
  });
}

/* ── Language swap button ────────────────────────────────────────────────── */
const swapBtn = document.getElementById('swap-btn');
if (swapBtn) {
  swapBtn.addEventListener('click', function () {
    const src = document.getElementById('source_lang');
    const tgt = document.getElementById('target_lang');
    if (!src || !tgt) return;

    const tmp = src.value;
    src.value = tgt.value;
    tgt.value = tmp;

    // Micro-interaction: brief scale pulse on selects
    [src, tgt].forEach(el => {
      el.style.transition = 'transform 150ms ease';
      el.style.transform  = 'scale(1.02)';
      setTimeout(() => { el.style.transform = ''; }, 150);
    });
  });
}

/* ── Auto-dismiss toast messages after 5 s ───────────────────────────────── */
document.querySelectorAll('.flash').forEach(function (el) {
  const DELAY   = 5000;
  const FADE_MS = 300;

  const timer = setTimeout(function () {
    el.style.transition = 'opacity ' + FADE_MS + 'ms ease, transform ' + FADE_MS + 'ms ease';
    el.style.opacity    = '0';
    el.style.transform  = 'translateX(8px)';
    setTimeout(function () { el.remove(); }, FADE_MS);
  }, DELAY);

  // Cancel auto-dismiss if user hovers (they're reading it)
  el.addEventListener('mouseenter', () => clearTimeout(timer));
});
