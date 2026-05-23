"""Admin management service with role-based access."""

import os

from web_dashboard.auth.password_utils import hash_password
from web_dashboard.utils.path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from database.admin_repository import (  # noqa: E402
    create_admin_user,
    get_admin_by_id,
    get_admin_by_username,
    get_all_admin_users,
    update_admin_password,
    update_admin_user,
)
from database.audit_repository import create_audit  # noqa: E402
from database.database_manager import execute_non_query, execute_query_one  # noqa: E402
from database.person_repository import create_person  # noqa: E402

ROLE_SUPER = "Super Admin"
ROLE_OPERATOR = "Operator"


def get_admin_role(admin_id):
    row = execute_query_one(
        "SELECT Role FROM AdminUser WHERE AdminUserID = ?;",
        (admin_id,),
    )
    return row["Role"] if row and row.get("Role") else ROLE_OPERATOR


def is_super_admin(admin_id):
    return get_admin_role(admin_id) == ROLE_SUPER


def list_admins():
    return execute_query_one(
        """
        SELECT COUNT(*) AS Total FROM AdminUser WHERE IsDeleted = 0;
        """
    ), _fetch_admins()


def _fetch_admins():
    from database.database_manager import execute_query

    return execute_query(
        """
        SELECT
            A.AdminUserID,
            A.UserName,
            A.Email,
            A.Role,
            A.IsActive,
            A.LastLoginDate,
            P.FirstName || ' ' || P.LastName AS FullName
        FROM AdminUser A
        INNER JOIN Person P ON P.PersonID = A.PersonID
        WHERE A.IsDeleted = 0
        ORDER BY A.AdminUserID;
        """
    )


def create_admin(actor_id, username, email, password, role, first_name, last_name):
    if not is_super_admin(actor_id):
        return None, "Only Super Admin can create admin accounts."

    if get_admin_by_username(username):
        return None, "Username already exists."

    person_id = create_person(first_name, "Admin", "User", last_name)
    admin_id = create_admin_user(person_id, username, email, hash_password(password), 1)

    if admin_id:
        execute_non_query(
            "UPDATE AdminUser SET Role = ? WHERE AdminUserID = ?;",
            (role, admin_id),
        )
        create_audit(
            admin_user_id=actor_id,
            action_type="CREATE_ADMIN",
            table_name="AdminUser",
            record_id=admin_id,
            description=f"Created admin account {username}.",
        )

    return admin_id, None


def update_admin(actor_id, admin_id, email, role, is_active):
    if not is_super_admin(actor_id):
        return False, "Only Super Admin can edit admin accounts."

    admin = get_admin_by_id(admin_id)
    if not admin:
        return False, "Admin not found."

    update_admin_user(admin_id, admin["UserName"], email, is_active)
    execute_non_query(
        "UPDATE AdminUser SET Role = ? WHERE AdminUserID = ?;",
        (role, admin_id),
    )

    create_audit(
        admin_user_id=actor_id,
        action_type="UPDATE_ADMIN",
        table_name="AdminUser",
        record_id=admin_id,
        description=f"Updated admin account {admin['UserName']}.",
    )
    return True, None


def reset_admin_password(actor_id, admin_id, new_password):
    if not is_super_admin(actor_id):
        return False, "Only Super Admin can reset passwords."

    success = update_admin_password(admin_id, hash_password(new_password))

    if success:
        create_audit(
            admin_user_id=actor_id,
            action_type="RESET_ADMIN_PASSWORD",
            table_name="AdminUser",
            record_id=admin_id,
            description="Admin password reset.",
        )

    return success, None
