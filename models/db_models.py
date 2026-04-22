"""
MongoDB document helpers for User and TranslationHistory.
We use PyMongo directly (no ORM) for simplicity and performance.
"""
from datetime import datetime, timezone
from bson import ObjectId


# ─── User helpers ────────────────────────────────────────────────────────────

def make_user(username: str, email: str, password_hash: str) -> dict:
    """Return a new user document ready for insertion."""
    return {
        "username": username,
        "email": email.lower().strip(),
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc),
    }


def user_to_dict(user: dict) -> dict:
    """Serialize a user document for safe external use (no password)."""
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "created_at": user.get("created_at", ""),
    }


# ─── Translation History helpers ─────────────────────────────────────────────

def make_history_entry(
    user_id: str,
    original_text: str,
    translated_text: str,
    source_lang: str,
    target_lang: str,
    model_used: str,
    audio_filename: str = None,
) -> dict:
    """Return a new history document ready for insertion."""
    return {
        "user_id": user_id,
        "original_text": original_text,
        "translated_text": translated_text,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "model_used": model_used,
        "audio_filename": audio_filename,
        "timestamp": datetime.now(timezone.utc),
    }


def history_to_dict(entry: dict) -> dict:
    """Serialize a history document for template rendering."""
    return {
        "id": str(entry["_id"]),
        "original_text": entry.get("original_text", ""),
        "translated_text": entry.get("translated_text", ""),
        "source_lang": entry.get("source_lang", ""),
        "target_lang": entry.get("target_lang", ""),
        "model_used": entry.get("model_used", ""),
        "audio_filename": entry.get("audio_filename"),
        "timestamp": entry.get("timestamp", ""),
    }
