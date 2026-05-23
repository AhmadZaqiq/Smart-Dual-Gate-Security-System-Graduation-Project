from flask import Blueprint, request

from web_dashboard.auth.decorators import login_required
from web_dashboard.config import Config
from web_dashboard.services import auth_attempts_service
from web_dashboard.utils.response_helpers import json_error, json_success

auth_attempts_api_bp = Blueprint("api_auth_attempts", __name__, url_prefix="/api/auth-attempts")


@auth_attempts_api_bp.route("/")
@login_required
def list_attempts():
    result = auth_attempts_service.list_authentication_attempts(
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("limit", Config.DEFAULT_PAGE_SIZE, type=int),
        final_result=request.args.get("result") or None,
        search_text=request.args.get("q"),
        employee_id=request.args.get("employee_id", type=int),
    )
    return json_success(result)


@auth_attempts_api_bp.route("/<int:attempt_id>")
@login_required
def attempt_detail(attempt_id):
    attempt = auth_attempts_service.get_authentication_attempt_detail(attempt_id)

    if not attempt:
        return json_error("Authentication attempt not found.", 404)

    return json_success(attempt)
