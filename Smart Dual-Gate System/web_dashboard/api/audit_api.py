from flask import Blueprint, request

from web_dashboard.auth.decorators import login_required
from web_dashboard.config import Config
from web_dashboard.services import audit_service
from web_dashboard.utils.response_helpers import json_success

audit_api_bp = Blueprint("api_audit", __name__, url_prefix="/api/audit")


@audit_api_bp.route("/")
@login_required
def list_audits():
    result = audit_service.list_audits(
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("limit", Config.DEFAULT_PAGE_SIZE, type=int),
        search_text=request.args.get("q"),
        table_name=request.args.get("table") or None,
        action_type=request.args.get("action") or None,
    )
    return json_success(result)
