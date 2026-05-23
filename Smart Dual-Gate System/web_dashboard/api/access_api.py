from flask import Blueprint, request

from web_dashboard.auth.decorators import login_required
from web_dashboard.config import Config
from web_dashboard.services import access_service
from web_dashboard.utils.response_helpers import json_error, json_success

access_api_bp = Blueprint("api_access", __name__, url_prefix="/api/access-sessions")


@access_api_bp.route("/")
@login_required
def list_sessions():
    result = access_service.list_access_sessions(
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("limit", Config.DEFAULT_PAGE_SIZE, type=int),
        final_status=request.args.get("status") or None,
        search_text=request.args.get("q"),
        date_from=request.args.get("date_from"),
        date_to=request.args.get("date_to"),
    )
    return json_success(result)


@access_api_bp.route("/<int:session_id>")
@login_required
def session_detail(session_id):
    detail = access_service.get_access_session_detail(session_id)

    if not detail:
        return json_error("Access session not found.", 404)

    return json_success(detail)
