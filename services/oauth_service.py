"""
services/oauth_service.py
Google OAuth 2.0 via Authlib.

Flow:
  1. /auth/google/login  → redirect to Google consent screen
  2. Google redirects to /auth/google/callback with ?code=...
  3. We exchange code for token, fetch user profile, upsert in DB
  4. Log the user in and redirect to dashboard

Security:
  - state parameter handled automatically by Authlib
  - redirect_uri validated server-side
  - no sensitive data stored in session beyond user_id
"""
import logging
from datetime import datetime, timezone

from authlib.integrations.flask_client import OAuth

from config.db import get_db
from services.auth_service import USERS   # in-memory fallback

logger = logging.getLogger(__name__)

# Singleton OAuth registry — initialised once in create_app()
oauth = OAuth()


def init_oauth(app):
    """Register Google provider. Call once from create_app()."""
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID", ""),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET", ""),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    return oauth


def upsert_oauth_user(profile: dict) -> dict:
    """
    Find or create a user from a Google profile dict.
    Returns the user document (MongoDB or in-memory).

    profile keys we use: sub, email, name, picture
    """
    email    = profile.get("email", "").lower().strip()
    name     = profile.get("name", email.split("@")[0])
    google_id = profile.get("sub", "")

    # ── MongoDB path ──────────────────────────────────────────────────────────
    db = get_db()
    if db is not None:
        try:
            doc = db.users.find_one({"email": email})
            if doc:
                # Link Google ID if not already stored
                if not doc.get("google_id"):
                    db.users.update_one({"_id": doc["_id"]}, {"$set": {"google_id": google_id}})
                return doc

            # New user via Google
            doc = {
                "username":    _safe_username(name, db),
                "email":       email,
                "password_hash": None,          # no password for OAuth users
                "google_id":   google_id,
                "avatar":      profile.get("picture", ""),
                "created_at":  datetime.now(timezone.utc),
            }
            result = db.users.insert_one(doc)
            doc["_id"] = result.inserted_id
            logger.info("OAuth user created in MongoDB: %s", email)
            return doc

        except Exception as e:
            logger.error("MongoDB OAuth upsert error: %s", e)

    # ── In-memory fallback ────────────────────────────────────────────────────
    if email in USERS:
        return USERS[email]

    doc = {
        "_id":           f"oauth_{google_id[:8]}",
        "username":      name,
        "email":         email,
        "password_hash": None,
        "google_id":     google_id,
        "avatar":        profile.get("picture", ""),
        "created_at":    datetime.now(timezone.utc),
    }
    USERS[email] = doc
    logger.info("OAuth user created in memory: %s", email)
    return doc


def _safe_username(name: str, db) -> str:
    """Generate a unique username from the Google display name."""
    base = "".join(c for c in name.replace(" ", "_") if c.isalnum() or c == "_")[:28] or "user"
    candidate = base
    i = 1
    while db.users.find_one({"username": candidate}):
        candidate = f"{base}_{i}"
        i += 1
    return candidate
