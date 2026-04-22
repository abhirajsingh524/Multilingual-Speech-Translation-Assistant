import os
import logging
import whisper

logger = logging.getLogger(__name__)

# Load Whisper model once at import time (downloads on first run)
# options: tiny, base, small, medium, large
model = whisper.load_model("base")


def speech_to_text(audio_path: str) -> str:
    """
    Transcribe an audio file to text using OpenAI Whisper.

    FIX: always resolve to an absolute path before passing to Whisper.
    Whisper (and ffmpeg underneath it) cannot handle relative paths on
    Windows — they raise "The system cannot find the file specified."
    """
    # Resolve to absolute path — critical fix for Windows
    audio_path = os.path.abspath(audio_path)

    # Guard: confirm the file exists before handing off to Whisper
    if not os.path.exists(audio_path):
        logger.error("speech_to_text: file not found → %s", audio_path)
        return f"Error: file not found at {audio_path}"

    logger.info("speech_to_text: transcribing → %s", audio_path)

    try:
        result = model.transcribe(audio_path)
        text = result.get("text", "").strip()
        logger.info("speech_to_text: extracted %d chars", len(text))
        return text
    except Exception as e:
        logger.error("speech_to_text: Whisper error → %s", e)
        return f"Error: {str(e)}"
