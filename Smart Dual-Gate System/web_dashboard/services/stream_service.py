"""Safe camera stream subprocess management — dashboard never opens cameras."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests

from web_dashboard.config import Config
from web_dashboard.utils.path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from core.system_status import read_status_snapshot  # noqa: E402

FACE_PID = Config.PROJECT_ROOT / "runtime" / "face_stream.pid"
INNER_PREVIEW_PID = Config.PROJECT_ROOT / "runtime" / "inner_preview_stream.pid"
FACE_PORT = int(os.environ.get("FACE_STREAM_PORT", "5001"))
INNER_PREVIEW_PORT = int(os.environ.get("INNER_PREVIEW_PORT", "5002"))


def _read_pid(path):
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _is_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _stop_pid_file(path):
    pid = _read_pid(path)
    if pid and _is_alive(pid):
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
        else:
            os.kill(pid, signal.SIGTERM)
        time.sleep(0.5)
    if path.exists():
        path.unlink(missing_ok=True)


def _stream_health(url):
    try:
        response = requests.get(url, timeout=1.5, stream=True)
        response.close()
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_streams_status():
    snapshot = read_status_snapshot()
    yolo_active = snapshot.get("yolo_running", False)

    face_pid = _read_pid(FACE_PID)
    inner_preview_pid = _read_pid(INNER_PREVIEW_PID)

    face_running = _is_alive(face_pid)
    inner_preview_running = _is_alive(inner_preview_pid)

    face_url = f"http://127.0.0.1:{FACE_PORT}/video"
    yolo_url = f"{Config.YOLO_STREAM_BASE_URL}/video"
    inner_preview_url = f"http://127.0.0.1:{INNER_PREVIEW_PORT}/video"

    return {
        "face": {
            "label": "Face Camera",
            "running": face_running,
            "health": "ONLINE" if face_running and _stream_health(face_url) else "OFFLINE",
            "url": face_url if face_running else None,
            "port": FACE_PORT,
        },
        "inner": {
            "label": "Inner Camera (YOLO)",
            "running": yolo_active or inner_preview_running,
            "health": "ONLINE" if yolo_active and snapshot.get("stream_available") else (
                "ONLINE" if inner_preview_running and _stream_health(inner_preview_url) else "OFFLINE"
            ),
            "url": yolo_url if yolo_active else (inner_preview_url if inner_preview_running else None),
            "source": "yolo" if yolo_active else ("preview" if inner_preview_running else "inactive"),
            "port": 5000 if yolo_active else INNER_PREVIEW_PORT,
        },
    }


def start_face_stream():
    if _is_alive(_read_pid(FACE_PID)):
        return True, "Face camera stream is already running."

    python_executable = os.environ.get("MANTRAP_PYTHON", sys.executable)
    script = Config.PROJECT_ROOT / "ai" / "face_stream_server.py"

    subprocess.Popen(
        [python_executable, str(script)],
        cwd=str(Config.PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=(os.name != "nt"),
    )

    time.sleep(1.5)

    if _is_alive(_read_pid(FACE_PID)):
        return True, "Face camera stream started."

    return False, "Unable to start face camera stream."


def stop_face_stream():
    _stop_pid_file(FACE_PID)
    return True, "Face camera stream stopped."


def start_inner_stream():
    snapshot = read_status_snapshot()

    if snapshot.get("yolo_running"):
        return True, "Inner camera is active through YOLO monitoring stream."

    if _is_alive(_read_pid(INNER_PREVIEW_PID)):
        return True, "Inner camera preview stream is already running."

    python_executable = os.environ.get("MANTRAP_PYTHON", sys.executable)
    script = Config.PROJECT_ROOT / "ai" / "inner_preview_stream.py"

    subprocess.Popen(
        [python_executable, str(script)],
        cwd=str(Config.PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=(os.name != "nt"),
    )

    time.sleep(1.5)

    if _is_alive(_read_pid(INNER_PREVIEW_PID)):
        return True, "Inner camera preview stream started."

    return False, "Unable to start inner camera preview. Camera may be in use by YOLO."


def stop_inner_stream():
    snapshot = read_status_snapshot()

    if snapshot.get("yolo_running"):
        return False, "YOLO monitor controls the inner camera during person counting."

    _stop_pid_file(INNER_PREVIEW_PID)
    return True, "Inner camera preview stream stopped."
