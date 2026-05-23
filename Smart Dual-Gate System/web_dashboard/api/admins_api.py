from flask import Blueprint, request, session

from web_dashboard.auth.decorators import login_required
from web_dashboard.auth.role_decorators import super_admin_required
from web_dashboard.services import admin_service
from web_dashboard.utils.response_helpers import json_error, json_success

admins_api_bp = Blueprint("api_admins", __name__, url_prefix="/api/admins")


@admins_api_bp.route("/")
@login_required
@super_admin_required
def list_admins():
    from web_dashboard.services.admin_service import _fetch_admins
    return json_success(_fetch_admins())


@admins_api_bp.route("/", methods=["POST"])
@login_required
@super_admin_required
def create_admin():
    payload = request.get_json() or {}
    admin_id, error = admin_service.create_admin(
        session["admin_id"],
        payload.get("username", "").strip(),
        payload.get("email", "").strip(),
        payload.get("password", ""),
        payload.get("role", admin_service.ROLE_OPERATOR),
        payload.get("first_name", "Admin"),
        payload.get("last_name", "User"),
    )

    if error:
        return json_error(error, 400)

    return json_success({"admin_id": admin_id})


@admins_api_bp.route("/<int:admin_id>", methods=["PUT"])
@login_required
@super_admin_required
def update_admin(admin_id):
    payload = request.get_json() or {}
    success, error = admin_service.update_admin(
        session["admin_id"],
        admin_id,
        payload.get("email"),
        payload.get("role", admin_service.ROLE_OPERATOR),
        1 if payload.get("is_active", True) else 0,
    )

    if not success:
        return json_error(error or "Update failed.", 400)

    return json_success({"updated": True})


@admins_api_bp.route("/<int:admin_id>/reset-password", methods=["POST"])
@login_required
@super_admin_required
def reset_password(admin_id):
    payload = request.get_json() or {}
    success, error = admin_service.reset_admin_password(
        session["admin_id"],
        admin_id,
        payload.get("password", ""),
    )

    if not success:
        return json_error(error or "Password reset failed.", 400)

    return json_success({"reset": True})
