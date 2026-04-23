"""
Authentication blueprint — /auth/login, /auth/logout
MongoDB replaced with in-memory USERS dict from auth_service.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from services.auth_service import User, authenticate_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Already logged in → go straight to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("login.html")

        # ── Validate against in-memory store (no MongoDB) ─────────────────
        user_doc, error = authenticate_user(email, password)
        if error:
            flash(error, "error")
            return render_template("login.html", email=email)

        user = User(user_doc)
        login_user(user, remember=True)

        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        flash(
            "Signup is currently disabled in demo mode. Please use the demo account to continue.",
            "info",
        )
        return render_template("signup.html", username=username, email=email)

    return render_template("signup.html")
