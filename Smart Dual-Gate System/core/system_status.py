"""
Read-only runtime status bridge for the admin dashboard.
The FSM and YOLO monitor update this file; the dashboard only reads it.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = PROJECT_ROOT / "runtime"
STATUS_FILE = RUNTIME_DIR / "mantrap_status.json"

DEFAULT_STATUS = {
    "updated_at": None,
    "fsm_state": "SYSTEM_OFF",
    "system_online": False,
    "outer_door": "unknown",
    "inner_door": "unknown",
    "yolo_running": False,
    "yolo_person_count": 0,
    "stream_available": False,
    "active_session_id": None,
    "alarm_active": False,
}


def ensure_runtime_directory():
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def read_status_snapshot():
    ensure_runtime_directory()

    if not STATUS_FILE.exists():
        return dict(DEFAULT_STATUS)

    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as status_file:
            data = json.load(status_file)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_STATUS)

    merged = dict(DEFAULT_STATUS)
    merged.update(data)
    return merged


def update_status_snapshot(**fields):
    ensure_runtime_directory()

    snapshot = read_status_snapshot()
    snapshot.update(fields)
    snapshot["updated_at"] = datetime.now(timezone.utc).isoformat()

    directory = str(STATUS_FILE.parent)
    fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            json.dump(snapshot, temp_file, indent=2)
        os.replace(temp_path, STATUS_FILE)
    except OSError:
        if os.path.exists(temp_path):
            os.remove(temp_path)
