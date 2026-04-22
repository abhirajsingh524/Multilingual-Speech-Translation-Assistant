"""
In-memory translation history store (no database).

Stores history as a list of dicts, keyed by user email.
Data is lost on app restart — this is intentional for the temporary setup.
"""
from datetime import datetime, timezone
from collections import defaultdict

# ─── In-memory store ──────────────────────────────────────────────────────────
# { user_email: [ {entry}, ... ] }   newest entries appended last
_history: dict[str, list] = defaultdict(list)

# Auto-incrementing ID counter
_id_counter = 0


def _next_id() -> str:
    global _id_counter
    _id_counter += 1
    return f"hist_{_id_counter}"


# ─── CRUD helpers ─────────────────────────────────────────────────────────────

def add_entry(
    user_email: str,
    original_text: str,
    translated_text: str,
    source_lang: str,
    target_lang: str,
    model_used: str,
    audio_filename: str = None,
) -> dict:
    """Append a new history entry and return it."""
    entry = {
        "id": _next_id(),
        "user_email": user_email,
        "original_text": original_text,
        "translated_text": translated_text,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "model_used": model_used,
        "audio_filename": audio_filename,
        "timestamp": datetime.now(timezone.utc),
    }
    _history[user_email].append(entry)
    return entry


def get_entries(user_email: str, limit: int = 100) -> list:
    """Return entries for a user, newest first."""
    entries = _history.get(user_email, [])
    return list(reversed(entries))[:limit]


def delete_entry(user_email: str, entry_id: str) -> bool:
    """Remove a single entry. Returns True if found and deleted."""
    entries = _history.get(user_email, [])
    for i, e in enumerate(entries):
        if e["id"] == entry_id:
            entries.pop(i)
            return True
    return False


def clear_entries(user_email: str) -> None:
    """Remove all history for a user."""
    _history[user_email] = []


def count_entries(user_email: str) -> int:
    return len(_history.get(user_email, []))
