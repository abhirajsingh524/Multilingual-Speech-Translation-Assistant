"""
routes/auth.py
Authentication blueprint — local login/signup + Google OAuth + My Space entry.

Routes (all existing routes preserved):
  GET/POST /auth/login          — standard email/password login
  GET/POST /auth/signup         — new account registration
  GET      /auth/register       — alias for /auth/signup
  GET      /auth/logout         — clear session
  GET      /auth/myspace        — unified entry point (navbar button)
  GET      /auth/google/login   — start Google OAuth flow
  GET      /auth/google/callback— Google OAuth callback
"""
import re
import logging

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from flask_login import login_user, logout_user, login_required, current_user

from services.auth_service import User, authenticate_user, register_user
from services.oauth_service import oauth, upsert_oauth_user
from config.db import is_connected

logger = logging.getLogger(__name__)

auth_bp   = Blueprint("auth", __name__, url_prefix="/auth")
EMAIL_RE  = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ─────────────────────────────────────────────────────────────────────────────
# My Space — unified navbar entry point
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/myspace")
def myspace():
    """
    Single entry point shown in the navbar as 'My Space'.
    Authenticated → dashboard.
    Unauthenticated → unified login/signup page.
    ?tab=signup opens the signup panel directly.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    tab = request.args.get("tab", "login")
    return render_template("myspace.html", active_tab=tab)


# ─────────────────────────────────────────────────────────────────────────────
# Standard login
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("myspace.html", active_tab="login", email=email)

        user_doc, error = authenticate_user(email, password)
        if error:
            flash(error, "error")
            return render_template("myspace.html", active_tab="login", email=email)

        login_user(User(user_doc), remember=True)
        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.dashboard"))

    # GET → show unified page with login tab
    return render_template("myspace.html", active_tab="login")


# ─────────────────────────────────────────────────────────────────────────────
# Standard signup
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        errors = []
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", username):
            errors.append("Username must be 3–30 characters (letters, numbers, underscores).")
        if not EMAIL_RE.match(email):
            errors.append("Please enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("myspace.html", active_tab="signup",
                                   username=username, su_email=email)

        user_doc, error = register_user(username, email, password)
        if error:
            flash(error, "error")
            return render_template("myspace.html", active_tab="signup",
                                   username=username, su_email=email)

        login_user(User(user_doc), remember=True)
        flash("Account created! Welcome to MSTA.", "success")
        return redirect(url_for("main.dashboard"))

    # GET → show unified page with signup tab
    return render_template("myspace.html", active_tab="signup")


# Alias
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    return signup()


# ─────────────────────────────────────────────────────────────────────────────
# Logout
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


# ─────────────────────────────────────────────────────────────────────────────
# Google OAuth 2.0
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/google/login")
def google_login():
    """Redirect user to Google consent screen."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    redirect_uri = url_for("auth.google_callback", _external=True)
    # Authlib handles state parameter automatically (CSRF protection)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback")
def google_callback():
    """
    Google redirects here after user grants permission.
    Exchange code → token → fetch profile → upsert user → login.
    """
    try:
        token   = oauth.google.authorize_access_token()
        profile = token.get("userinfo") or oauth.google.userinfo()
    except Exception as e:
        logger.error("Google OAuth callback error: %s", e)
        flash("Google sign-in failed. Please try again or use email/password.", "error")
        return redirect(url_for("auth.login"))

    if not profile or not profile.get("email"):
        flash("Could not retrieve your Google account details.", "error")
        return redirect(url_for("auth.login"))

    try:
        user_doc = upsert_oauth_user(profile)
    except Exception as e:
        logger.error("OAuth user upsert error: %s", e)
        flash("Account setup failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    login_user(User(user_doc), remember=True)
    flash(f"Welcome, {user_doc.get('username', 'there')}! Signed in with Google.", "success")

    next_page = session.pop("oauth_next", None) or url_for("main.dashboard")
    return redirect(next_page)


# ─────────────────────────────────────────────────────────────────────────────
# Latency probe endpoint (HEAD /auth/ping)
# Used by the adaptive processing panel JS to measure server response time.
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/ping", methods=["HEAD", "GET"])
def ping():
    from flask import Response
    return Response(status=204)
