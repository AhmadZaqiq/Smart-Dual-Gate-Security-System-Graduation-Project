from flask import Blueprint, session

from web_dashboard.auth.decorators import login_required
from web_dashboard.services import process_control_service, system_status_service, workflow_service
from web_dashboard.utils.response_helpers import json_error, json_success

system_api_bp = Blueprint("api_system", __name__, url_prefix="/api/system")


@system_api_bp.route("/status")
@login_required
def status():
    data = system_status_service.get_system_status()
    data["workflow"] = workflow_service.get_workflow_view(data)
    return json_success(data)


@system_api_bp.route("/workflow")
@login_required
def workflow():
    status_data = system_status_service.get_system_status()
    return json_success(workflow_service.get_workflow_view(status_data))


@system_api_bp.route("/health")
@login_required
def health():
    return json_success(system_status_service.get_health_report())


@system_api_bp.route("/process-status")
@login_required
def process_status():
    return json_success(process_control_service.get_process_status())


@system_api_bp.route("/start", methods=["POST"])
@login_required
def start_system():
    success, message = process_control_service.start_system(session["admin_id"])

    if not success:
        return json_error(message, 400)

    return json_success({
        "message": message,
        "process": process_control_service.get_process_status(),
    })


@system_api_bp.route("/stop", methods=["POST"])
@login_required
def stop_system():
    success, message = process_control_service.stop_system(session["admin_id"])

    if not success:
        return json_error(message, 400)

    return json_success({
        "message": message,
        "process": process_control_service.get_process_status(),
    })
