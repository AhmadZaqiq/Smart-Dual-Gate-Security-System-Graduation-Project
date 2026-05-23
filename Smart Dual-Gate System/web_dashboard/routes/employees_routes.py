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
