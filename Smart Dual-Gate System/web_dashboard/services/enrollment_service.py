"""Enrollment subprocess orchestration for employee wizard."""

import json
import os
import subprocess
import sys
from pathlib import Path

from web_dashboard.config import Config

STATUS_FILE = Config.PROJECT_ROOT / "runtime" / "enrollment_status.json"
ENROLLMENT_PID_FILE = Config.PROJECT_ROOT / "runtime" / "enrollment.pid"


def _write_pid(process):
    ENROLLMENT_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENROLLMENT_PID_FILE.write_text(str(process.pid), encoding="utf-8")


def _clear_pid():
    if ENROLLMENT_PID_FILE.exists():
        ENROLLMENT_PID_FILE.unlink()


def _reset_status(enrollment_type, state, message):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": enrollment_type,
        "state": state,
        "message": message,
        "updated_at": "",
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as status_file:
        json.dump(payload, status_file, indent=2)


def start_rfid_enrollment():
    script = Config.PROJECT_ROOT / "auth" / "enroll_rfid.py"
    return _start_enrollment(script, "rfid")


def start_fingerprint_enrollment():
    script = Config.PROJECT_ROOT / "auth" / "enroll_fingerprint.py"
    return _start_enrollment(script, "fingerprint")


def _start_enrollment(script, enrollment_type):
    if not script.exists():
        return False, "Enrollment script not found."

    _reset_status(enrollment_type, "starting", "Starting enrollment process...")
    python_executable = os.environ.get("MANTRAP_PYTHON", sys.executable)

    process = subprocess.Popen(
        [python_executable, str(script)],
        cwd=str(Config.PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    _write_pid(process)
    return True, "Enrollment started."


def cancel_enrollment():
    if ENROLLMENT_PID_FILE.exists():
        try:
            pid = int(ENROLLMENT_PID_FILE.read_text(encoding="utf-8").strip())
            os.kill(pid, 9)
        except (ValueError, OSError):
            pass

    _clear_pid()
    _reset_status("cancelled", "cancelled", "Enrollment cancelled.")
    return True, "Enrollment cancelled."


def get_enrollment_status():
    if not STATUS_FILE.exists():
        return {"state": "idle", "message": "No active enrollment."}

    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as status_file:
            return json.load(status_file)
    except (json.JSONDecodeError, OSError):
        return {"state": "error", "message": "Unable to read enrollment status."}
