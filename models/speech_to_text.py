import os
import logging
import whisper

logger = logging.getLogger(__name__)

# Load once
model = whisper.load_model("base")


def speech_to_text(audio_path: str) -> str:
    try:
        audio_path = os.path.abspath(audio_path)

        logger.info(f"[Whisper] File: {audio_path}")

        if not os.path.exists(audio_path):
            return f"Error: File not found → {audio_path}"

        # ⚡ Faster inference
        result = model.transcribe(audio_path, fp16=False)

        text = result.get("text", "").strip()

        if not text:
            return "Error: No speech detected"

        return text

    except Exception as e:
        logger.error(f"Whisper Error: {str(e)}")
        return f"Error: {str(e)}"