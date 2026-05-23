from flask import Blueprint, request

from web_dashboard.auth.decorators import login_required
from web_dashboard.services import dashboard_service
from web_dashboard.utils.response_helpers import json_success

dashboard_api_bp = Blueprint("api_dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_api_bp.route("/summary")
@login_required
def summary():
    return json_success(dashboard_service.get_overview_summary())


@dashboard_api_bp.route("/activity")
@login_required
def activity():
    limit = request.args.get("limit", 20, type=int)
    return json_success(dashboard_service.get_recent_activity(limit))


@dashboard_api_bp.route("/recent-access")
@login_required
def recent_access():
    limit = request.args.get("limit", 5, type=int)
    return json_success(dashboard_service.get_recent_access(limit))


@dashboard_api_bp.route("/recent-security")
@login_required
def recent_security():
    limit = request.args.get("limit", 5, type=int)
    return json_success(dashboard_service.get_recent_security(limit))


@dashboard_api_bp.route("/charts/access")
@login_required
def access_chart():
    days = request.args.get("days", 7, type=int)
    return json_success(dashboard_service.get_access_chart(days))


@dashboard_api_bp.route("/charts/security")
@login_required
def security_chart():
    days = request.args.get("days", 7, type=int)
    return json_success(dashboard_service.get_security_chart(days))
