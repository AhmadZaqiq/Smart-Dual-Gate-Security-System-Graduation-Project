from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from web_dashboard.auth.decorators import login_required
from web_dashboard.auth.role_decorators import super_admin_required
from web_dashboard.services import admin_service

admins_bp = Blueprint("admins", __name__, url_prefix="/admins")


@admins_bp.route("/")
@login_required
@super_admin_required
def list_admins():
    from web_dashboard.services.admin_service import _fetch_admins

    return render_template("admins/list.html", admins=_fetch_admins())


@admins_bp.route("/new", methods=["GET", "POST"])
@login_required
@super_admin_required
def new_admin():
    if request.method == "POST":
        admin_id, error = admin_service.create_admin(
            session["admin_id"],
            request.form.get("username", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("password", ""),
            request.form.get("role", admin_service.ROLE_OPERATOR),
            request.form.get("first_name", "Admin"),
            request.form.get("last_name", "User"),
        )

        if admin_id:
            flash("Admin account created.", "success")
            return redirect(url_for("admins.list_admins"))

        flash(error or "Failed to create admin.", "danger")

    return render_template("admins/form.html", title="Add Admin")


@admins_bp.route("/<int:admin_id>/edit", methods=["GET", "POST"])
@login_required
@super_admin_required
def edit_admin(admin_id):
    from database.admin_repository import get_admin_by_id
    from database.database_manager import execute_query_one

    admin = get_admin_by_id(admin_id)

    if not admin:
        from flask import abort
        abort(404)

    person = execute_query_one(
        "SELECT FirstName, LastName FROM Person WHERE PersonID = ?;",
        (admin["PersonID"],),
    )

    admin_view = {
        **admin,
        "FirstName": person["FirstName"] if person else "Admin",
        "LastName": person["LastName"] if person else "User",
    }

    if request.method == "POST":
        success, error = admin_service.update_admin(
            session["admin_id"],
            admin_id,
            request.form.get("email", "").strip(),
            request.form.get("role", admin_service.ROLE_OPERATOR),
            1 if request.form.get("is_active") == "1" else 0,
        )

        new_password = request.form.get("new_password", "").strip()
        if new_password:
            reset_ok, reset_error = admin_service.reset_admin_password(
                session["admin_id"],
                admin_id,
                new_password,
            )
            if not reset_ok:
                flash(reset_error or "Password reset failed.", "danger")
                return render_template("admins/form.html", title="Edit Admin", admin=admin_view)

        if success:
            flash("Admin account updated.", "success")
            return redirect(url_for("admins.list_admins"))

        flash(error or "Failed to update admin.", "danger")

    return render_template("admins/form.html", title="Edit Admin", admin=admin_view)
