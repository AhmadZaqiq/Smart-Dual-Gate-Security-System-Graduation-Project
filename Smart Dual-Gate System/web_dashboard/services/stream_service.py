"""Safe camera stream subprocess management. The dashboard never opens cameras directly."""

import os
import signal
import subprocess
import sys
import time

import requests

from web_dashboard.config import Config
from web_dashboard.utils.path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from core.system_status import read_status_snapshot  # noqa: E402

RUNTIME_DIR = Config.PROJECT_ROOT / "runtime"

FACE_PID = RUNTIME_DIR / "face_stream.pid"
INNER_PREVIEW_PID = RUNTIME_DIR / "inner_preview_stream.pid"

FACE_LOG = RUNTIME_DIR / "face_stream.log"
INNER_PREVIEW_LOG = RUNTIME_DIR / "inner_preview_stream.log"

FACE_PORT = int(os.environ.get("FACE_STREAM_PORT", "5001"))
INNER_PREVIEW_PORT = int(os.environ.get("INNER_PREVIEW_PORT", "5002"))

START_TIMEOUT_SECONDS = 6


def _read_pid(path):
    if not path.exists():
        return None

    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _is_linux_zombie(pid):
    if os.name == "nt" or not pid:
        return False

    try:
        with open(f"/proc/{pid}/stat", "r", encoding="utf-8") as stat_file:
            stat_data = stat_file.read().split()
            return len(stat_data) > 2 and stat_data[2] == "Z"
    except OSError:
        return False


def _is_alive(pid):
    if not pid:
        return False

    if _is_linux_zombie(pid):
        return False

    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _remove_stale_pid(path):
    pid = _read_pid(path)

    if pid and _is_alive(pid):
        return pid

    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass

    return None


def _stop_pid_file(path):
    pid = _read_pid(path)

    if pid and _is_alive(pid):
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
            else:
                os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

        time.sleep(1)

        if _is_alive(pid) and os.name != "nt":
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


def _json_health(url):
    try:
        response = requests.get(url, timeout=1.5)
        if response.status_code != 200:
            return False

        data = response.json()
        return bool(data.get("running") and data.get("has_frame"))
    except requests.RequestException:
        return False
    except ValueError:
        return False


def _read_last_log_lines(log_path, limit=12):
    if not log_path.exists():
        return "No stream log found."

    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-limit:]) if lines else "Stream log is empty."
    except OSError:
        return "Unable to read stream log."


def _wait_for_ready(pid_path, health_url, timeout_seconds):
    started_at = time.time()

    while time.time() - started_at < timeout_seconds:
        pid = _remove_stale_pid(pid_path)

        if pid and _json_health(health_url):
            return pid

        time.sleep(0.3)

    return None


def _start_subprocess(script_path, log_path):
    python_executable = os.environ.get("MANTRAP_PYTHON", sys.executable)

    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as log_file:
        subprocess.Popen(
            [python_executable, str(script_path)],
            cwd=str(Config.PROJECT_ROOT),
            stdout=log_file,
            stderr=log_file,
            start_new_session=(os.name != "nt"),
        )


def _build_local_video_url(port):
    return f"http://127.0.0.1:{port}/video"


def _build_local_health_url(port):
    return f"http://127.0.0.1:{port}/health"


def get_streams_status():
    snapshot = read_status_snapshot()
    yolo_active = snapshot.get("yolo_running", False)

    face_pid = _remove_stale_pid(FACE_PID)
    inner_preview_pid = _remove_stale_pid(INNER_PREVIEW_PID)

    face_running = face_pid is not None
    inner_preview_running = inner_preview_pid is not None

    face_video_url = _build_local_video_url(FACE_PORT)
    face_health_url = _build_local_health_url(FACE_PORT)

    yolo_video_url = f"{Config.YOLO_STREAM_BASE_URL}/video"
    yolo_health = bool(yolo_active and snapshot.get("stream_available"))

    inner_preview_video_url = _build_local_video_url(INNER_PREVIEW_PORT)
    inner_preview_health_url = _build_local_health_url(INNER_PREVIEW_PORT)

    face_online = face_running and _json_health(face_health_url)

    if yolo_active:
        inner_online = yolo_health
    else:
        inner_online = inner_preview_running and _json_health(inner_preview_health_url)

    return {
        "face": {
            "label": "Face Camera",
            "running": face_running,
            "health": "ONLINE" if face_online else "OFFLINE",
            "url": face_video_url if face_online else None,
            "port": FACE_PORT,
        },
        "inner": {
            "label": "Inner Camera",
            "running": yolo_active or inner_preview_running,
            "health": "ONLINE" if inner_online else "OFFLINE",
            "url": yolo_video_url if yolo_active and inner_online else (
                inner_preview_video_url if inner_preview_running and inner_online else None
            ),
            "source": "yolo" if yolo_active else ("preview" if inner_preview_running else "inactive"),
            "port": 5000 if yolo_active else INNER_PREVIEW_PORT,
        },
    }


def start_face_stream():
    pid = _remove_stale_pid(FACE_PID)
    health_url = _build_local_health_url(FACE_PORT)

    if pid and _json_health(health_url):
        return True, "Face camera stream is already running."

    if pid:
        _stop_pid_file(FACE_PID)

    script = Config.PROJECT_ROOT / "ai" / "face_stream_server.py"

    if not script.exists():
        return False, "face_stream_server.py was not found."

    _start_subprocess(script, FACE_LOG)

    ready_pid = _wait_for_ready(FACE_PID, health_url, START_TIMEOUT_SECONDS)

    if ready_pid:
        return True, "Face camera stream started."

    _stop_pid_file(FACE_PID)
    return False, "Unable to start face camera stream.\n" + _read_last_log_lines(FACE_LOG)


def stop_face_stream():
    _stop_pid_file(FACE_PID)
    return True, "Face camera stream stopped."


def start_inner_stream():
    snapshot = read_status_snapshot()

    if snapshot.get("yolo_running") and snapshot.get("stream_available"):
        return True, "Inner camera is active through YOLO monitoring stream."

    pid = _remove_stale_pid(INNER_PREVIEW_PID)
    health_url = _build_local_health_url(INNER_PREVIEW_PORT)

    if pid and _json_health(health_url):
        return True, "Inner camera preview stream is already running."

    if pid:
        _stop_pid_file(INNER_PREVIEW_PID)

    script = Config.PROJECT_ROOT / "ai" / "inner_preview_stream.py"

    if not script.exists():
        return False, "inner_preview_stream.py was not found."

    _start_subprocess(script, INNER_PREVIEW_LOG)

    ready_pid = _wait_for_ready(INNER_PREVIEW_PID, health_url, START_TIMEOUT_SECONDS)

    if ready_pid:
        return True, "Inner camera preview stream started."

    _stop_pid_file(INNER_PREVIEW_PID)
    return False, "Unable to start inner camera preview.\n" + _read_last_log_lines(INNER_PREVIEW_LOG)


def stop_inner_stream():
    snapshot = read_status_snapshot()

    if snapshot.get("yolo_running"):
        return False, "YOLO monitor controls the inner camera during person counting."

    _stop_pid_file(INNER_PREVIEW_PID)
    return True, "Inner camera preview stream stopped."
