import os
import shutil
import logging
import whisper

logger = logging.getLogger(__name__)

# ── Lazy model cache ──────────────────────────────────────────────────────────
# Loading at module-import time blocks Flask startup for 5-15 s on CPU and
# crashes the entire app if the download fails.  Load on first use instead.
_model = None


def _get_model():
    global _model
    if _model is None:
        logger.info("[Whisper] Loading model (base) — first call only…")
        _model = whisper.load_model("base")
        logger.info("[Whisper] Model ready.")
    return _model


def _check_ffmpeg() -> bool:
    """Return True if the ffmpeg binary is available on PATH."""
    return shutil.which("ffmpeg") is not None


def speech_to_text(audio_path: str) -> str:
    try:
        audio_path = os.path.abspath(audio_path)

        logger.info(f"[Whisper] File: {audio_path}")

        if not os.path.exists(audio_path):
            return f"Error: File not found → {audio_path}"

        # Detect missing ffmpeg early and return a clear, actionable message
        # instead of a cryptic FileNotFoundError buried in Whisper internals.
        if not _check_ffmpeg():
            return (
                "Error: ffmpeg is not installed or not on PATH. "
                "Whisper requires ffmpeg to decode audio files. "
                "Install it with: choco install ffmpeg  (Windows) "
                "or: sudo apt install ffmpeg  (Linux/WSL) "
                "or: brew install ffmpeg  (macOS), "
                "then restart the server."
            )

        model = _get_model()

        # fp16=False — required on CPU; GPU builds can set this to True
        result = model.transcribe(audio_path, fp16=False)

        text = result.get("text", "").strip()

        if not text:
            return "Error: No speech detected"

        return text

    except Exception as e:
        logger.error(f"Whisper Error: {str(e)}")
        return f"Error: {str(e)}"