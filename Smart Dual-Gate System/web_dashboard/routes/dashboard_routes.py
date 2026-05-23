from flask import Blueprint, render_template

from web_dashboard.auth.decorators import login_required
from web_dashboard.config import Config
from web_dashboard.services import dashboard_service

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    summary = dashboard_service.get_overview_summary()
    recent_access = dashboard_service.get_recent_access(5)
    recent_security = dashboard_service.get_recent_security(5)
    recent_activity = dashboard_service.get_recent_activity(10)

    return render_template(
        "dashboard/index.html",
        summary=summary,
        recent_access=recent_access,
        recent_security=recent_security,
        recent_activity=recent_activity,
        stream_url=Config.YOLO_STREAM_BASE_URL,
    )
