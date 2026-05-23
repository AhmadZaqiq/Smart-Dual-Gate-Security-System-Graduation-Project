from flask import Blueprint, request, session

from web_dashboard.auth.decorators import login_required
from web_dashboard.services import settings_service
from web_dashboard.utils.response_helpers import json_error, json_success

settings_api_bp = Blueprint("api_settings", __name__, url_prefix="/api/settings")


@settings_api_bp.route("/")
@login_required
def get_settings():
    return json_success(settings_service.get_settings_for_display())


@settings_api_bp.route("/", methods=["PUT"])
@login_required
def update_settings():
    payload = request.get_json() or {}

    if not payload:
        return json_error("No settings provided.", 400)

    updated, errors = settings_service.update_settings(session["admin_id"], payload)

    return json_success({"updated": updated, "errors": errors})
