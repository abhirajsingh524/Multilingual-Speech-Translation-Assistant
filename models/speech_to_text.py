"""
models/speech_to_text.py
Speech-to-text pipeline — memory-optimised for ≤512 MB environments.

Fallback chain:
  1. Groq Whisper-large-v3 API  →  zero local RAM, fast, accurate
  2. Local whisper-tiny          →  74 MB, loaded + unloaded per request

When does fallback trigger?
  - GROQ_API_KEY not set
  - Groq rate limit hit (429 / RateLimitError)
  - Groq network timeout or any other API error
  - Groq returns empty text

The fallback is transparent to the caller — speech_to_text() always returns
either a transcribed string or an "Error: ..." string.
"""
import os
import gc
import shutil
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Groq API path
# ─────────────────────────────────────────────────────────────────────────────

class _GroqRateLimited(Exception):
    """Raised specifically when Groq returns a 429 / rate-limit response."""


def _transcribe_via_groq(audio_path: str) -> str:
    """
    Transcribe using Groq's hosted Whisper-large-v3.
    Raises _GroqRateLimited when the free-tier quota is exhausted.
    Raises any other exception on network / auth failures.
    """
    from groq import Groq
    from groq import RateLimitError as GroqRateLimitError

    client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

    try:
        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                file=(os.path.basename(audio_path), f),
                model="whisper-large-v3",
                response_format="text",
            )
    except GroqRateLimitError as e:
        # Re-raise as our own type so the caller can log it distinctly
        raise _GroqRateLimited(str(e)) from e

    text = response if isinstance(response, str) else getattr(response, "text", "")
    return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Local whisper-tiny fallback
# ─────────────────────────────────────────────────────────────────────────────

def _check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _transcribe_local_tiny(audio_path: str) -> str:
    """
    Load whisper-tiny (≈74 MB), transcribe once, then immediately unload.
    Model is NEVER kept in memory between requests.

    Memory profile:
      - Load:       +74 MB
      - Transcribe: +~30 MB peak
      - After del + gc.collect(): back to baseline
    """
    import whisper

    if not _check_ffmpeg():
        raise RuntimeError(
            "ffmpeg is not installed or not on PATH. "
            "Install: choco install ffmpeg (Windows) | "
            "apt install ffmpeg (Linux) | brew install ffmpeg (macOS)"
        )

    logger.info("[Whisper-tiny] Loading model for single-use transcription…")
    model = whisper.load_model("tiny")
    try:
        result = model.transcribe(audio_path, fp16=False)
        text = result.get("text", "").strip()
    finally:
        # Critical: unload immediately — do NOT cache the model
        del model
        gc.collect()
        logger.info("[Whisper-tiny] Model unloaded, memory freed.")

    return text


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def speech_to_text(audio_path: str) -> str:
    """
    Transcribe audio at audio_path.

    Returns:
        Transcribed text string on success.
        "Error: <reason>" string on failure (never raises).

    Fallback behaviour when Groq API is unavailable:
    ┌─────────────────────────────────────────────────────────────┐
    │  Condition                  │  What happens                 │
    ├─────────────────────────────┼───────────────────────────────┤
    │  No GROQ_API_KEY            │  Skip API, use whisper-tiny   │
    │  Groq rate limit (429)      │  Log warning, use whisper-tiny│
    │  Groq network error         │  Log warning, use whisper-tiny│
    │  Groq auth error            │  Log warning, use whisper-tiny│
    │  whisper-tiny + no ffmpeg   │  Return "Error: ffmpeg …"     │
    │  whisper-tiny model error   │  Return "Error: <detail>"     │
    └─────────────────────────────┴───────────────────────────────┘
    """
    audio_path = os.path.abspath(audio_path)

    if not os.path.exists(audio_path):
        return f"Error: File not found → {audio_path}"

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    used_fallback = False
    fallback_reason = ""

    # ── Attempt 1: Groq API ───────────────────────────────────────────────────
    if groq_key:
        try:
            logger.info("[STT] Attempting Groq Whisper-large-v3 API…")
            text = _transcribe_via_groq(audio_path)

            if text:
                logger.info("[STT] Groq transcription succeeded.")
                return text

            # Groq returned empty — treat as soft failure
            logger.warning("[STT] Groq returned empty text — falling back to whisper-tiny.")
            used_fallback = True
            fallback_reason = "Groq returned empty transcription"

        except _GroqRateLimited as e:
            # Free-tier quota exhausted — this is the most common production case
            logger.warning(
                "[STT] Groq rate limit reached — falling back to local whisper-tiny. "
                "Detail: %s", e
            )
            used_fallback = True
            fallback_reason = "Groq API rate limit reached"

        except Exception as e:
            logger.warning(
                "[STT] Groq API unavailable (%s: %s) — falling back to local whisper-tiny.",
                type(e).__name__, e
            )
            used_fallback = True
            fallback_reason = f"Groq API error ({type(e).__name__})"
    else:
        logger.info("[STT] GROQ_API_KEY not set — using local whisper-tiny directly.")
        used_fallback = True
        fallback_reason = "No GROQ_API_KEY configured"

    # ── Attempt 2: Local whisper-tiny ─────────────────────────────────────────
    if used_fallback:
        logger.info("[STT] Fallback reason: %s. Starting local whisper-tiny…", fallback_reason)

    try:
        text = _transcribe_local_tiny(audio_path)
        if not text:
            return "Error: No speech detected in the audio file."
        return text

    except RuntimeError as e:
        # ffmpeg missing — actionable error
        logger.error("[STT] whisper-tiny failed (RuntimeError): %s", e)
        return f"Error: {e}"

    except Exception as e:
        logger.error("[STT] whisper-tiny failed (%s): %s", type(e).__name__, e)
        return (
            f"Error: Speech transcription failed. "
            f"Groq API: {fallback_reason}. "
            f"Local fallback: {type(e).__name__}: {e}"
        )
