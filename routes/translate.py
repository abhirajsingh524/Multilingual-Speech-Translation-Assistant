"""
Translation blueprint — /translate (POST)
Handles:
- Text translation
- Audio → Text → Translation (Whisper)
- In-memory history storage
"""
# ── imports MUST come first ───────────────────────────────────────────────────
import os
import time
import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from services.history_store import add_entry
from models.groq_translator import groq_translate
from models.translator import translate_text
from models.speech_to_text import speech_to_text

logger = logging.getLogger(__name__)

translate_bp = Blueprint("translate", __name__)

# ── Supported audio formats ───────────────────────────────────────────────────
ALLOWED_AUDIO = {"mp3", "wav", "m4a", "ogg", "flac", "webm"}

# ── Output folder — anchored to this file so the path is always absolute ─────
# BUG FIX: was declared before `import os` AND used a CWD-relative path.
# os.path.dirname(__file__) gives the absolute routes/ directory; go one level
# up with dirname again to reach the project root.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FOLDER = os.path.join(_PROJECT_ROOT, "static", "outputs", "speech")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _allowed_audio(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_AUDIO


def _save_audio(audio_file, upload_folder: str):
    """
    Save uploaded audio to upload_folder (already absolute from app.config).
    Returns (unique_filename, absolute_save_path).
    """
    os.makedirs(upload_folder, exist_ok=True)

    filename    = secure_filename(audio_file.filename)
    unique_name = f"{int(time.time())}_{filename}"

    # upload_folder is already absolute (set in app.py via __file__),
    # but os.path.abspath() is called again as a Windows safety net.
    save_path = os.path.abspath(os.path.join(upload_folder, unique_name))

    audio_file.save(save_path)

    if not os.path.exists(save_path):
        raise FileNotFoundError(f"File not saved correctly: {save_path}")

    logger.info("Audio saved → %s", save_path)
    return unique_name, save_path


# ── Main route ────────────────────────────────────────────────────────────────

@translate_bp.route("/translate", methods=["POST"])
@login_required
def translate():

    text         = request.form.get("text", "").strip()
    source_lang  = request.form.get("source_lang", "en")
    target_lang  = request.form.get("target_lang", "hi")
    model_choice = request.form.get("model_choice", "huggingface")

    audio_filename = None
    extracted_text = None

    # upload_folder is an absolute path set in app.py — safe on Windows
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    # =========================================================================
    # 🎤  SPEECH MODEL  →  audio → text → translate
    # =========================================================================
    if model_choice == "speech":

        audio_file = request.files.get("audio")

        if not audio_file or audio_file.filename == "":
            flash("Please upload an audio file.", "error")
            return redirect(url_for("main.translate_page"))

        if not _allowed_audio(audio_file.filename):
            flash("Invalid format. Allowed: mp3, wav, m4a, ogg, flac, webm", "error")
            return redirect(url_for("main.translate_page"))

        try:
            # Step 1 — save with absolute path
            audio_filename, save_path = _save_audio(audio_file, upload_folder)

            logger.info("Passing to Whisper → %s  exists=%s", save_path, os.path.exists(save_path))

            # Step 2 — speech → text (speech_to_text also calls os.path.abspath internally)
            extracted_text = speech_to_text(save_path)

            if not extracted_text or "Error:" in extracted_text:
                flash(f"Speech error: {extracted_text}", "error")
                return redirect(url_for("main.translate_page"))

            if extracted_text.strip() == "":
                flash("No speech detected in the audio file.", "error")
                return redirect(url_for("main.translate_page"))

            # Step 3 — translate extracted text.
            # The "speech" model_choice covers transcription only; translation
            # always uses the local HuggingFace pipeline here.  If Groq
            # translation is needed after STT, a separate model_choice field
            # for the translation step should be added to the form (P2 backlog).
            translated_text = translate_text(extracted_text, source_lang, target_lang)

            # Step 4 — save plain-text output file (optional, non-blocking)
            try:
                output_filename = f"{int(time.time())}_translated.txt"
                output_path     = os.path.join(OUTPUT_FOLDER, output_filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(f"Original:\n{extracted_text}\n\nTranslated:\n{translated_text}")
                logger.info("Output saved → %s", output_path)
            except Exception as oe:
                logger.warning("Could not save output file: %s", oe)

            text = extracted_text

        except Exception as e:
            logger.error("Speech route error: %s", e)
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("main.translate_page"))

    # =========================================================================
    # 📝  TEXT / GROQ MODEL  →  existing flow, unchanged
    # =========================================================================
    else:

        audio_file = request.files.get("audio")
        if audio_file and audio_file.filename and _allowed_audio(audio_file.filename):
            audio_filename, _ = _save_audio(audio_file, upload_folder)

        if not text:
            flash("Please enter text.", "error")
            return redirect(url_for("main.translate_page"))

        try:
            if model_choice == "groq":
                translated_text = groq_translate(text, source_lang, target_lang)
            else:
                translated_text = translate_text(text, source_lang, target_lang)
        except Exception as e:
            logger.error("Translation error: %s", e)
            translated_text = f"Translation error: {str(e)}"

    # =========================================================================
    # 💾  HISTORY  +  📤  RESULT
    # =========================================================================
    add_entry(
        user_email=current_user.email,
        original_text=text,
        translated_text=translated_text,
        source_lang=source_lang,
        target_lang=target_lang,
        model_used=model_choice,
        audio_filename=audio_filename,
    )

    return render_template(
        "result.html",
        original_text=text,
        translated_text=translated_text,
        extracted_text=extracted_text,
        model_used=model_choice,
        source_lang=source_lang,
        target_lang=target_lang,
        audio_filename=audio_filename,
    )


# ── /process alias ────────────────────────────────────────────────────────────
@translate_bp.route("/process", methods=["POST"])
@login_required
def process():
    """Thin alias — /process POSTs are handled identically to /translate."""
    return translate()
