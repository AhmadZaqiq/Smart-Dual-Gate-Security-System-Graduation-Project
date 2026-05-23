"""Enrollment subprocess orchestration for employee wizard."""

import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _detect_project_root():
    current_file = Path(__file__).resolve()

    for parent in current_file.parents:
        rfid_script = parent / "auth" / "enroll_rfid.py"
        fingerprint_script = parent / "auth" / "enroll_fingerprint.py"
        dashboard_folder = parent / "web_dashboard"

        if rfid_script.exists() and fingerprint_script.exists() and dashboard_folder.exists():
            return parent

    return current_file.parents[2]


PROJECT_ROOT = _detect_project_root()

STATUS_FILE = PROJECT_ROOT / "runtime" / "enrollment_status.json"
ENROLLMENT_PID_FILE = PROJECT_ROOT / "runtime" / "enrollment.pid"
ENROLLMENT_LOG_FILE = PROJECT_ROOT / "runtime" / "enrollment.log"


def _write_pid(process):
    ENROLLMENT_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENROLLMENT_PID_FILE.write_text(str(process.pid), encoding="utf-8")


def _clear_pid():
    if ENROLLMENT_PID_FILE.exists():
        try:
            ENROLLMENT_PID_FILE.unlink()
        except OSError:
            pass


def _read_pid():
    if not ENROLLMENT_PID_FILE.exists():
        return None

    try:
        return int(ENROLLMENT_PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _is_pid_alive(pid):
    if not pid:
        return False

    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _stop_existing_enrollment():
    pid = _read_pid()

    if pid and _is_pid_alive(pid):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

    _clear_pid()


def _reset_status(enrollment_type, state, message):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "type": enrollment_type,
        "state": state,
        "message": message,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(STATUS_FILE, "w", encoding="utf-8") as status_file:
        json.dump(payload, status_file, indent=2)


def _read_last_log_lines(limit=12):
    if not ENROLLMENT_LOG_FILE.exists():
        return ""

    try:
        lines = ENROLLMENT_LOG_FILE.read_text(
            encoding="utf-8",
            errors="replace"
        ).splitlines()
        return "\n".join(lines[-limit:])
    except OSError:
        return ""


def start_rfid_enrollment():
    script = PROJECT_ROOT / "auth" / "enroll_rfid.py"
    return _start_enrollment(script, "rfid")


def start_fingerprint_enrollment():
    script = PROJECT_ROOT / "auth" / "enroll_fingerprint.py"
    return _start_enrollment(script, "fingerprint")


def _start_enrollment(script, enrollment_type):
    if not script.exists():
        message = f"Enrollment script not found: {script}"
        _reset_status(enrollment_type, "error", message)
        return False, message

    _stop_existing_enrollment()
    _reset_status(enrollment_type, "starting", "Starting enrollment process...")

    python_executable = os.environ.get("MANTRAP_PYTHON", sys.executable)

    ENROLLMENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    log_file = open(ENROLLMENT_LOG_FILE, "a", encoding="utf-8")

    try:
        process = subprocess.Popen(
            [python_executable, str(script)],
            cwd=str(PROJECT_ROOT),
            stdout=log_file,
            stderr=log_file,
            start_new_session=(os.name != "nt"),
        )
    except Exception as error:
        message = f"Could not start enrollment process: {error}"
        _reset_status(enrollment_type, "error", message)
        return False, message

    _write_pid(process)
    return True, "Enrollment started."


def cancel_enrollment():
    _stop_existing_enrollment()
    _reset_status("cancelled", "cancelled", "Enrollment cancelled.")
    return True, "Enrollment cancelled."


def get_enrollment_status():
    if not STATUS_FILE.exists():
        return {
            "state": "idle",
            "message": "No active enrollment.",
            "project_root": str(PROJECT_ROOT),
        }

    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as status_file:
            data = json.load(status_file)
    except (json.JSONDecodeError, OSError):
        return {
            "state": "error",
            "message": "Unable to read enrollment status.",
            "project_root": str(PROJECT_ROOT),
        }

    pid = _read_pid()

    if pid and not _is_pid_alive(pid):
        _clear_pid()

    if data.get("state") == "error":
        log_tail = _read_last_log_lines()

        if log_tail:
            data["message"] = f"{data.get('message')}\n{log_tail}"

    data["project_root"] = str(PROJECT_ROOT)
    return data
