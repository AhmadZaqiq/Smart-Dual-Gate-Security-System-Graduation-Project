from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from flask import session

from web_dashboard.auth.decorators import login_required
from web_dashboard.config import Config
from web_dashboard.forms.security_resolve_form import SecurityResolveForm
from web_dashboard.services import security_service

security_bp = Blueprint("security", __name__, url_prefix="/security-events")


@security_bp.route("/")
@login_required
def list_events():
    page = request.args.get("page", 1, type=int)

    result = security_service.list_security_events(
        page=page,
        per_page=Config.DEFAULT_PAGE_SIZE,
        severity=request.args.get("severity") or None,
        event_type=request.args.get("type") or None,
        resolved=_parse_resolved_filter(request.args.get("resolved")),
        search_text=request.args.get("q"),
    )

    return render_template(
        "security/list.html",
        events=result["items"],
        pagination=result["pagination"],
        filters={
            "severity": request.args.get("severity") or "",
            "type": request.args.get("type") or "",
            "resolved": request.args.get("resolved") or "",
            "q": request.args.get("q") or "",
        },
    )


@security_bp.route("/timeline")
@login_required
def timeline():
    result = security_service.list_security_events(page=1, per_page=100)
    return render_template("security/timeline.html", events=result["items"])


@security_bp.route("/<int:event_id>")
@login_required
def event_detail(event_id):
    event = security_service.get_security_event_detail(event_id)

    if not event:
        abort(404)

    form = SecurityResolveForm()

    return render_template("security/detail.html", event=event, form=form)


@security_bp.route("/<int:event_id>/resolve", methods=["POST"])
@login_required
def resolve_event(event_id):
    form = SecurityResolveForm()

    if form.validate_on_submit():
        success = security_service.resolve_event(
            event_id,
            session["admin_id"],
            form.notes.data,
        )

        if success:
            flash("Security event marked as resolved.", "success")
        else:
            flash("Unable to resolve security event.", "danger")

    return redirect(url_for("security.event_detail", event_id=event_id))


def _parse_resolved_filter(value):
    if value == "1":
        return True
    if value == "0":
        return False
    return None
