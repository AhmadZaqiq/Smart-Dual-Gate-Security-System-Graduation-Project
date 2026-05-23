from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from web_dashboard.auth.decorators import login_required
from web_dashboard.services import admin_service

admins_bp = Blueprint("admins", __name__, url_prefix="/admins")


@admins_bp.route("/")
@login_required
def list_admins():
    admins = admin_service.list_admins()
    return render_template("admins/list.html", admins=admins)


@admins_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_admin():
    if request.method == "POST":
        admin_id, error = admin_service.create_admin(
            session["admin_id"],
            request.form,
        )

        if error:
            flash(error, "danger")
            return render_template("admins/form.html", admin=None, mode="new")

        flash("Admin account created successfully.", "success")
        return redirect(url_for("admins.list_admins"))

    return render_template("admins/form.html", admin=None, mode="new")


@admins_bp.route("/<int:admin_id>/edit", methods=["GET", "POST"])
@login_required
def edit_admin(admin_id):
    admin = admin_service.get_admin_by_id(admin_id)

    if not admin:
        flash("Admin not found.", "danger")
        return redirect(url_for("admins.list_admins"))

    if request.method == "POST":
        success, error = admin_service.update_admin(
            session["admin_id"],
            admin_id,
            request.form,
        )

        if error:
            flash(error, "danger")
            admin = admin_service.get_admin_by_id(admin_id)
            return render_template("admins/form.html", admin=admin, mode="edit")

        flash("Admin account updated successfully.", "success")
        return redirect(url_for("admins.list_admins"))

    return render_template("admins/form.html", admin=admin, mode="edit")


@admins_bp.route("/<int:admin_id>/reset-password", methods=["GET", "POST"])
@login_required
def reset_password(admin_id):
    admin = admin_service.get_admin_by_id(admin_id)

    if not admin:
        flash("Admin not found.", "danger")
        return redirect(url_for("admins.list_admins"))

    if request.method == "POST":
        success, error = admin_service.reset_admin_password(
            session["admin_id"],
            admin_id,
            request.form.get("password") or "",
            request.form.get("confirm_password") or "",
        )

        if error:
            flash(error, "danger")
            return render_template("admins/reset_password.html", admin=admin)

        flash("Admin password reset successfully.", "success")
        return redirect(url_for("admins.list_admins"))

    return render_template("admins/reset_password.html", admin=admin)


@admins_bp.route("/<int:admin_id>/toggle", methods=["POST"])
@login_required
def toggle_admin(admin_id):
    admin = admin_service.get_admin_by_id(admin_id)

    if not admin:
        flash("Admin not found.", "danger")
        return redirect(url_for("admins.list_admins"))

    next_status = 0 if admin["IsActive"] else 1

    success, error = admin_service.change_admin_status(
        session["admin_id"],
        admin_id,
        next_status,
    )

    if error:
        flash(error, "danger")
    else:
        flash("Admin status updated successfully.", "success")

    return redirect(url_for("admins.list_admins"))
