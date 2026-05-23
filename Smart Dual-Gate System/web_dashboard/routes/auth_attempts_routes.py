from flask import Blueprint, abort, render_template, request

from web_dashboard.auth.decorators import login_required
from web_dashboard.config import Config
from web_dashboard.services import auth_attempts_service

auth_attempts_bp = Blueprint("auth_attempts", __name__, url_prefix="/auth-attempts")


@auth_attempts_bp.route("/")
@login_required
def list_attempts():
    page = request.args.get("page", 1, type=int)
    final_result = request.args.get("result") or None
    search_text = request.args.get("q")

    result = auth_attempts_service.list_authentication_attempts(
        page=page,
        per_page=Config.DEFAULT_PAGE_SIZE,
        final_result=final_result,
        search_text=search_text,
    )

    return render_template(
        "auth_attempts/list.html",
        attempts=result["items"],
        pagination=result["pagination"],
        filters={"result": final_result or "", "q": search_text or ""},
    )


@auth_attempts_bp.route("/<int:attempt_id>")
@login_required
def attempt_detail(attempt_id):
    attempt = auth_attempts_service.get_authentication_attempt_detail(attempt_id)

    if not attempt:
        abort(404)

    return render_template("auth_attempts/detail.html", attempt=attempt)
