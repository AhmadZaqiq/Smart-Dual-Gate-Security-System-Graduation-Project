from flask import Blueprint, render_template, request

from web_dashboard.auth.decorators import login_required
from web_dashboard.config import Config
from web_dashboard.services import logs_service

logs_bp = Blueprint("logs", __name__, url_prefix="/logs")


@logs_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)

    result = logs_service.list_logs(
        page=page,
        per_page=50,
        level=request.args.get("level") or None,
        search_text=request.args.get("q"),
    )

    return render_template(
        "logs/index.html",
        logs=result["items"],
        pagination=result["pagination"],
        filters={
            "level": request.args.get("level") or "",
            "q": request.args.get("q") or "",
        },
    )
