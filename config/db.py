"""
config/db.py — MongoDB singleton with liveness probe.

Key fixes vs previous version:
  1. Re-attempt connection on every get_db() call if currently disconnected
     (handles the case where Mongo starts after Flask).
  2. Liveness probe on get_db() — if the handle exists but the server
     dropped, we detect it and reset so callers fall back to cache.
  3. Thread-safe via a simple lock (Flask dev server is multi-threaded).
"""
import logging
import threading
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

_client   = None
_db       = None
_uri      = "mongodb://localhost:27017/"
_db_name  = "translator_app"
_lock     = threading.Lock()


def init_db(uri: str = "mongodb://localhost:27017/", db_name: str = "translator_app"):
    """
    Store connection params and attempt first connection.
    Called once from create_app().
    """
    global _uri, _db_name
    _uri     = uri
    _db_name = db_name
    _connect()          # attempt; silently continues if Mongo is offline


def _connect():
    """Internal: try to open (or re-open) the MongoDB connection."""
    global _client, _db

    with _lock:
        try:
            client = MongoClient(_uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")            # real connection test
            db = client[_db_name]

            # Idempotent indexes
            db.users.create_index("email",    unique=True)
            db.users.create_index("username", unique=True)
            db.history.create_index(
                [("user_email", ASCENDING), ("timestamp", DESCENDING)]
            )

            _client = client
            _db     = db
            logger.info("MongoDB connected → %s / %s", _uri, _db_name)

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning("MongoDB unavailable — offline/cache mode. (%s)", e)
            _client = None
            _db     = None


def get_db():
    """
    Return the db handle.
    - If currently connected: run a cheap liveness ping; reset on failure.
    - If currently disconnected: attempt reconnect (so Mongo can start late).
    Returns None when MongoDB is genuinely unavailable.
    """
    global _client, _db

    if _db is not None:
        # Liveness check — detect dropped connections
        try:
            _client.admin.command("ping")
            return _db
        except Exception:
            logger.warning("MongoDB connection lost — resetting handle.")
            with _lock:
                _client = None
                _db     = None

    # Not connected — try once to reconnect
    _connect()
    return _db


def is_connected() -> bool:
    return get_db() is not None
