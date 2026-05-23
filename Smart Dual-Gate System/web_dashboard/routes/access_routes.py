from flask import Blueprint, abort, render_template, request

from web_dashboard.auth.decorators import login_required
from web_dashboard.config import Config
from web_dashboard.services import access_service

access_bp = Blueprint("access", __name__, url_prefix="/access-sessions")


@access_bp.route("/")
@login_required
def list_sessions():
    page = request.args.get("page", 1, type=int)
    final_status = request.args.get("status") or None
    search_text = request.args.get("q")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    result = access_service.list_access_sessions(
        page=page,
        per_page=Config.DEFAULT_PAGE_SIZE,
        final_status=final_status,
        search_text=search_text,
        date_from=date_from,
        date_to=date_to,
    )

    return render_template(
        "access/list.html",
        sessions=result["items"],
        pagination=result["pagination"],
        filters={
            "status": final_status or "",
            "q": search_text or "",
            "date_from": date_from or "",
            "date_to": date_to or "",
        },
    )


@access_bp.route("/<int:session_id>")
@login_required
def session_detail(session_id):
    detail = access_service.get_access_session_detail(session_id)

    if not detail:
        abort(404)

    return render_template(
        "access/detail.html",
        session=detail["session"],
        attempts=detail["attempts"],
    )
