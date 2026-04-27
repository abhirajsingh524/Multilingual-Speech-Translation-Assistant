"""
routes/history.py — /history, /history/delete/<id>, /history/clear
MongoDB primary, JSON cache fallback via history_store.
"""
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from services.history_store import get_entries, delete_entry as delete_entry_svc, clear_entries
from config.db import is_connected

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
@login_required
def history():
    if not is_connected():
        flash("Database temporarily unavailable — showing offline history.", "warning")

    entries = get_entries(current_user.email, limit=100)
    return render_template("history.html", entries=entries)


@history_bp.route("/history/delete/<entry_id>", methods=["POST"])
@login_required
def delete_entry(entry_id: str):
    deleted = delete_entry_svc(current_user.email, entry_id)
    flash("Entry deleted." if deleted else "Entry not found.", "info")
    return redirect(url_for("history.history"))


@history_bp.route("/history/clear", methods=["POST"])
@login_required
def clear_history():
    clear_entries(current_user.email)
    flash("History cleared.", "info")
    return redirect(url_for("history.history"))
