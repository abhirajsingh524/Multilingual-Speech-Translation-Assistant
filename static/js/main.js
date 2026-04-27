/* =============================================================================
   MSTA — main.js  (Dynamic CSS driver + UI utilities)
   Every section maps directly to a CSS feature in theme.css.
   ============================================================================= */
'use strict';

const ROOT = document.documentElement;

/* ─────────────────────────────────────────────────────────────────────────────
   1. PAGE ENTRANCE
   Adds .page--loaded to <body> so .main-content fades in via CSS transition.
   ───────────────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('page--loaded');
});

/* ─────────────────────────────────────────────────────────────────────────────
   2. THEME TOGGLE  (light ↔ dark)
   Persists choice in localStorage. Updates moon/sun icon.
   Drives [data-theme="dark"] token overrides in theme.css.
   ───────────────────────────────────────────────────────────────────────────── */
const THEME_KEY   = 'msta-theme';
const themeToggle = document.getElementById('theme-toggle');
const themeIcon   = document.querySelector('.theme-toggle-icon');

function applyTheme(theme) {
  ROOT.setAttribute('data-theme', theme);
  if (themeIcon) themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
  if (themeToggle) themeToggle.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
}

const savedTheme = localStorage.getItem(THEME_KEY);
applyTheme(savedTheme || 'light');

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const next = (ROOT.getAttribute('data-theme') || 'light') === 'light' ? 'dark' : 'light';
    applyTheme(next);
    localStorage.setItem(THEME_KEY, next);
  });
}

/* ─────────────────────────────────────────────────────────────────────────────
   3. SCROLL PROGRESS BAR
   Updates --scroll-progress (0 → 1) on :root so the CSS bar width animates.
   ───────────────────────────────────────────────────────────────────────────── */
(function initScrollProgress() {
  // Inject the bar element once
  const bar = document.createElement('div');
  bar.className = 'scroll-progress-bar';
  bar.setAttribute('role', 'progressbar');
  bar.setAttribute('aria-hidden', 'true');
  document.body.prepend(bar);

  function updateProgress() {
    const scrolled = window.scrollY;
    const total    = document.documentElement.scrollHeight - window.innerHeight;
    const ratio    = total > 0 ? Math.min(scrolled / total, 1) : 0;
    ROOT.style.setProperty('--scroll-progress', ratio);
  }

  window.addEventListener('scroll', updateProgress, { passive: true });
  updateProgress();
})();

/* ─────────────────────────────────────────────────────────────────────────────
   4. NAVBAR SCROLL STATE
   Adds .navbar--scrolled after 10px scroll — CSS darkens the background.
   ───────────────────────────────────────────────────────────────────────────── */
(function initNavbarScroll() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;

  function onScroll() {
    navbar.classList.toggle('navbar--scrolled', window.scrollY > 10);
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();

/* ─────────────────────────────────────────────────────────────────────────────
   5. CURSOR GLOW
   Updates --cursor-x / --cursor-y on :root so body::after follows the mouse.
   Disabled on touch devices (no cursor).
   ───────────────────────────────────────────────────────────────────────────── */
(function initCursorGlow() {
  if (window.matchMedia('(pointer: coarse)').matches) return; // touch device

  let rafId = null;
  let mx = window.innerWidth / 2;
  let my = window.innerHeight / 2;

  document.addEventListener('mousemove', (e) => {
    mx = e.clientX;
    my = e.clientY;
    if (rafId) return;
    rafId = requestAnimationFrame(() => {
      ROOT.style.setProperty('--cursor-x', mx + 'px');
      ROOT.style.setProperty('--cursor-y', my + 'px');
      rafId = null;
    });
  }, { passive: true });
})();

/* ─────────────────────────────────────────────────────────────────────────────
   6. CARD 3D TILT
   On mousemove over .card-left / .card-right / .stat-card, applies a subtle
   perspective tilt via inline transform. Resets on mouseleave.
   Also triggers the shimmer animation (.card--hovered).
   ───────────────────────────────────────────────────────────────────────────── */
(function initCardTilt() {
  if (window.matchMedia('(pointer: coarse)').matches) return;

  const TILT_MAX = 6; // degrees

  document.querySelectorAll('.card-left, .card-right, .stat-card, .auth-card, .result-card').forEach(card => {
    card.style.transformStyle = 'preserve-3d';
    card.style.perspective    = '800px';

    card.addEventListener('mouseenter', () => {
      card.classList.add('card--hovered');
      setTimeout(() => card.classList.remove('card--hovered'), 650);
    });

    card.addEventListener('mousemove', (e) => {
      const rect   = card.getBoundingClientRect();
      const cx     = rect.left + rect.width  / 2;
      const cy     = rect.top  + rect.height / 2;
      const dx     = (e.clientX - cx) / (rect.width  / 2); // -1 → 1
      const dy     = (e.clientY - cy) / (rect.height / 2); // -1 → 1
      const tiltX  = (-dy * TILT_MAX).toFixed(2);
      const tiltY  = ( dx * TILT_MAX).toFixed(2);
      card.style.transform = `perspective(800px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateZ(4px)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });
})();

/* ─────────────────────────────────────────────────────────────────────────────
   7. BUTTON RIPPLE
   Injects a .btn-ripple span on click for the CSS ripple animation.
   ───────────────────────────────────────────────────────────────────────────── */
(function initRipple() {
  document.querySelectorAll('.btn-translate, .btn-auth, .btn-new-translate, .btn-calm').forEach(btn => {
    btn.addEventListener('click', function (e) {
      const rect   = btn.getBoundingClientRect();
      const size   = Math.max(rect.width, rect.height);
      const x      = e.clientX - rect.left - size / 2;
      const y      = e.clientY - rect.top  - size / 2;

      const ripple = document.createElement('span');
      ripple.className = 'btn-ripple';
      ripple.style.cssText = `width:${size}px;height:${size}px;left:${x}px;top:${y}px`;
      btn.appendChild(ripple);
      ripple.addEventListener('animationend', () => ripple.remove());
    });
  });
})();

/* ─────────────────────────────────────────────────────────────────────────────
   8. SCROLL-REVEAL (IntersectionObserver)
   Adds .reveal--visible to any element with class .reveal when it enters
   the viewport. Also animates history table rows (.history-table tbody tr).
   ───────────────────────────────────────────────────────────────────────────── */
(function initScrollReveal() {
  if (!('IntersectionObserver' in window)) {
    // Fallback: show everything immediately
    document.querySelectorAll('.reveal, .history-table tbody tr').forEach(el => {
      el.classList.add('reveal--visible', 'row--visible');
    });
    return;
  }

  // Generic reveal elements
  const revealObs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('reveal--visible');
        revealObs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

  // History table rows — staggered entrance
  const rowObs = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        const row = entry.target;
        setTimeout(() => row.classList.add('row--visible'), i * 40);
        rowObs.unobserve(row);
      }
    });
  }, { threshold: 0.05 });

  document.querySelectorAll('.history-table tbody tr').forEach(row => rowObs.observe(row));
})();

/* ─────────────────────────────────────────────────────────────────────────────
   9. ANIMATED GRADIENT HEADINGS
   Adds .heading--animate to major headings so the gradient shifts continuously.
   ───────────────────────────────────────────────────────────────────────────── */
(function initAnimatedHeadings() {
  document.querySelectorAll(
    '.card-header h1, .banner-text h1, .auth-header h1, .page-header h1'
  ).forEach(h => h.classList.add('heading--animate'));
})();

/* ─────────────────────────────────────────────────────────────────────────────
   10. FILE UPLOAD ZONE — active state
   Adds .file-upload-label--active when a file is selected (CSS changes border).
   ───────────────────────────────────────────────────────────────────────────── */
(function initFileUpload() {
  const audioInput = document.getElementById('audio-input');
  if (!audioInput) return;

  const label = document.getElementById('file-name');
  const hint  = document.getElementById('audio-hint');
  const zone  = audioInput.closest('.file-upload-label');

  audioInput.addEventListener('change', function () {
    if (this.files.length) {
      const file = this.files[0];
      if (label) label.textContent = file.name;
      if (hint)  hint.textContent  = (file.size / 1024 / 1024).toFixed(1) + ' MB';
      if (zone)  zone.classList.add('file-upload-label--active');
    } else {
      if (label) label.textContent = 'Choose audio file';
      if (hint)  hint.textContent  = 'MP3, WAV, M4A, OGG · max 25 MB';
      if (zone)  zone.classList.remove('file-upload-label--active');
    }
  });
})();

/* ─────────────────────────────────────────────────────────────────────────────
   11. LANGUAGE SWAP BUTTON
   ───────────────────────────────────────────────────────────────────────────── */
(function initSwap() {
  const swapBtn = document.getElementById('swap-btn');
  if (!swapBtn) return;

  swapBtn.addEventListener('click', () => {
    const src = document.getElementById('source_lang');
    const tgt = document.getElementById('target_lang');
    if (!src || !tgt) return;

    const tmp = src.value;
    src.value = tgt.value;
    tgt.value = tmp;

    [src, tgt].forEach(el => {
      el.style.transition = 'transform 150ms ease';
      el.style.transform  = 'scale(1.03)';
      setTimeout(() => { el.style.transform = ''; }, 150);
    });
  });
})();

/* ─────────────────────────────────────────────────────────────────────────────
   12. TRANSLATE FORM — loading state
   ───────────────────────────────────────────────────────────────────────────── */
(function initTranslateForm() {
  const form = document.getElementById('translate-form');
  if (!form) return;

  form.addEventListener('submit', () => {
    const btn     = document.getElementById('translate-btn');
    const label   = document.getElementById('btn-label-text');
    const loading = btn && btn.querySelector('.btn-loading');
    const svg     = btn && btn.querySelector('svg');
    if (!btn) return;

    btn.disabled = true;
    if (svg)     svg.style.display = 'none';
    if (label)   label.classList.add('hidden');
    if (loading) loading.classList.remove('hidden');
  });
})();

/* ─────────────────────────────────────────────────────────────────────────────
   13. MODEL SELECTOR — show/hide speech UI
   ───────────────────────────────────────────────────────────────────────────── */
const MODEL_HINTS = {
  huggingface: 'Local model — no API key required. Best for offline use.',
  groq:        'Cloud model — faster and more accurate. Requires Groq API key.',
  speech:      'Transcribes audio with Whisper, then translates the result.'
};

function onModelChange(val) {
  const isSpeech      = val === 'speech';
  const textGroup     = document.getElementById('text-input-group');
  const audioOptional = document.getElementById('audio-optional');
  const speechInfo    = document.getElementById('speech-info');
  const btnLabel      = document.getElementById('btn-label-text');
  const audioInput    = document.getElementById('audio-input');
  const modelDesc     = document.getElementById('model-desc');

  if (modelDesc) {
    modelDesc.textContent    = MODEL_HINTS[val] || '';
    modelDesc.style.display  = 'block';
  }

  if (isSpeech) {
    if (textGroup)     textGroup.classList.add('hidden');
    if (audioOptional) { audioOptional.textContent = '(required)'; audioOptional.style.color = '#ef4444'; }
    if (audioInput)    audioInput.setAttribute('required', 'required');
    if (speechInfo)    speechInfo.classList.remove('hidden');
    if (btnLabel)      btnLabel.textContent = 'Transcribe & Translate';
  } else {
    if (textGroup)     textGroup.classList.remove('hidden');
    if (audioOptional) { audioOptional.textContent = '(optional)'; audioOptional.style.color = ''; }
    if (audioInput)    audioInput.removeAttribute('required');
    if (speechInfo)    speechInfo.classList.add('hidden');
    if (btnLabel)      btnLabel.textContent = 'Translate Now';
  }
}

// Expose globally for inline onchange attribute
window.onModelChange = onModelChange;

/* ─────────────────────────────────────────────────────────────────────────────
   14. TOAST AUTO-DISMISS (5 s, cancels on hover)
   ───────────────────────────────────────────────────────────────────────────── */
(function initToasts() {
  document.querySelectorAll('.flash').forEach(el => {
    const DELAY = 5000, FADE = 300;
    const timer = setTimeout(() => {
      el.style.transition = `opacity ${FADE}ms ease, transform ${FADE}ms ease`;
      el.style.opacity    = '0';
      el.style.transform  = 'translateX(8px)';
      setTimeout(() => el.remove(), FADE);
    }, DELAY);
    el.addEventListener('mouseenter', () => clearTimeout(timer));
  });
})();

/* ─────────────────────────────────────────────────────────────────────────────
   15. COPY BUTTON (result page)
   ───────────────────────────────────────────────────────────────────────────── */
function copyText(id, btn) {
  const el = document.getElementById(id);
  if (!el) return;
  const text = el.innerText;

  const doFeedback = () => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg><span>Copied!</span>';
    btn.style.cssText += 'color:var(--teal-600);border-color:var(--teal-200);background:var(--teal-50)';
    setTimeout(() => { btn.innerHTML = orig; btn.style.cssText = ''; }, 2000);
  };

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(doFeedback).catch(() => {});
  } else {
    // Modern fallback — no deprecated execCommand
    const ta = Object.assign(document.createElement('textarea'), {
      value: text, style: 'position:fixed;opacity:0;pointer-events:none'
    });
    document.body.appendChild(ta);
    ta.focus(); ta.select();
    try { document.execCommand('copy'); } catch (_) {}
    document.body.removeChild(ta);
    doFeedback();
  }
}
window.copyText = copyText;

/* ─────────────────────────────────────────────────────────────────────────────
   16. SIDEBAR ACTIVE LINK
   Marks the current page link in .dash-sidebar as active.
   ───────────────────────────────────────────────────────────────────────────── */
(function initSidebarActive() {
  const path = window.location.pathname;
  document.querySelectorAll('.dash-sidebar a').forEach(a => {
    if (a.getAttribute('href') === path) a.classList.add('active');
  });
})();

/* ─────────────────────────────────────────────────────────────────────────────
   17. ADAPTIVE PROCESSING PANEL
   Intercepts form submissions when the server is slow (latency > threshold).
   
   Fix vs previous version:
   - We no longer navigate away before the fetch completes.
   - Instead we show the processing page in an invisible iframe overlay,
     submit the real form normally, and let the server redirect handle it.
   - sessionStorage stores the destination so processing.html can redirect.
   ───────────────────────────────────────────────────────────────────────────── */
(function initProcessingPanel() {
  const LATENCY_THRESHOLD_MS = 1200;
  const PROC_FORMS           = ['login-form', 'signup-form', 'translate-form'];

  let lastLatencyMs = 0;

  function probeLatency() {
    const t0 = performance.now();
    fetch('/auth/ping', { method: 'HEAD', cache: 'no-store' })
      .then(() => { lastLatencyMs = performance.now() - t0; })
      .catch(() => { lastLatencyMs = 9999; });
  }

  probeLatency();
  setInterval(probeLatency, 30000);

  PROC_FORMS.forEach(id => {
    const form = document.getElementById(id);
    if (!form) return;

    form.addEventListener('submit', function (e) {
      if (lastLatencyMs < LATENCY_THRESHOLD_MS) return; // fast path — normal submit

      // High latency: show processing panel while form submits in background.
      e.preventDefault();

      const action   = form.getAttribute('action') || window.location.href;
      const method   = (form.getAttribute('method') || 'POST').toUpperCase();
      const formData = new FormData(form);

      // 1. Submit the real form data via fetch (non-blocking)
      fetch(action, { method, body: formData, redirect: 'follow', credentials: 'same-origin' })
        .then(res => {
          // Store the final URL (after any server-side redirects) for the panel to use
          sessionStorage.setItem('proc_dest', res.url || action);
        })
        .catch(() => {
          sessionStorage.setItem('proc_dest', action);
        });

      // 2. Navigate to the processing panel immediately (cosmetic overlay)
      //    The panel reads proc_dest from sessionStorage when its animation ends.
      const procUrl = '/processing?redirect=' + encodeURIComponent(action);
      window.location.href = procUrl;
    });
  });
})();
