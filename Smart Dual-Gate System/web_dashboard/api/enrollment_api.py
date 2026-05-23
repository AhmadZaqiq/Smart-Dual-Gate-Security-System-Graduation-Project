from flask import Blueprint

from web_dashboard.auth.decorators import login_required
from web_dashboard.services import enrollment_service
from web_dashboard.utils.response_helpers import json_success

enrollment_api_bp = Blueprint("api_enrollment", __name__, url_prefix="/api/enrollment")


@enrollment_api_bp.route("/rfid/start", methods=["POST"])
@login_required
def start_rfid():
    ok, message = enrollment_service.start_rfid_enrollment()
    return json_success({"success": ok, "message": message})


@enrollment_api_bp.route("/fingerprint/start", methods=["POST"])
@login_required
def start_fingerprint():
    ok, message = enrollment_service.start_fingerprint_enrollment()
    return json_success({"success": ok, "message": message})


@enrollment_api_bp.route("/cancel", methods=["POST"])
@login_required
def cancel():
    ok, message = enrollment_service.cancel_enrollment()
    return json_success({"success": ok, "message": message})


@enrollment_api_bp.route("/status")
@login_required
def status():
    return json_success(enrollment_service.get_enrollment_status())
