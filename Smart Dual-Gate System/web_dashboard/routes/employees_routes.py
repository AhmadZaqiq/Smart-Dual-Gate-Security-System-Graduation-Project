from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from web_dashboard.auth.decorators import login_required
from web_dashboard.forms.employee_form import EmployeeForm
from web_dashboard.services import employees_service

employees_bp = Blueprint("employees", __name__, url_prefix="/employees")


@employees_bp.route("/")
@login_required
def list_employees():
    employees = employees_service.list_employees(request.args.get("q"))
    return render_template(
        "employees/list.html",
        employees=employees,
        search_query=request.args.get("q") or "",
    )


@employees_bp.route("/<int:employee_id>")
@login_required
def employee_detail(employee_id):
    detail = employees_service.get_employee_detail(employee_id)

    if not detail:
        abort(404)

    return render_template("employees/detail.html", detail=detail)


@employees_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_employee():
    if request.method == "GET":
        return render_template("employees/wizard.html")

    form = EmployeeForm()

    if form.validate_on_submit():
        employee_id, error = employees_service.create_employee_record(
            session["admin_id"],
            {
                "employee_number": form.employee_number.data.strip(),
                "first_name": form.first_name.data.strip(),
                "second_name": form.second_name.data.strip(),
                "third_name": form.third_name.data.strip(),
                "last_name": form.last_name.data.strip(),
                "rfid_uid": form.rfid_uid.data.strip() if form.rfid_uid.data else None,
                "fingerprint_position": form.fingerprint_position.data,
                "face_image_path": form.face_image_path.data.strip() if form.face_image_path.data else None,
            },
        )

        if employee_id:
            flash("Employee created successfully.", "success")
            return redirect(url_for("employees.employee_detail", employee_id=employee_id))

        flash(error or "Failed to create employee.", "danger")

    return render_template("employees/form.html", form=form, title="Add Employee")


@employees_bp.route("/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    detail = employees_service.get_employee_detail(employee_id)

    if not detail:
        abort(404)

    form = EmployeeForm()

    if request.method == "GET":
        person = detail["person"] or {}
        auth_info = detail["authentication"] or {}
        employee = detail["employee"]

        form.employee_number.data = employee.get("EmployeeNumber")
        form.first_name.data = person.get("FirstName")
        form.second_name.data = person.get("SecondName")
        form.third_name.data = person.get("ThirdName")
        form.last_name.data = person.get("LastName")
        form.rfid_uid.data = auth_info.get("RFIDUID")
        form.fingerprint_position.data = auth_info.get("FingerprintPosition")
        form.face_image_path.data = auth_info.get("FaceImagePath")

    if form.validate_on_submit():
        success, error = employees_service.update_employee_record(
            session["admin_id"],
            employee_id,
            {
                "employee_number": form.employee_number.data.strip(),
                "is_active": detail["employee"].get("IsActive", 1),
                "rfid_uid": form.rfid_uid.data.strip() if form.rfid_uid.data else None,
                "fingerprint_position": form.fingerprint_position.data,
                "face_image_path": form.face_image_path.data.strip() if form.face_image_path.data else None,
            },
        )

        if success:
            flash("Employee updated successfully.", "success")
            return redirect(url_for("employees.employee_detail", employee_id=employee_id))

        flash(error or "Failed to update employee.", "danger")

    return render_template(
        "employees/form.html",
        form=form,
        title="Edit Employee",
        employee_id=employee_id,
    )


# ===== MANTRAP ENROLLMENT WIZARD API PATCH =====

import json as _enrollment_json
import sqlite3 as _enrollment_sqlite3
from datetime import datetime as _enrollment_datetime
from flask import jsonify as _enrollment_jsonify
from flask import request as _enrollment_request
from web_dashboard.config import Config as _EnrollmentConfig
from web_dashboard.services import enrollment_service as _enrollment_service


def _enrollment_get_database_path():
    for attr_name in ("DATABASE_PATH", "DB_PATH", "SQLITE_DATABASE_PATH"):
        db_path = getattr(_EnrollmentConfig, attr_name, None)
        if db_path:
            return db_path

    return _EnrollmentConfig.PROJECT_ROOT / "database" / "mantrap.db"


def _enrollment_table_exists(cursor, table_name):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _enrollment_get_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def _enrollment_insert_dynamic(cursor, table_name, values):
    columns = _enrollment_get_columns(cursor, table_name)
    allowed = {key: value for key, value in values.items() if key in columns}

    if not allowed:
        raise RuntimeError(f"No matching columns found for table {table_name}")

    column_sql = ", ".join(allowed.keys())
    placeholder_sql = ", ".join(["?"] * len(allowed))
    cursor.execute(
        f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholder_sql})",
        list(allowed.values()),
    )
    return cursor.lastrowid


def _enrollment_update_dynamic(cursor, table_name, key_column, key_value, values):
    columns = _enrollment_get_columns(cursor, table_name)
    allowed = {
        key: value
        for key, value in values.items()
        if key in columns and key != key_column
    }

    if not allowed:
        return

    set_sql = ", ".join([f"{key}=?" for key in allowed.keys()])
    params = list(allowed.values()) + [key_value]

    cursor.execute(
        f"UPDATE {table_name} SET {set_sql} WHERE {key_column}=?",
        params,
    )


def _enrollment_create_or_update_employee(payload):
    db_path = _enrollment_get_database_path()
    now = _enrollment_datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    employee_number = str(payload.get("employee_number", "")).strip()
    first_name = str(payload.get("first_name", "")).strip()
    second_name = str(payload.get("second_name", "")).strip()
    third_name = str(payload.get("third_name", "")).strip()
    last_name = str(payload.get("last_name", "")).strip()
    rfid_uid = str(payload.get("rfid_uid", "")).strip()
    face_image_path = str(payload.get("face_image_path", "")).strip()

    fingerprint_position = payload.get("fingerprint_position")
    if fingerprint_position in ("", None, "—"):
        fingerprint_position = None
    else:
        fingerprint_position = int(fingerprint_position)

    if not employee_number or not first_name or not last_name:
        return False, "Employee number, first name, and last name are required.", None

    full_name = " ".join(
        part for part in [first_name, second_name, third_name, last_name] if part
    )

    connection = _enrollment_sqlite3.connect(str(db_path))
    connection.row_factory = _enrollment_sqlite3.Row

    try:
        cursor = connection.cursor()

        if not _enrollment_table_exists(cursor, "Person"):
            return False, "Database table Person was not found.", None

        if not _enrollment_table_exists(cursor, "Employee"):
            return False, "Database table Employee was not found.", None

        if not _enrollment_table_exists(cursor, "EmployeeAuthentication"):
            return False, "Database table EmployeeAuthentication was not found.", None

        cursor.execute(
            "SELECT EmployeeID FROM Employee WHERE EmployeeNumber=?",
            (employee_number,),
        )
        existing_employee = cursor.fetchone()

        if existing_employee:
            employee_id = existing_employee["EmployeeID"]

            cursor.execute(
                "SELECT PersonID FROM Employee WHERE EmployeeID=?",
                (employee_id,),
            )
            employee_row = cursor.fetchone()
            person_id = employee_row["PersonID"] if employee_row and "PersonID" in employee_row.keys() else None

            if person_id:
                _enrollment_update_dynamic(
                    cursor,
                    "Person",
                    "PersonID",
                    person_id,
                    {
                        "FirstName": first_name,
                        "SecondName": second_name,
                        "ThirdName": third_name,
                        "LastName": last_name,
                        "FullName": full_name,
                        "ModifiedDate": now,
                        "UpdatedAt": now,
                    },
                )

            _enrollment_update_dynamic(
                cursor,
                "Employee",
                "EmployeeID",
                employee_id,
                {
                    "EmployeeNumber": employee_number,
                    "IsActive": 1,
                    "ModifiedDate": now,
                    "UpdatedAt": now,
                },
            )

        else:
            person_id = _enrollment_insert_dynamic(
                cursor,
                "Person",
                {
                    "FirstName": first_name,
                    "SecondName": second_name,
                    "ThirdName": third_name,
                    "LastName": last_name,
                    "FullName": full_name,
                    "CreationDate": now,
                    "CreatedAt": now,
                    "ModifiedDate": now,
                    "UpdatedAt": now,
                },
            )

            employee_id = _enrollment_insert_dynamic(
                cursor,
                "Employee",
                {
                    "PersonID": person_id,
                    "EmployeeNumber": employee_number,
                    "IsActive": 1,
                    "CreationDate": now,
                    "CreatedAt": now,
                    "ModifiedDate": now,
                    "UpdatedAt": now,
                },
            )

        cursor.execute(
            "SELECT * FROM EmployeeAuthentication WHERE EmployeeID=?",
            (employee_id,),
        )
        existing_auth = cursor.fetchone()

        auth_values = {
            "EmployeeID": employee_id,
            "RFIDUID": rfid_uid or None,
            "FingerprintPosition": fingerprint_position,
            "FaceImagePath": face_image_path or None,
            "IsActive": 1,
            "CreationDate": now,
            "CreatedAt": now,
            "ModifiedDate": now,
            "UpdatedAt": now,
        }

        if existing_auth:
            _enrollment_update_dynamic(
                cursor,
                "EmployeeAuthentication",
                "EmployeeID",
                employee_id,
                auth_values,
            )
        else:
            _enrollment_insert_dynamic(
                cursor,
                "EmployeeAuthentication",
                auth_values,
            )

        connection.commit()
        return True, "Employee saved successfully.", employee_id

    except Exception as error:
        connection.rollback()
        return False, f"Save failed: {error}", None

    finally:
        connection.close()


def _enrollment_normalize_status(data):
    if not isinstance(data, dict):
        return data

    enrollment_type = data.get("type")
    state = data.get("state")

    if enrollment_type == "rfid":
        uid_value = (
            data.get("rfid_uid")
            or data.get("uid")
            or data.get("uid_id")
            or data.get("rfid_id")
            or data.get("id")
            or data.get("RFIDUID")
        )

        if uid_value:
            data["rfid_uid"] = str(uid_value)

    if enrollment_type == "fingerprint":
        position_value = (
            data.get("position")
            or data.get("fingerprint_position")
            or data.get("slot")
            or data.get("FingerprintPosition")
        )

        if position_value is not None:
            data["fingerprint_position"] = position_value

    if state == "success":
        data["done"] = True

    return data


@employees_bp.route("/api/enrollment/rfid/start", methods=["POST"])
def api_start_rfid_enrollment():
    success, message = _enrollment_service.start_rfid_enrollment()
    return _enrollment_jsonify({"success": success, "message": message}), 200 if success else 400


@employees_bp.route("/api/enrollment/fingerprint/start", methods=["POST"])
def api_start_fingerprint_enrollment():
    success, message = _enrollment_service.start_fingerprint_enrollment()
    return _enrollment_jsonify({"success": success, "message": message}), 200 if success else 400


@employees_bp.route("/api/enrollment/cancel", methods=["POST"])
def api_cancel_enrollment():
    success, message = _enrollment_service.cancel_enrollment()
    return _enrollment_jsonify({"success": success, "message": message}), 200 if success else 400


@employees_bp.route("/api/enrollment/status", methods=["GET"])
def api_get_enrollment_status():
    data = _enrollment_service.get_enrollment_status()
    data = _enrollment_normalize_status(data)
    return _enrollment_jsonify(data)


@employees_bp.route("/api/enrollment/save", methods=["POST"])
def api_save_employee_enrollment():
    payload = _enrollment_request.get_json(silent=True) or {}
    success, message, employee_id = _enrollment_create_or_update_employee(payload)

    return _enrollment_jsonify(
        {
            "success": success,
            "message": message,
            "employee_id": employee_id,
        }
    ), 200 if success else 400

# ===== END MANTRAP ENROLLMENT WIZARD API PATCH =====


# ===== MANTRAP ENROLLMENT CSRF EXEMPT PATCH =====
# These endpoints are called by JavaScript fetch() from the employee wizard.
# Flask-WTF blocks POST requests without CSRF by default, so we exempt only
# the enrollment API endpoints.

try:
    from web_dashboard.extensions import csrf as _mantrap_csrf
except Exception:
    _mantrap_csrf = None

if _mantrap_csrf is not None:
    try:
        api_start_rfid_enrollment = _mantrap_csrf.exempt(api_start_rfid_enrollment)
        api_start_fingerprint_enrollment = _mantrap_csrf.exempt(api_start_fingerprint_enrollment)
        api_cancel_enrollment = _mantrap_csrf.exempt(api_cancel_enrollment)
        api_save_employee_enrollment = _mantrap_csrf.exempt(api_save_employee_enrollment)
        print("[EMPLOYEES] Enrollment API CSRF exempt enabled")
    except Exception as error:
        print(f"[EMPLOYEES] Enrollment CSRF exempt warning: {error}")
# ===== END MANTRAP ENROLLMENT CSRF EXEMPT PATCH =====


# ===== MANTRAP EMPLOYEE SOFT DELETE API START =====

import sqlite3 as _soft_delete_sqlite3
from datetime import datetime as _soft_delete_datetime
from flask import jsonify as _soft_delete_jsonify
from web_dashboard.config import Config as _SoftDeleteConfig


def _soft_delete_get_database_path():
    for attr_name in ("DATABASE_PATH", "DB_PATH", "SQLITE_DATABASE_PATH"):
        db_path = getattr(_SoftDeleteConfig, attr_name, None)
        if db_path:
            return db_path

    return _SoftDeleteConfig.PROJECT_ROOT / "database" / "mantrap.db"


def _soft_delete_get_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def _soft_delete_update_existing_columns(cursor, table_name, key_column, key_value, values):
    columns = _soft_delete_get_columns(cursor, table_name)

    allowed = {
        key: value
        for key, value in values.items()
        if key in columns and key != key_column
    }

    if not allowed:
        return False

    set_sql = ", ".join([f"{key}=?" for key in allowed.keys()])
    params = list(allowed.values()) + [key_value]

    cursor.execute(
        f"UPDATE {table_name} SET {set_sql} WHERE {key_column}=?",
        params,
    )

    return True


@employees_bp.route("/api/<int:employee_id>/soft-delete", methods=["POST"])
def api_soft_delete_employee(employee_id):
    db_path = _soft_delete_get_database_path()
    now = _soft_delete_datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    connection = _soft_delete_sqlite3.connect(str(db_path))
    connection.row_factory = _soft_delete_sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT EmployeeID FROM Employee WHERE EmployeeID=?",
            (employee_id,),
        )
        employee = cursor.fetchone()

        if not employee:
            return _soft_delete_jsonify({
                "success": False,
                "message": "Employee was not found.",
            }), 404

        # Delete:
        # Keep employee in database, but hide from dashboard list.
        updated_employee = _soft_delete_update_existing_columns(
            cursor,
            "Employee",
            "EmployeeID",
            employee_id,
            {
                "IsDeleted": 1,
                "IsActive": 0,
                "DeletedDate": now,
                "DeletedAt": now,
                "ModifiedDate": now,
                "UpdatedAt": now,
            },
        )

        if not updated_employee:
            return _soft_delete_jsonify({
                "success": False,
                "message": "Employee table does not contain expected delete columns.",
            }), 500

        # Disable authentication for the deleted employee, but keep the data.
        try:
            _soft_delete_update_existing_columns(
                cursor,
                "EmployeeAuthentication",
                "EmployeeID",
                employee_id,
                {
                    "IsActive": 0,
                    "IsDeleted": 1,
                    "DeletedDate": now,
                    "DeletedAt": now,
                    "ModifiedDate": now,
                    "UpdatedAt": now,
                },
            )
        except Exception:
            pass

        connection.commit()

        return _soft_delete_jsonify({
            "success": True,
            "message": "Employee deleted successfully.",
            "employee_id": employee_id,
        })

    except Exception as error:
        connection.rollback()

        return _soft_delete_jsonify({
            "success": False,
            "message": f"Delete failed: {error}",
        }), 500

    finally:
        connection.close()


# Exempt only this internal JavaScript API from CSRF.
try:
    from web_dashboard.extensions import csrf as _soft_delete_csrf
except Exception:
    _soft_delete_csrf = None

if _soft_delete_csrf is not None:
    try:
        api_soft_delete_employee = _soft_delete_csrf.exempt(api_soft_delete_employee)
        print("[EMPLOYEES] Delete API CSRF exempt enabled")
    except Exception as error:
        print(f"[EMPLOYEES] Delete CSRF exempt warning: {error}")

# ===== MANTRAP EMPLOYEE SOFT DELETE API END =====

