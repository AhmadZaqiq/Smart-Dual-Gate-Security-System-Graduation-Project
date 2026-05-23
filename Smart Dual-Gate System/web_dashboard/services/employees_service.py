from web_dashboard.utils.path_setup import ensure_project_root_on_path
from web_dashboard.utils.validators import sanitize_search_text

ensure_project_root_on_path()

from database.audit_repository import create_audit  # noqa: E402
from database.employee_auth_repository import (  # noqa: E402
    create_employee_authentication,
    get_authentication_by_employee_id,
    update_face_image_path,
    update_fingerprint_position,
    update_rfid_uid,
)
from database.employee_repository import (  # noqa: E402
    create_employee,
    get_all_employees,
    get_employee_by_id,
    search_employees,
    update_employee,
)
from database.person_repository import create_person, get_person_by_id  # noqa: E402


def list_employees(search_text=None):
    search_text = sanitize_search_text(search_text)

    if search_text:
        return search_employees(search_text)

    return get_all_employees()


def get_employee_detail(employee_id):
    employee = get_employee_by_id(employee_id)

    if not employee:
        return None

    auth_info = get_authentication_by_employee_id(employee_id)
    person = get_person_by_id(employee["PersonID"])

    return {
        "employee": employee,
        "person": person,
        "authentication": auth_info,
    }


def create_employee_record(admin_user_id, form_data):
    person_id = create_person(
        form_data["first_name"],
        form_data["second_name"],
        form_data["third_name"],
        form_data["last_name"],
    )

    if not person_id:
        return None, "Failed to create person record."

    employee_id = create_employee(form_data["employee_number"], person_id)

    if not employee_id:
        return None, "Failed to create employee record."

    create_employee_authentication(
        employee_id=employee_id,
        rfid_uid=form_data.get("rfid_uid"),
        fingerprint_position=form_data.get("fingerprint_position"),
        face_image_path=form_data.get("face_image_path"),
    )

    create_audit(
        admin_user_id=admin_user_id,
        action_type="CREATE_EMPLOYEE",
        table_name="Employee",
        record_id=employee_id,
        description=f"Employee {form_data['employee_number']} created.",
    )

    return employee_id, None


def update_employee_record(admin_user_id, employee_id, form_data):
    success = update_employee(
        employee_id,
        form_data["employee_number"],
        form_data.get("is_active", 1),
    )

    if not success:
        return False, "Employee update failed."

    if form_data.get("rfid_uid") is not None:
        update_rfid_uid(employee_id, form_data["rfid_uid"])

    if form_data.get("fingerprint_position") is not None:
        update_fingerprint_position(employee_id, form_data["fingerprint_position"])

    if form_data.get("face_image_path") is not None:
        update_face_image_path(employee_id, form_data["face_image_path"])

    create_audit(
        admin_user_id=admin_user_id,
        action_type="UPDATE_EMPLOYEE",
        table_name="Employee",
        record_id=employee_id,
        description=f"Employee {employee_id} updated.",
    )

    return True, None
