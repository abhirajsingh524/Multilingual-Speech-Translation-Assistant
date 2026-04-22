"""
MSTA — Multilingual Speech Translation Assistant
In-memory mode: no MongoDB, no external database required.
"""
import os
import logging
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

# ── MongoDB imports REMOVED ───────────────────────────────────────────────────
# from flask_pymongo import PyMongo   # <-- disabled

from services.auth_service import User, get_user_by_id
from services.cleanup import start_cleanup_scheduler

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

login_manager = LoginManager()


def create_app() -> Flask:
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "msta-temp-secret-key-2026")
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 26214400))  # 25 MB

    # FIX: store UPLOAD_FOLDER as an absolute path anchored to this file's
    # directory so it resolves correctly regardless of the working directory
    # Flask is launched from (critical on Windows).
    _base_dir = os.path.dirname(os.path.abspath(__file__))
    app.config["UPLOAD_FOLDER"] = os.path.join(_base_dir, "static", "uploads", "audio")
    app.config["OUTPUT_FOLDER"] = os.path.join(_base_dir, "static", "outputs", "speech")

    # ── MongoDB config REMOVED ────────────────────────────────────────────────
    # app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/msta_db")
    # mongo.init_app(app)

    # ── Ensure upload/output directories exist ────────────────────────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

    # ── Flask-Login ───────────────────────────────────────────────────────────
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id: str):
        doc = get_user_by_id(user_id)          # in-memory lookup
        return User(doc) if doc else None

    # ── Register blueprints ───────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.translate import translate_bp
    from routes.history import history_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(translate_bp)
    app.register_blueprint(history_bp)

    # ── MongoDB index creation REMOVED ────────────────────────────────────────
    # with app.app_context():
    #     mongo.db.users.create_index("email", unique=True)
    #     mongo.db.history.create_index([("user_id", 1), ("timestamp", -1)])

    # ── Background audio cleanup ──────────────────────────────────────────────
    max_age = int(os.getenv("FILE_CLEANUP_HOURS", 24))
    start_cleanup_scheduler(app.config["UPLOAD_FOLDER"], max_age)

    logger.info("MSTA started in in-memory mode (no database).")
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
