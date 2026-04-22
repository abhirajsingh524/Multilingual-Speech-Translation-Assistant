"""
Main blueprint — home redirect and protected dashboard.
Uses in-memory history store instead of MongoDB.
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from services.history_store import get_entries, count_entries

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    # ── Pull from in-memory store (no MongoDB) ────────────────────────────
    recent = get_entries(current_user.email, limit=5)
    total  = count_entries(current_user.email)
    return render_template("dashboard.html", recent=recent, total=total)


@main_bp.route("/translate-page")
@login_required
def translate_page():
    return render_template("index.html")
