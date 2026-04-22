/* ── MSTA — main.js ──────────────────────────────────────────────────────── */

// ── Audio file name display ───────────────────────────────────────────────
const audioInput = document.getElementById('audio-input');
if (audioInput) {
  audioInput.addEventListener('change', function () {
    const label = document.getElementById('file-name');
    if (label) {
      label.textContent = this.files.length ? this.files[0].name : 'Choose audio file';
    }
  });
}

// ── Language swap button ──────────────────────────────────────────────────
const swapBtn = document.getElementById('swap-btn');
if (swapBtn) {
  swapBtn.addEventListener('click', function () {
    const src = document.getElementById('source_lang');
    const tgt = document.getElementById('target_lang');
    if (src && tgt) {
      const tmp = src.value;
      src.value = tgt.value;
      tgt.value = tmp;
    }
  });
}

// ── Auto-dismiss flash messages after 5 s ────────────────────────────────
document.querySelectorAll('.flash').forEach(function (el) {
  setTimeout(function () {
    el.style.transition = 'opacity .4s';
    el.style.opacity = '0';
    setTimeout(function () { el.remove(); }, 400);
  }, 5000);
});
