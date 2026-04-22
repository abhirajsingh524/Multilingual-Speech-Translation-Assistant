"""
History blueprint — /history, /history/delete/<id>, /history/clear
Uses in-memory history store instead of MongoDB.
"""
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from services.history_store import get_entries, delete_entry, clear_entries

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
@login_required
def history():
    # ── In-memory lookup (no MongoDB) ─────────────────────────────────────
    entries = get_entries(current_user.email, limit=100)
    return render_template("history.html", entries=entries)


@history_bp.route("/history/delete/<entry_id>", methods=["POST"])
@login_required
def delete_entry_route(entry_id: str):
    deleted = delete_entry(current_user.email, entry_id)
    flash("Entry deleted." if deleted else "Entry not found.", "info")
    return redirect(url_for("history.history"))


@history_bp.route("/history/clear", methods=["POST"])
@login_required
def clear_history():
    clear_entries(current_user.email)
    flash("History cleared.", "info")
    return redirect(url_for("history.history"))
