import sys
import hashlib
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, request, redirect, session, url_for

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR / "database"))

from database_manager import fetch_one, fetch_all


app = Flask(__name__)
app.secret_key = "mantrap_dashboard_secret_key"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("login"))
        return function(*args, **kwargs)
    return wrapper


@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin = fetch_one("""
            SELECT *
            FROM AdminUser
            WHERE UserName = ?
              AND PasswordHash = ?
              AND IsActive = 1
              AND IsDeleted = 0
        """, (username, hash_password(password)))

        if admin:
            session["admin_id"] = admin["AdminUserID"]
            session["username"] = admin["UserName"]
            return redirect(url_for("dashboard"))

        error = "Invalid username or password"

    return render_template("login.html", error=error)


@app.route("/dashboard")
@login_required
def dashboard():
    employees_count = fetch_one("SELECT COUNT(*) AS Count FROM Employee WHERE IsDeleted = 0")
    access_count = fetch_one("SELECT COUNT(*) AS Count FROM AccessSession")
    auth_count = fetch_one("SELECT COUNT(*) AS Count FROM AuthenticationAttempt")
    security_count = fetch_one("SELECT COUNT(*) AS Count FROM SecurityEvent")

    latest_access = fetch_all("""
        SELECT
            a.AccessSessionID,
            p.FirstName || ' ' || p.LastName AS EmployeeName,
            a.EntryTime,
            a.ExitTime,
            a.SessionDurationSeconds,
            a.FinalStatus
        FROM AccessSession a
        LEFT JOIN Employee e ON a.EmployeeID = e.EmployeeID
        LEFT JOIN Person p ON e.PersonID = p.PersonID
        ORDER BY a.AccessSessionID DESC
        LIMIT 5
    """)

    latest_security = fetch_all("""
        SELECT *
        FROM SecurityEvent
        ORDER BY SecurityEventID DESC
        LIMIT 5
    """)

    return render_template(
        "dashboard.html",
        employees_count=employees_count["Count"],
        access_count=access_count["Count"],
        auth_count=auth_count["Count"],
        security_count=security_count["Count"],
        latest_access=latest_access,
        latest_security=latest_security
    )


@app.route("/employees")
@login_required
def employees():
    rows = fetch_all("""
        SELECT
            e.EmployeeID,
            e.EmployeeNumber,
            p.FirstName,
            p.SecondName,
            p.ThirdName,
            p.LastName,
            ea.RFIDUID,
            ea.FingerprintPosition,
            ea.FaceImagePath,
            e.IsActive
        FROM Employee e
        INNER JOIN Person p ON e.PersonID = p.PersonID
        LEFT JOIN EmployeeAuthentication ea ON e.EmployeeID = ea.EmployeeID
        WHERE e.IsDeleted = 0
        ORDER BY e.EmployeeID
    """)

    return render_template("employees.html", employees=rows)


@app.route("/access-sessions")
@login_required
def access_sessions():
    rows = fetch_all("""
        SELECT
            a.*,
            p.FirstName || ' ' || p.LastName AS EmployeeName
        FROM AccessSession a
        LEFT JOIN Employee e ON a.EmployeeID = e.EmployeeID
        LEFT JOIN Person p ON e.PersonID = p.PersonID
        ORDER BY a.AccessSessionID DESC
    """)

    return render_template("access_sessions.html", sessions=rows)


@app.route("/auth-attempts")
@login_required
def auth_attempts():
    rows = fetch_all("""
        SELECT
            aa.*,
            p.FirstName || ' ' || p.LastName AS EmployeeName
        FROM AuthenticationAttempt aa
        LEFT JOIN Employee e ON aa.EmployeeID = e.EmployeeID
        LEFT JOIN Person p ON e.PersonID = p.PersonID
        ORDER BY aa.AuthenticationAttemptID DESC
    """)

    return render_template("auth_attempts.html", attempts=rows)


@app.route("/security-events")
@login_required
def security_events():
    rows = fetch_all("""
        SELECT *
        FROM SecurityEvent
        ORDER BY SecurityEventID DESC
    """)

    return render_template("security_events.html", events=rows)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
