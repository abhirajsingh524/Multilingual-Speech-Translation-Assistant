"""
services/auth_service.py
Authentication service — MongoDB primary, in-memory fallback.

User documents in MongoDB:
  { _id, username, email, password_hash, created_at }

In-memory fallback (USERS dict) is used when MongoDB is offline.
Passwords are hashed with werkzeug.security (pbkdf2:sha256).
"""
import logging
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from config.db import get_db

logger = logging.getLogger(__name__)

# ── In-memory fallback store ──────────────────────────────────────────────────
# Seeded with the demo account.  Password stored as a proper hash.
_DEMO_HASH = generate_password_hash("anoop@123")

USERS: dict[str, dict] = {
    "anoop12@gmail.com": {
        "_id":           "user_001",
        "username":      "Anoop",
        "email":         "anoop12@gmail.com",
        "password_hash": _DEMO_HASH,   # bcrypt hash of "anoop@123"
        "created_at":    datetime.now(timezone.utc),
    }
}


# ── Flask-Login User wrapper ──────────────────────────────────────────────────

class User(UserMixin):
    def __init__(self, doc: dict):
        self._doc = doc

    def get_id(self) -> str:
        return str(self._doc["_id"])

    @property
    def username(self) -> str:
        return self._doc.get("username", "User")

    @property
    def email(self) -> str:
        return self._doc["email"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mem_get(email: str):
    return USERS.get(email.lower().strip())


def _mem_get_by_id(user_id: str):
    for u in USERS.values():
        if str(u["_id"]) == user_id:
            return u
    return None


# ── Public API ────────────────────────────────────────────────────────────────

def register_user(username: str, email: str, password: str):
    """
    Create a new user.  MongoDB primary, in-memory fallback.
    Returns (user_doc, error_string).
    """
    email = email.lower().strip()
    pw_hash = generate_password_hash(password)

    db = get_db()
    if db is not None:
        try:
            if db.users.find_one({"email": email}):
                return None, "An account with that email already exists."
            if db.users.find_one({"username": username}):
                return None, "That username is already taken."

            doc = {
                "username":      username,
                "email":         email,
                "password_hash": pw_hash,
                "created_at":    datetime.now(timezone.utc),
            }
            result = db.users.insert_one(doc)
            doc["_id"] = result.inserted_id
            logger.info("User registered in MongoDB: %s", email)
            return doc, None

        except Exception as e:
            logger.error("MongoDB register error: %s", e)
            # fall through to in-memory

    # In-memory fallback
    if email in USERS:
        return None, "An account with that email already exists."
    if any(u["username"] == username for u in USERS.values()):
        return None, "That username is already taken."

    doc = {
        "_id":           f"mem_{len(USERS)+1}",
        "username":      username,
        "email":         email,
        "password_hash": pw_hash,
        "created_at":    datetime.now(timezone.utc),
    }
    USERS[email] = doc
    logger.info("User registered in memory (DB offline): %s", email)
    return doc, None


def authenticate_user(email: str, password: str):
    """
    Verify credentials.  MongoDB primary, in-memory fallback.
    Returns (user_doc, error_string).
    """
    email = email.lower().strip()

    db = get_db()
    if db is not None:
        try:
            doc = db.users.find_one({"email": email})
            if doc:
                if check_password_hash(doc["password_hash"], password):
                    return doc, None
                return None, "Incorrect password."
            # Not in DB — check in-memory (covers demo account when DB is fresh)
        except Exception as e:
            logger.error("MongoDB auth error: %s", e)

    # In-memory fallback
    doc = _mem_get(email)
    if not doc:
        return None, "No account found with that email."
    if not check_password_hash(doc["password_hash"], password):
        return None, "Incorrect password."
    return doc, None


def get_user_by_id(user_id: str):
    """Flask-Login user_loader — returns raw dict or None."""
    db = get_db()
    if db is not None:
        try:
            from bson import ObjectId
            doc = db.users.find_one({"_id": ObjectId(user_id)})
            if doc:
                return doc
        except Exception:
            pass  # ObjectId parse fail or DB error → try memory

    return _mem_get_by_id(user_id)
