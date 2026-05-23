from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from web_dashboard.auth.decorators import login_required
from web_dashboard.forms.settings_form import SettingsForm
from web_dashboard.services import settings_service

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = SettingsForm()
    settings_data = settings_service.get_settings_for_display()

    if request.method == "POST" and form.validate_on_submit():
        payload = {}

        for key in request.form:
            if key in ("csrf_token", "submit"):
                continue

            if key.startswith("REQUIRE_"):
                payload[key] = "1" if request.form.get(key) else "0"
            else:
                payload[key] = request.form.get(key)

        updated, errors = settings_service.update_settings(session["admin_id"], payload)

        if updated:
            flash(f"Updated {len(updated)} setting(s).", "success")

        for error in errors:
            flash(error, "danger")

        return redirect(url_for("settings.index"))

    return render_template(
        "settings/index.html",
        form=form,
        settings_data=settings_data,
    )
