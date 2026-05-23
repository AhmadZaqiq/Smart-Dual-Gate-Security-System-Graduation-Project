from datetime import timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from web_dashboard.auth.decorators import login_required
from web_dashboard.auth.session_auth import authenticate_admin, login_admin, logout_admin
from web_dashboard.config import Config
from web_dashboard.forms.login_form import LoginForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if "admin_id" in session:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    error = None

    if form.validate_on_submit():
        admin, error = authenticate_admin(
            form.username.data.strip(),
            form.password.data,
            request.remote_addr or "unknown",
        )

        if admin:
            login_admin(admin, remember=form.remember.data)
            return redirect(url_for("dashboard.index"))

        error = error or "Invalid username or password."

    return render_template("auth/login.html", form=form, error=error)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_admin()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
