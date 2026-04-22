"""
Translation blueprint — /translate (POST)
Saves history to in-memory store instead of MongoDB.
Audio files saved to temp folder; auto-cleaned by scheduler.
"""
import os
import time
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from services.history_store import add_entry
from models.groq_translator import groq_translate
from models.translator import translate_text
from models.speech_to_text import speech_to_text   # ← Whisper integration

logger = logging.getLogger(__name__)

translate_bp = Blueprint("translate", __name__)

ALLOWED_AUDIO = {"mp3", "wav", "m4a", "ogg", "flac", "webm"}


def _allowed_audio(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_AUDIO


def _save_audio(audio_file, upload_folder: str) -> tuple[str, str]:
    """
    Save uploaded audio to upload_folder.
    Returns (filename, absolute_path).

    FIX: upload_folder is already absolute (set in app.py via os.path.abspath).
    We call os.path.abspath() again here as a safety net so Whisper always
    receives a full Windows path (e.g. C:\\...\\static\\uploads\\audio\\file.wav)
    instead of a relative one that triggers "The system cannot find the file".
    """
    # Guarantee the folder exists even if called before app startup completes
    os.makedirs(upload_folder, exist_ok=True)

    audio_filename = f"{int(time.time())}_{secure_filename(audio_file.filename)}"

    # Build and normalise to an absolute path
    save_path = os.path.abspath(os.path.join(upload_folder, audio_filename))

    audio_file.save(save_path)

    # Confirm the file actually landed on disk before returning
    if not os.path.exists(save_path):
        raise FileNotFoundError(f"File was not saved correctly: {save_path}")

    logger.info("Audio saved → %s", save_path)
    return audio_filename, save_path


@translate_bp.route("/translate", methods=["POST"])
@login_required
def translate():
    text         = request.form.get("text", "").strip()
    source_lang  = request.form.get("source_lang", "en")
    target_lang  = request.form.get("target_lang", "hi")
    model_choice = request.form.get("model_choice", "huggingface")

    audio_filename  = None
    extracted_text  = None          # only set when speech model is used
    upload_folder   = current_app.config["UPLOAD_FOLDER"]

    # ── SPEECH model: audio → text → translate ────────────────────────────────
    if model_choice == "speech":
        audio_file = request.files.get("audio")

        # Validate presence
        if not audio_file or not audio_file.filename:
            flash("Please upload an audio file when using the Speech model.", "error")
            return redirect(url_for("main.translate_page"))

        # Validate format
        if not _allowed_audio(audio_file.filename):
            flash("Unsupported format. Use MP3, WAV, M4A, OGG or FLAC.", "error")
            return redirect(url_for("main.translate_page"))

        # Step 1 — save to temp upload folder (absolute path guaranteed)
        try:
            audio_filename, save_path = _save_audio(audio_file, upload_folder)
        except (FileNotFoundError, OSError) as e:
            logger.error("Audio save failed: %s", e)
            flash(f"Could not save audio file: {e}", "error")
            return redirect(url_for("main.translate_page"))

        # Step 2 — double-check the file is on disk before calling Whisper
        if not os.path.exists(save_path):
            logger.error("File missing after save: %s", save_path)
            flash("Audio file could not be found after upload. Please try again.", "error")
            return redirect(url_for("main.translate_page"))

        logger.info("Passing to Whisper: %s (exists=%s)", save_path, os.path.exists(save_path))

        # Step 3 — convert audio → text using existing speech_to_text()
        extracted_text = speech_to_text(save_path)
        if not extracted_text or extracted_text.startswith("Error:"):
            flash(f"Speech recognition failed: {extracted_text}", "error")
            return redirect(url_for("main.translate_page"))

        # Step 3 — translate the extracted text with the HuggingFace model
        try:
            translated_text = translate_text(extracted_text, source_lang, target_lang)
        except Exception as e:
            logger.error("Translation error (speech): %s", e)
            translated_text = f"Translation error: {str(e)}"

        # Use extracted text as the "original" for history / result display
        text = extracted_text

    else:
        # ── TEXT / GROQ models: existing flow, unchanged ──────────────────────
        audio_file = request.files.get("audio")
        if audio_file and audio_file.filename:
            if not _allowed_audio(audio_file.filename):
                flash("Unsupported format. Use MP3, WAV, M4A, OGG or FLAC.", "error")
                return redirect(url_for("main.translate_page"))
            audio_filename, _ = _save_audio(audio_file, upload_folder)

        if not text:
            flash("Please enter text or upload an audio file.", "error")
            return redirect(url_for("main.translate_page"))

        try:
            if model_choice == "groq":
                translated_text = groq_translate(text, source_lang, target_lang)
            else:
                translated_text = translate_text(text, source_lang, target_lang)
        except Exception as e:
            logger.error("Translation error: %s", e)
            translated_text = f"Translation error: {str(e)}"

    # ── Save to in-memory history ─────────────────────────────────────────────
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
        model_used=model_choice,
        source_lang=source_lang,
        target_lang=target_lang,
        audio_filename=audio_filename,
        extracted_text=extracted_text,   # None for non-speech models
    )
