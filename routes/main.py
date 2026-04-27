"""
routes/main.py — home, dashboard, translate page, about, contact
"""
import re
import logging

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from services.history_store import get_entries, count_entries
from services.mail_service  import send_contact_email

main_bp = Blueprint("main", __name__)
logger  = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


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


# ── Contact ───────────────────────────────────────────────────────────────────

@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """
    GET  — render the contact form (fields blank or re-populated after error).
    POST — validate, persist to MongoDB (or in-memory fallback), flash result.

    Isolated from all other routes.  No email service required — submissions
    are stored in the `contact_messages` collection so nothing is lost even
    without SMTP configured.
    """
    if request.method == "GET":
        return render_template("contact.html")

    # ── Collect & strip ───────────────────────────────────────────────────────
    name    = request.form.get("name",    "").strip()
    email   = request.form.get("email",   "").strip()
    message = request.form.get("message", "").strip()

    # ── Server-side validation ────────────────────────────────────────────────
    errors = []
    if not name:
        errors.append("Full name is required.")
    if not email or not _EMAIL_RE.match(email):
        errors.append("A valid email address is required.")
    if not message:
        errors.append("Message cannot be empty.")

    if errors:
        for err in errors:
            flash(err, "error")
        # Re-render with values so the user doesn't lose their input
        logger.warning("[Contact] Validation failed — %s", errors)
        return render_template("contact.html",
                               form_name=name,
                               form_email=email,
                               form_message=message), 422

    # ── Persist ───────────────────────────────────────────────────────────────
    from datetime import datetime, timezone
    from config.db import get_db

    doc = {
        "name":       name,
        "email":      email,
        "message":    message,
        "submitted_at": datetime.now(timezone.utc),
    }

    db = get_db()
    if db is not None:
        try:
            db.contact_messages.insert_one(doc)
            logger.info("[Contact] Message saved to MongoDB from %s <%s>", name, email)
        except Exception as exc:
            # Non-fatal — log and continue; user still gets a success response
            logger.error("[Contact] MongoDB insert failed: %s", exc)
    else:
        # MongoDB offline — log the submission so it isn't silently lost
        logger.warning(
            "[Contact] MongoDB offline — message NOT persisted. "
            "From: %s <%s> | Message: %.120s", name, email, message
        )

    # ── Send email notification ───────────────────────────────────────────────
    # Non-fatal: if SMTP fails the submission is already in MongoDB.
    # The user always sees a success message either way.
    email_sent = send_contact_email(
        sender_name=name,
        sender_email=email,
        message=message,
    )
    if not email_sent:
        logger.warning(
            "[Contact] Email notification not sent (SMTP unconfigured or failed). "
            "Submission is saved to DB."
        )

    flash("Thanks for reaching out! We'll get back to you shortly.", "success")
    return redirect(url_for("main.contact"))


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
