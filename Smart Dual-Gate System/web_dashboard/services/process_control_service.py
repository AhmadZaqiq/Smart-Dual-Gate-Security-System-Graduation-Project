"""
Safe mantrap process lifecycle control for the admin dashboard.
Never imports GPIO or camera modules.
"""

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

from web_dashboard.config import Config
from web_dashboard.utils.path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from database.audit_repository import create_audit  # noqa: E402

RUNTIME_DIR = Config.PROJECT_ROOT / "runtime"
PID_FILE = RUNTIME_DIR / "mantrap.pid"
LOCK_FILE = RUNTIME_DIR / "mantrap.lock"
PROCESS_STATE_FILE = RUNTIME_DIR / "process_state.json"
MAIN_SCRIPT = Config.PROJECT_ROOT / "main.py"

STOP_TIMEOUT_SECONDS = 12
START_TIMEOUT_SECONDS = 20


def _ensure_runtime_dir():
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def _read_process_state_file():
    _ensure_runtime_dir()

    if not PROCESS_STATE_FILE.exists():
        return {}

    try:
        with open(PROCESS_STATE_FILE, "r", encoding="utf-8") as state_file:
            return json.load(state_file)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_process_state_file(state, message=None, pid=None):
    _ensure_runtime_dir()

    payload = {
        "state": state,
        "message": message,
        "pid": pid,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(PROCESS_STATE_FILE, "w", encoding="utf-8") as state_file:
        json.dump(payload, state_file, indent=2)


def _read_pid():
    if not PID_FILE.exists():
        return None

    try:
        raw_value = PID_FILE.read_text(encoding="utf-8").strip()
        return int(raw_value)
    except (ValueError, OSError):
        return None


def _is_linux_zombie(pid):
    if os.name == "nt" or not pid:
        return False

    stat_path = f"/proc/{pid}/stat"

    try:
        with open(stat_path, "r", encoding="utf-8") as stat_file:
            stat_data = stat_file.read().split()
            return len(stat_data) > 2 and stat_data[2] == "Z"
    except OSError:
        return False


def _is_pid_alive(pid):
    if not pid:
        return False

    if _is_linux_zombie(pid):
        return False

    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _cleanup_stale_pid_file():
    pid = _read_pid()

    if pid and _is_pid_alive(pid):
        return pid

    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
        except OSError:
            pass

    return None


def _acquire_lock():
    _ensure_runtime_dir()

    if LOCK_FILE.exists():
        try:
            lock_pid = int(LOCK_FILE.read_text(encoding="utf-8").strip())

            if _is_pid_alive(lock_pid):
                return False

            LOCK_FILE.unlink()
        except (ValueError, OSError):
            try:
                LOCK_FILE.unlink()
            except OSError:
                return False

    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True


def _release_lock():
    if LOCK_FILE.exists():
        try:
            LOCK_FILE.unlink()
        except OSError:
            pass


def _wait_until_process_stops(pid, timeout_seconds):
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        if not _is_pid_alive(pid):
            return True

        time.sleep(0.4)

    return not _is_pid_alive(pid)


def _send_ctrl_c_to_process(pid):
    """
    Send SIGINT like pressing Ctrl+C in terminal.
    The process is started in a new session, so its process group ID is the PID.
    """
    if not pid or not _is_pid_alive(pid):
        return True

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T"],
                check=False,
                capture_output=True,
            )
        else:
            os.killpg(pid, signal.SIGINT)

        return _wait_until_process_stops(pid, STOP_TIMEOUT_SECONDS)
    except ProcessLookupError:
        return True
    except OSError:
        return False


def _force_stop_process(pid):
    """
    Last-resort stop if Ctrl+C cleanup did not finish.
    """
    if not pid or not _is_pid_alive(pid):
        return True

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                capture_output=True,
            )
            return True

        os.killpg(pid, signal.SIGTERM)

        if _wait_until_process_stops(pid, 5):
            return True

        if _is_pid_alive(pid):
            os.killpg(pid, signal.SIGKILL)

        return _wait_until_process_stops(pid, 3)
    except ProcessLookupError:
        return True
    except OSError:
        return False


def get_process_status():
    file_state = _read_process_state_file()
    pid = _cleanup_stale_pid_file()
    running = pid is not None and _is_pid_alive(pid)

    if running:
        lifecycle = "RUNNING"
    elif file_state.get("state") in ("STARTING", "STOPPING"):
        lifecycle = file_state.get("state")
    else:
        lifecycle = "STOPPED"

    return {
        "lifecycle": lifecycle,
        "running": running,
        "pid": pid,
        "message": file_state.get("message"),
        "updated_at": file_state.get("updated_at"),
        "main_script": str(MAIN_SCRIPT),
    }


def _wait_for_pid(started_at):
    while time.time() - started_at < START_TIMEOUT_SECONDS:
        pid = _read_pid()

        if pid and _is_pid_alive(pid):
            return pid

        time.sleep(0.5)

    return None


def start_system(admin_user_id):
    current = get_process_status()

    if current["running"]:
        return False, "Mantrap system is already running."

    if not _acquire_lock():
        return False, "Another control operation is in progress."

    try:
        if not MAIN_SCRIPT.exists():
            return False, "main.py was not found."

        _write_process_state_file("STARTING", "Launching mantrap process")

        creation_flags = 0

        if os.name == "nt":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

        python_executable = os.environ.get("MANTRAP_PYTHON", sys.executable)

        subprocess.Popen(
            [python_executable, str(MAIN_SCRIPT)],
            cwd=str(Config.PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
            start_new_session=(os.name != "nt"),
        )

        pid = _wait_for_pid(time.time())

        if not pid:
            _write_process_state_file("STOPPED", "Failed to detect mantrap PID")
            return False, "Mantrap process did not start in time."

        _write_process_state_file("RUNNING", "Mantrap process started", pid=pid)

        create_audit(
            admin_user_id=admin_user_id,
            action_type="SYSTEM_START",
            table_name="MantrapProcess",
            record_id=pid,
            description="Mantrap system started from dashboard.",
        )

        return True, "Mantrap system started successfully."
    finally:
        _release_lock()


def stop_system(admin_user_id):
    current = get_process_status()
    pid = current.get("pid")

    if not pid or not current["running"]:
        _write_process_state_file("STOPPED", "Mantrap process already stopped")
        _cleanup_stale_pid_file()
        return True, "Mantrap system is already stopped."

    if not _acquire_lock():
        return False, "Another control operation is in progress."

    try:
        _write_process_state_file("STOPPING", "Sending Ctrl+C stop signal", pid=pid)

        stopped = _send_ctrl_c_to_process(pid)

        if not stopped:
            _write_process_state_file("STOPPING", "Ctrl+C timeout, forcing stop", pid=pid)
            stopped = _force_stop_process(pid)

        _cleanup_stale_pid_file()

        if stopped:
            _write_process_state_file("STOPPED", "Mantrap process stopped")
            create_audit(
                admin_user_id=admin_user_id,
                action_type="SYSTEM_STOP",
                table_name="MantrapProcess",
                record_id=pid,
                description="Mantrap system stopped from dashboard using Ctrl+C signal.",
            )
            return True, "Mantrap system stopped successfully."

        return False, "Unable to stop mantrap process."
    finally:
        _release_lock()
