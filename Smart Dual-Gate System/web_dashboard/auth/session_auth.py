import time
from collections import defaultdict

from flask import session

from web_dashboard.auth.password_utils import verify_password
from web_dashboard.utils.path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from database.admin_repository import get_admin_by_username  # noqa: E402
from database.database_manager import execute_non_query  # noqa: E402
from web_dashboard.services.admin_service import get_admin_role  # noqa: E402

LOGIN_ATTEMPTS = defaultdict(list)
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 900


def _is_rate_limited(client_ip):
    now = time.time()
    attempts = LOGIN_ATTEMPTS[client_ip]
    LOGIN_ATTEMPTS[client_ip] = [
        attempt_time for attempt_time in attempts
        if now - attempt_time < WINDOW_SECONDS
    ]

    return len(LOGIN_ATTEMPTS[client_ip]) >= MAX_ATTEMPTS


def _record_failed_attempt(client_ip):
    LOGIN_ATTEMPTS[client_ip].append(time.time())


def authenticate_admin(username, password, client_ip):
    if _is_rate_limited(client_ip):
        return None, "Too many login attempts. Please try again later."

    admin = get_admin_by_username(username)

    if not admin or not admin.get("IsActive"):
        _record_failed_attempt(client_ip)
        return None, "Invalid username or password."

    if not verify_password(password, admin["PasswordHash"]):
        _record_failed_attempt(client_ip)
        return None, "Invalid username or password."

    execute_non_query(
        """
        UPDATE AdminUser
        SET LastLoginDate = datetime('now')
        WHERE AdminUserID = ?;
        """,
        (admin["AdminUserID"],),
    )

    LOGIN_ATTEMPTS[client_ip] = []

    return admin, None


def _build_display_name(admin):
    full_name = admin.get("FullName")

    if full_name:
        return full_name.strip()

    return admin.get("UserName", "Admin").title()


def _build_initials(display_name):
    parts = [part for part in display_name.split() if part]

    if not parts:
        return "AD"

    if len(parts) == 1:
        return parts[0][:2].upper()

    return (parts[0][0] + parts[-1][0]).upper()


def login_admin(admin, remember=False):
    display_name = _build_display_name(admin)

    session.clear()
    session["admin_id"] = admin["AdminUserID"]
    session["username"] = admin["UserName"]
    session["display_name"] = display_name
    session["initials"] = _build_initials(display_name)
    session["role_label"] = get_admin_role(admin["AdminUserID"])
    session.permanent = remember


def logout_admin():
    session.clear()
