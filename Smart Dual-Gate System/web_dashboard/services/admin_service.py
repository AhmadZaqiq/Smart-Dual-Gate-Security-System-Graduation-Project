from web_dashboard.auth.password_utils import hash_password
from web_dashboard.utils.path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from database.admin_repository import (  # noqa: E402
    create_admin_user,
    get_admin_by_code,
    get_admin_by_email,
    get_admin_by_id,
    get_admin_by_username,
    get_all_admin_users,
    set_admin_active_status,
    update_admin_password,
    update_admin_user,
)
from database.audit_repository import create_audit  # noqa: E402
from database.database_manager import execute_non_query  # noqa: E402
from database.person_repository import create_person  # noqa: E402


def get_admin_role(admin_id):
    return "Admin"


def is_super_admin(admin_id):
    return admin_id is not None


def list_admins():
    return get_all_admin_users()


def validate_admin_code(admin_code):
    admin_code = (admin_code or "").strip()

    if not admin_code:
        return False, "Admin ID is required."

    if not admin_code.isdigit():
        return False, "Admin ID must contain numbers only."

    return True, admin_code


def _normalize_text(value):
    return (value or "").strip()


def _validate_password(password, confirm_password, required=True):
    if required and not password:
        return False, "Password is required."

    if password and len(password) < 8:
        return False, "Password must be at least 8 characters."

    if password != confirm_password:
        return False, "Password confirmation does not match."

    return True, None


def create_admin(actor_id, form_data):
    admin_code = _normalize_text(form_data.get("admin_code"))
    first_name = _normalize_text(form_data.get("first_name"))
    last_name = _normalize_text(form_data.get("last_name"))
    username = _normalize_text(form_data.get("username"))
    email = _normalize_text(form_data.get("email"))
    password = form_data.get("password") or ""
    confirm_password = form_data.get("confirm_password") or ""
    is_active = 1 if form_data.get("is_active") else 0

    is_valid, result = validate_admin_code(admin_code)
    if not is_valid:
        return None, result

    admin_code = result

    if not first_name:
        return None, "First name is required."

    if not last_name:
        return None, "Last name is required."

    if not username:
        return None, "Username is required."

    if get_admin_by_code(admin_code):
        return None, "Admin ID already exists."

    if get_admin_by_username(username):
        return None, "Username already exists."

    if email and get_admin_by_email(email):
        return None, "Email already exists."

    password_valid, password_error = _validate_password(password, confirm_password, required=True)
    if not password_valid:
        return None, password_error

    person_id = create_person(first_name, "Admin", "User", last_name)

    if not person_id:
        return None, "Failed to create person record."

    admin_id = create_admin_user(
        admin_code=admin_code,
        person_id=person_id,
        username=username,
        email=email or None,
        password_hash=hash_password(password),
        is_active=is_active,
    )

    if not admin_id:
        return None, "Failed to create admin account."

    create_audit(
        admin_user_id=actor_id,
        action_type="CREATE_ADMIN",
        table_name="AdminUser",
        record_id=admin_id,
        description=f"Admin account {username} created.",
    )

    return admin_id, None


def update_admin(actor_id, admin_id, form_data):
    admin = get_admin_by_id(admin_id)

    if not admin:
        return False, "Admin not found."

    admin_code = _normalize_text(form_data.get("admin_code"))
    first_name = _normalize_text(form_data.get("first_name"))
    last_name = _normalize_text(form_data.get("last_name"))
    username = _normalize_text(form_data.get("username"))
    email = _normalize_text(form_data.get("email"))
    is_active = 1 if form_data.get("is_active") else 0

    is_valid, result = validate_admin_code(admin_code)
    if not is_valid:
        return False, result

    admin_code = result

    if not first_name:
        return False, "First name is required."

    if not last_name:
        return False, "Last name is required."

    if not username:
        return False, "Username is required."

    existing_code = get_admin_by_code(admin_code)
    if existing_code and existing_code["AdminUserID"] != admin_id:
        return False, "Admin ID already exists."

    existing_username = get_admin_by_username(username)
    if existing_username and existing_username["AdminUserID"] != admin_id:
        return False, "Username already exists."

    if email:
        existing_email = get_admin_by_email(email)
        if existing_email and existing_email["AdminUserID"] != admin_id:
            return False, "Email already exists."

    execute_non_query(
        """
        UPDATE Person
        SET
            FirstName = ?,
            SecondName = 'Admin',
            ThirdName = 'User',
            LastName = ?,
            LastUpdatedDate = datetime('now')
        WHERE PersonID = ?
          AND IsDeleted = 0;
        """,
        (first_name, last_name, admin["PersonID"]),
    )

    success = update_admin_user(
        admin_user_id=admin_id,
        admin_code=admin_code,
        username=username,
        email=email or None,
        is_active=is_active,
    )

    if not success:
        return False, "Failed to update admin account."

    create_audit(
        admin_user_id=actor_id,
        action_type="UPDATE_ADMIN",
        table_name="AdminUser",
        record_id=admin_id,
        description=f"Admin account {username} updated.",
    )

    return True, None


def reset_admin_password(actor_id, admin_id, new_password, confirm_password):
    admin = get_admin_by_id(admin_id)

    if not admin:
        return False, "Admin not found."

    password_valid, password_error = _validate_password(
        new_password,
        confirm_password,
        required=True,
    )

    if not password_valid:
        return False, password_error

    success = update_admin_password(admin_id, hash_password(new_password))

    if success:
        create_audit(
            admin_user_id=actor_id,
            action_type="RESET_ADMIN_PASSWORD",
            table_name="AdminUser",
            record_id=admin_id,
            description=f"Password reset for admin {admin['UserName']}.",
        )

    return success, None if success else "Failed to reset password."


def change_admin_status(actor_id, admin_id, is_active):
    admin = get_admin_by_id(admin_id)

    if not admin:
        return False, "Admin not found."

    success = set_admin_active_status(admin_id, 1 if is_active else 0)

    if success:
        create_audit(
            admin_user_id=actor_id,
            action_type="UPDATE_ADMIN_STATUS",
            table_name="AdminUser",
            record_id=admin_id,
            new_value="1" if is_active else "0",
            description=f"Admin {admin['UserName']} set to {'Active' if is_active else 'Inactive'}.",
        )

    return success, None if success else "Failed to update admin status."
