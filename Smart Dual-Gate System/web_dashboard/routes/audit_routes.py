from flask import Blueprint, render_template, request

from web_dashboard.auth.decorators import login_required
from web_dashboard.config import Config
from web_dashboard.services import audit_service

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


@audit_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)

    result = audit_service.list_audits(
        page=page,
        per_page=Config.DEFAULT_PAGE_SIZE,
        search_text=request.args.get("q"),
        table_name=request.args.get("table") or None,
        action_type=request.args.get("action") or None,
    )

    return render_template(
        "audit/index.html",
        audits=result["items"],
        pagination=result["pagination"],
        filters={
            "q": request.args.get("q") or "",
            "table": request.args.get("table") or "",
            "action": request.args.get("action") or "",
        },
    )
