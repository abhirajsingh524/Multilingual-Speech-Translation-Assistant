"""
routes/main.py — home, dashboard, translate page, about, contact
"""
from flask import Blueprint, render_template, redirect, url_for, request
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
    recent = get_entries(current_user.email, limit=5)
    total  = count_entries(current_user.email)
    return render_template("dashboard.html", recent=recent, total=total)


@main_bp.route("/translate-page")
@login_required
def translate_page():
    return render_template("index.html")


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/contact")
def contact():
    return render_template("contact.html")


@main_bp.route("/processing")
def processing():
    """
    Adaptive processing panel.
    Backend evaluates current load and passes show_hacker_panel flag.
    Template renders hacker panel (high load) or standard loader (normal).
    redirect_to is the destination after the animation completes.
    """
    from services.load_monitor import should_show_hacker_panel
    redirect_to       = request.args.get("redirect", url_for("main.dashboard"))
    show_hacker_panel = should_show_hacker_panel()
    return render_template(
        "processing.html",
        redirect_to=redirect_to,
        show_hacker_panel=show_hacker_panel,
    )
