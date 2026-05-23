from flask import Blueprint, request, session

from web_dashboard.auth.decorators import login_required
from web_dashboard.config import Config
from web_dashboard.services import security_service
from web_dashboard.utils.response_helpers import json_error, json_success

security_api_bp = Blueprint("api_security", __name__, url_prefix="/api/security-events")


@security_api_bp.route("/")
@login_required
def list_events():
    resolved = request.args.get("resolved")

    resolved_value = None
    if resolved == "1":
        resolved_value = True
    elif resolved == "0":
        resolved_value = False

    result = security_service.list_security_events(
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("limit", Config.DEFAULT_PAGE_SIZE, type=int),
        severity=request.args.get("severity") or None,
        event_type=request.args.get("type") or None,
        resolved=resolved_value,
        search_text=request.args.get("q"),
    )
    return json_success(result)


@security_api_bp.route("/<int:event_id>")
@login_required
def event_detail(event_id):
    event = security_service.get_security_event_detail(event_id)

    if not event:
        return json_error("Security event not found.", 404)

    return json_success(event)


@security_api_bp.route("/<int:event_id>/resolve", methods=["POST"])
@login_required
def resolve_event(event_id):
    notes = None

    if request.is_json:
        notes = (request.get_json() or {}).get("notes")

    success = security_service.resolve_event(event_id, session["admin_id"], notes)

    if not success:
        return json_error("Unable to resolve event.", 400)

    return json_success({"resolved": True})
