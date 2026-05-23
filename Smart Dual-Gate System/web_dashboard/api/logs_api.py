from flask import Blueprint, request

from web_dashboard.auth.decorators import login_required
from web_dashboard.services import logs_service
from web_dashboard.utils.response_helpers import json_success

logs_api_bp = Blueprint("api_logs", __name__, url_prefix="/api/logs")


@logs_api_bp.route("/")
@login_required
def list_logs():
    result = logs_service.list_logs(
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("limit", 50, type=int),
        level=request.args.get("level") or None,
        search_text=request.args.get("q"),
    )
    return json_success(result)


@logs_api_bp.route("/tail")
@login_required
def tail_logs():
    lines = request.args.get("lines", 100, type=int)
    return json_success(
        logs_service.tail_logs(
            lines=lines,
            level=request.args.get("level") or None,
            search_text=request.args.get("q"),
        )
    )
