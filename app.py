"""
MSTA — Multilingual Speech Translation Assistant
MongoDB primary, in-memory/cache fallback.
Google OAuth via Authlib.
"""
import os
import time
import logging
from flask import Flask, g
from flask_login import LoginManager
from dotenv import load_dotenv

from services.auth_service import User, get_user_by_id
from services.cleanup import start_cleanup_scheduler
from services.oauth_service import init_oauth
from services.load_monitor import record_response
from config.db import init_db, is_connected

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

login_manager = LoginManager()


def create_app() -> Flask:
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────────────
    app.config["SECRET_KEY"]          = os.getenv("SECRET_KEY", "msta-temp-secret-key-2026")
    app.config["MAX_CONTENT_LENGTH"]  = int(os.getenv("MAX_CONTENT_LENGTH", 26214400))

    # Google OAuth credentials (set in .env)
    app.config["GOOGLE_CLIENT_ID"]     = os.getenv("GOOGLE_CLIENT_ID", "")
    app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET", "")

    _base_dir = os.path.dirname(os.path.abspath(__file__))
    app.config["UPLOAD_FOLDER"] = os.path.join(_base_dir, "static", "uploads", "audio")
    app.config["OUTPUT_FOLDER"] = os.path.join(_base_dir, "static", "outputs", "speech")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

    # ── MongoDB ───────────────────────────────────────────────────────────────
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    init_db(uri=mongo_uri, db_name="translator_app")

    if is_connected():
        logger.info("Running with MongoDB storage.")
    else:
        logger.warning("MongoDB offline — using in-memory + JSON cache fallback.")

    # ── Google OAuth ──────────────────────────────────────────────────────────
    init_oauth(app)

    # ── Request timing hooks (feeds load_monitor) ────────────────────────────
    @app.before_request
    def _start_timer():
        g._req_start = time.monotonic()

    @app.after_request
    def _record_timing(response):
        start = getattr(g, '_req_start', None)
        if start is not None:
            record_response(time.monotonic() - start)
        return response

    # ── Flask-Login ───────────────────────────────────────────────────────────
    login_manager.init_app(app)
    login_manager.login_view         = "auth.login"
    login_manager.login_message      = "Please sign in to access this page."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id: str):
        doc = get_user_by_id(user_id)
        return User(doc) if doc else None

    # ── Blueprints ────────────────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.translate import translate_bp
    from routes.history import history_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(translate_bp)
    app.register_blueprint(history_bp)

    # ── Background audio cleanup ──────────────────────────────────────────────
    max_age = int(os.getenv("FILE_CLEANUP_HOURS", 24))
    start_cleanup_scheduler(app.config["UPLOAD_FOLDER"], max_age)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5002)
