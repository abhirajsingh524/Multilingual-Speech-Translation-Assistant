"""
services/history_store.py
Translation history — three-layer storage with correct priority.

Layer 1 — MongoDB          (authoritative, always tried first)
Layer 2 — JSON file cache  (per-user file, written ONLY when MongoDB fails)
Layer 3 — In-memory dict   (last resort; lost on restart)

Key fixes vs previous version:
  A. Cache is written ONLY on MongoDB failure, not on every insert
     (eliminates duplicate entries in cache).
  B. Timestamp normalisation: all datetimes are timezone-aware UTC before
     being stored or returned, so template .strftime() never raises.
  C. In-memory TTL cache sits in front of MongoDB to reduce DB round-trips
     on the history page (TTL = 60 s per user).
  D. _append_cache no longer reads+rewrites the whole file on every call;
     it appends a single JSON line (NDJSON) for O(1) writes.
  E. Offline-to-online sync: when MongoDB comes back, pending cache entries
     are flushed to the DB automatically.
"""
import os
import json
import logging
import hashlib
import threading
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Optional

from config.db import get_db

logger = logging.getLogger(__name__)

# ── Cache folder ──────────────────────────────────────────────────────────────
_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_history")
os.makedirs(_CACHE_DIR, exist_ok=True)

# ── In-memory TTL cache (reduces DB hits on history page) ────────────────────
# Structure: { user_email: {"entries": [...], "expires_at": datetime} }
_ttl_cache: dict[str, dict] = {}
_TTL_SECONDS = 60           # invalidate after 60 s
_cache_lock  = threading.Lock()

# ── In-memory fallback (used only when DB + cache both fail) ─────────────────
_memory: dict[str, list] = defaultdict(list)
_id_counter = 0
_mem_lock   = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _next_id() -> str:
    global _id_counter
    with _mem_lock:
        _id_counter += 1
        return f"hist_{_id_counter}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(dt) -> Optional[datetime]:
    """Guarantee a timezone-aware datetime (or None)."""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)   # assume UTC
        return dt
    return None


def _serialise_entry(entry: dict) -> dict:
    """Return a JSON-safe copy of an entry."""
    row = dict(entry)
    ts = row.get("timestamp")
    if isinstance(ts, datetime):
        row["timestamp"] = ts.isoformat()
    if "_id" in row:
        row["_id"] = str(row["_id"])
    return row


def _deserialise_entry(row: dict) -> dict:
    """Restore types after loading from JSON."""
    row = dict(row)
    row["timestamp"] = _ensure_aware(row.get("timestamp"))
    if "id" not in row and "_id" in row:
        row["id"] = str(row["_id"])
    return row


# ─────────────────────────────────────────────────────────────────────────────
# JSON cache (NDJSON — one JSON object per line for O(1) appends)
# ─────────────────────────────────────────────────────────────────────────────

def _cache_path(user_email: str) -> str:
    safe = hashlib.md5(user_email.encode()).hexdigest()
    return os.path.join(_CACHE_DIR, f"{safe}.ndjson")


def _cache_append(user_email: str, entry: dict):
    """Append a single entry to the NDJSON cache file (fast, no full rewrite)."""
    path = _cache_path(user_email)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(_serialise_entry(entry), ensure_ascii=False) + "\n")
    except Exception as ex:
        logger.warning("Cache append error for %s: %s", user_email, ex)


def _cache_load(user_email: str) -> list:
    """Load all entries from the NDJSON cache, newest-first."""
    path = _cache_path(user_email)
    if not os.path.exists(path):
        return []
    entries = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(_deserialise_entry(json.loads(line)))
                except json.JSONDecodeError:
                    continue
    except Exception as ex:
        logger.warning("Cache load error for %s: %s", user_email, ex)
    return list(reversed(entries))     # newest first


def _cache_rewrite(user_email: str, entries: list):
    """Rewrite the entire cache (used for delete/clear operations)."""
    path = _cache_path(user_email)
    try:
        with open(path, "w", encoding="utf-8") as f:
            # Write oldest-first so _cache_load reversal gives newest-first
            for e in reversed(entries):
                f.write(json.dumps(_serialise_entry(e), ensure_ascii=False) + "\n")
    except Exception as ex:
        logger.warning("Cache rewrite error for %s: %s", user_email, ex)


# ─────────────────────────────────────────────────────────────────────────────
# TTL in-memory cache helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ttl_get(user_email: str) -> Optional[list]:
    with _cache_lock:
        slot = _ttl_cache.get(user_email)
        if slot and slot["expires_at"] > _utc_now():
            return slot["entries"]
        if slot:
            del _ttl_cache[user_email]   # expired
    return None


def _ttl_set(user_email: str, entries: list):
    with _cache_lock:
        _ttl_cache[user_email] = {
            "entries":    entries,
            "expires_at": _utc_now() + timedelta(seconds=_TTL_SECONDS),
        }


def _ttl_invalidate(user_email: str):
    with _cache_lock:
        _ttl_cache.pop(user_email, None)


# ─────────────────────────────────────────────────────────────────────────────
# Offline-to-online sync
# ─────────────────────────────────────────────────────────────────────────────

def sync_cache_to_db(user_email: str):
    """
    Push any cache entries that are not yet in MongoDB.
    Called automatically by get_entries() when DB becomes available.
    Safe to call multiple times (uses upsert logic via a cache_id field).
    """
    db = get_db()
    if db is None:
        return

    cached = _cache_load(user_email)
    if not cached:
        return

    synced = 0
    for entry in cached:
        cache_id = entry.get("id", "")
        if not cache_id or cache_id.startswith("hist_"):
            # Only sync entries that were created offline (no real ObjectId)
            try:
                doc = {k: v for k, v in entry.items() if k not in ("id", "_id")}
                doc["timestamp"] = _ensure_aware(doc.get("timestamp")) or _utc_now()
                db.history.update_one(
                    {"user_email": user_email, "original_text": doc["original_text"],
                     "timestamp": doc["timestamp"]},
                    {"$setOnInsert": doc},
                    upsert=True,
                )
                synced += 1
            except Exception as ex:
                logger.warning("Sync entry failed: %s", ex)

    if synced:
        logger.info("Synced %d offline entries to MongoDB for %s", synced, user_email)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def add_entry(
    user_email: str,
    original_text: str,
    translated_text: str,
    source_lang: str,
    target_lang: str,
    model_used: str,
    audio_filename: str = None,
) -> dict:
    """
    Persist a translation entry.

    Priority:
      1. MongoDB  → on success, invalidate TTL cache, done.
      2. JSON cache + in-memory  → only when MongoDB fails.
    """
    entry = {
        "user_email":      user_email,
        "original_text":   original_text,
        "translated_text": translated_text,
        "source_lang":     source_lang,
        "target_lang":     target_lang,
        "model_used":      model_used,
        "audio_filename":  audio_filename,
        "timestamp":       _utc_now(),
    }

    db = get_db()
    if db is not None:
        try:
            result = db.history.insert_one(dict(entry))
            entry["_id"] = result.inserted_id
            entry["id"]  = str(result.inserted_id)
            _ttl_invalidate(user_email)          # force fresh fetch next time
            logger.info("History saved to MongoDB for %s", user_email)
            return entry                         # ← success path, no cache write
        except Exception as e:
            logger.error("MongoDB insert failed for %s: %s — falling back to cache", user_email, e)

    # ── Fallback: DB unavailable or insert failed ─────────────────────────────
    entry["id"] = _next_id()
    _cache_append(user_email, entry)             # NDJSON append (fast)
    with _mem_lock:
        _memory[user_email].append(entry)
    logger.warning("History saved to cache (offline) for %s", user_email)
    return entry


def get_entries(user_email: str, limit: int = 100) -> list:
    """
    Fetch history newest-first.

    Priority:
      1. TTL in-memory cache  (fast, avoids DB on every page load)
      2. MongoDB              (authoritative)
      3. JSON file cache      (offline fallback)
      4. In-memory dict       (last resort)
    """
    # ── 1. TTL cache hit ──────────────────────────────────────────────────────
    cached = _ttl_get(user_email)
    if cached is not None:
        return cached[:limit]

    # ── 2. MongoDB ────────────────────────────────────────────────────────────
    db = get_db()
    if db is not None:
        try:
            # Opportunistically sync any offline entries first
            sync_cache_to_db(user_email)

            cursor = (
                db.history
                .find({"user_email": user_email})
                .sort("timestamp", -1)
                .limit(limit)
            )
            entries = []
            for doc in cursor:
                doc["id"]        = str(doc["_id"])
                doc["timestamp"] = _ensure_aware(doc.get("timestamp"))
                entries.append(doc)

            _ttl_set(user_email, entries)        # populate TTL cache
            return entries

        except Exception as e:
            logger.error("MongoDB fetch failed for %s: %s — using cache", user_email, e)

    # ── 3. JSON file cache ────────────────────────────────────────────────────
    file_entries = _cache_load(user_email)
    if file_entries:
        logger.info("Serving history from file cache for %s", user_email)
        return file_entries[:limit]

    # ── 4. In-memory last resort ──────────────────────────────────────────────
    with _mem_lock:
        mem = list(reversed(_memory.get(user_email, [])))
    return mem[:limit]


def delete_entry(user_email: str, entry_id: str) -> bool:
    """Delete one entry from all layers."""
    deleted = False
    _ttl_invalidate(user_email)

    db = get_db()
    if db is not None:
        try:
            from bson import ObjectId
            res = db.history.delete_one(
                {"_id": ObjectId(entry_id), "user_email": user_email}
            )
            deleted = res.deleted_count > 0
        except Exception as e:
            logger.error("MongoDB delete error: %s", e)

    # Sync cache
    cached = _cache_load(user_email)
    new_cache = [
        e for e in cached
        if str(e.get("_id", e.get("id", ""))) != entry_id
    ]
    if len(new_cache) != len(cached):
        _cache_rewrite(user_email, list(reversed(new_cache)))  # oldest-first for file
        deleted = True

    # Sync memory
    with _mem_lock:
        _memory[user_email] = [
            e for e in _memory.get(user_email, [])
            if str(e.get("id", "")) != entry_id
        ]

    return deleted


def clear_entries(user_email: str):
    """Delete all history for a user from all layers."""
    _ttl_invalidate(user_email)

    db = get_db()
    if db is not None:
        try:
            db.history.delete_many({"user_email": user_email})
        except Exception as e:
            logger.error("MongoDB clear error: %s", e)

    path = _cache_path(user_email)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

    with _mem_lock:
        _memory[user_email] = []


def count_entries(user_email: str) -> int:
    db = get_db()
    if db is not None:
        try:
            return db.history.count_documents({"user_email": user_email})
        except Exception:
            pass

    file_entries = _cache_load(user_email)
    if file_entries:
        return len(file_entries)

    with _mem_lock:
        return len(_memory.get(user_email, []))
