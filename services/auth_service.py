"""
Authentication service — in-memory user store (no database).

MongoDB code has been replaced with a simple Python dict.
A seed user is pre-loaded so the app works immediately without any setup.
"""
from flask_login import UserMixin

# ─── In-memory user store ─────────────────────────────────────────────────────
# Key: email (lowercase)  Value: user dict
# Passwords are stored as plain text here for the temporary/demo setup.
# In production, replace with bcrypt hashes + a real database.

USERS: dict[str, dict] = {
    "anoop12@gmail.com": {
        "_id": "user_001",
        "username": "Anoop",
        "email": "anoop12@gmail.com",
        "password": "anoop@123",   # plain-text for demo only
    }
}


# ─── Flask-Login compatible User class ───────────────────────────────────────

class User(UserMixin):
    """Thin wrapper around an in-memory user dict for Flask-Login."""

    def __init__(self, user_doc: dict):
        self._doc = user_doc

    def get_id(self) -> str:
        return str(self._doc["_id"])

    @property
    def username(self) -> str:
        return self._doc["username"]

    @property
    def email(self) -> str:
        return self._doc["email"]


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def authenticate_user(email: str, password: str):
    """
    Check credentials against the in-memory store.
    Returns (user_doc, error_string).
    """
    email = email.lower().strip()
    user = USERS.get(email)
    if not user:
        return None, "No account found with that email."
    if user["password"] != password:
        return None, "Incorrect password."
    return user, None


def get_user_by_id(user_id: str):
    """
    Load a user by their _id string (used by Flask-Login user_loader).
    """
    for user in USERS.values():
        if str(user["_id"]) == user_id:
            return user
    return None
