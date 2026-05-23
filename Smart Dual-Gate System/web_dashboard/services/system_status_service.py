from datetime import datetime, timezone

import requests

from web_dashboard.config import Config
from web_dashboard.services import door_sensor_service
from web_dashboard.utils.path_setup import ensure_project_root_on_path

ensure_project_root_on_path()

from core.system_status import read_status_snapshot  # noqa: E402


def _parse_timestamp(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _apply_live_door_states(snapshot):
    live_doors = door_sensor_service.read_live_door_states()

    snapshot["door_sensor_available"] = live_doors.get("available", False)

    if live_doors.get("available"):
        snapshot["outer_door"] = live_doors.get("outer_door") or "unknown"
        snapshot["inner_door"] = live_doors.get("inner_door") or "unknown"
        snapshot["outer_door_raw"] = live_doors.get("outer_raw")
        snapshot["inner_door_raw"] = live_doors.get("inner_raw")

    return snapshot


def get_system_status():
    from web_dashboard.services.process_control_service import get_process_status

    snapshot = read_status_snapshot()
    updated_at = _parse_timestamp(snapshot.get("updated_at"))
    process = get_process_status()

    is_online = False

    if process.get("running"):
        is_online = True
    elif updated_at:
        age_seconds = (
            datetime.now(timezone.utc) - updated_at.astimezone(timezone.utc)
        ).total_seconds()
        is_online = age_seconds <= Config.STATUS_STALE_SECONDS

    snapshot = _apply_live_door_states(snapshot)

    snapshot["system_online"] = is_online
    snapshot["process"] = process
    snapshot["process_lifecycle"] = process.get("lifecycle", "UNKNOWN")
    snapshot["stream_health"] = _resolve_stream_health(snapshot, process)
    snapshot["alarm_level"] = _resolve_alarm_level(snapshot)

    return snapshot


def _resolve_stream_health(snapshot, process):
    if not process.get("running"):
        return "INACTIVE"

    if snapshot.get("yolo_running") and snapshot.get("stream_available"):
        return "ONLINE"

    if check_stream_health():
        return "ONLINE"

    return "OFFLINE"


def _resolve_alarm_level(snapshot):
    if snapshot.get("fsm_state") == "SECURITY_LOCKDOWN":
        return "LOCKDOWN"

    if snapshot.get("alarm_active"):
        return "WARNING"

    return "NORMAL"


def check_stream_health():
    stream_url = f"{Config.YOLO_STREAM_BASE_URL}/video"

    try:
        response = requests.get(stream_url, timeout=Config.STREAM_HEALTH_TIMEOUT, stream=True)
        response.close()
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_health_report():
    status = get_system_status()
    stream_healthy = check_stream_health()

    return {
        "database_ok": Config.DATABASE_PATH and True,
        "status_file_ok": bool(status),
        "door_sensor_available": status.get("door_sensor_available", False),
        "stream_healthy": stream_healthy,
        "fsm_online": status.get("system_online", False),
        "yolo_running": status.get("yolo_running", False),
    }
