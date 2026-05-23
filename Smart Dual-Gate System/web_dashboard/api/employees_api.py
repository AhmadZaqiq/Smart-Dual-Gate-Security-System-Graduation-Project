from flask import Blueprint, request, session

from web_dashboard.auth.decorators import login_required
from web_dashboard.services import employees_service
from web_dashboard.utils.path_setup import ensure_project_root_on_path
from web_dashboard.utils.response_helpers import json_error, json_success

ensure_project_root_on_path()

from database.audit_repository import create_audit  # noqa: E402
from database.employee_repository import set_employee_active_status  # noqa: E402

employees_api_bp = Blueprint("api_employees", __name__, url_prefix="/api/employees")


@employees_api_bp.route("/")
@login_required
def list_employees():
    return json_success(employees_service.list_employees(request.args.get("q")))


@employees_api_bp.route("/<int:employee_id>")
@login_required
def employee_detail(employee_id):
    detail = employees_service.get_employee_detail(employee_id)

    if not detail:
        return json_error("Employee not found.", 404)

    return json_success(detail)


@employees_api_bp.route("/", methods=["POST"])
@login_required
def create_employee():
    payload = request.get_json() or {}

    employee_id, error = employees_service.create_employee_record(
        session["admin_id"],
        {
            "employee_number": (payload.get("employee_number") or "").strip(),
            "first_name": (payload.get("first_name") or "").strip(),
            "second_name": (payload.get("second_name") or "").strip(),
            "third_name": (payload.get("third_name") or "").strip(),
            "last_name": (payload.get("last_name") or "").strip(),
            "rfid_uid": payload.get("rfid_uid"),
            "fingerprint_position": payload.get("fingerprint_position"),
            "face_image_path": payload.get("face_image_path"),
        },
    )

    if not employee_id:
        return json_error(error or "Failed to create employee.", 400)

    return json_success({"employee_id": employee_id})


@employees_api_bp.route("/<int:employee_id>/active", methods=["PATCH"])
@login_required
def toggle_active(employee_id):
    payload = request.get_json() or {}
    is_active = 1 if payload.get("is_active") else 0

    success = set_employee_active_status(employee_id, is_active)

    if not success:
        return json_error("Unable to update employee status.", 400)

    create_audit(
        admin_user_id=session["admin_id"],
        action_type="UPDATE_EMPLOYEE_STATUS",
        table_name="Employee",
        record_id=employee_id,
        new_value=str(is_active),
        description=f"Employee {employee_id} set to {'Active' if is_active else 'Inactive'}.",
    )

    return json_success({"employee_id": employee_id, "is_active": is_active})
