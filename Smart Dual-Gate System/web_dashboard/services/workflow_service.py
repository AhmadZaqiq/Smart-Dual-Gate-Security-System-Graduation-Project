"""Maps backend workflow states to user-facing security path stages."""

from web_dashboard.utils.labels import workflow_state_label

WORKFLOW_STAGES = [
    {"id": "outer_door", "label": "Outer Door", "states": ["IDLE_OUTER_OPEN", "AI_START_DELAY"]},
    {"id": "occupancy", "label": "Multi-Person Detection", "states": ["PERSON_COUNTING", "MULTI_PERSON_WARNING", "MULTI_PERSON_EXIT_RELEASE"]},
    {"id": "rfid", "label": "Authentication Stage 1 (RFID)", "states": ["AUTHENTICATION_READY", "AUTHENTICATION_PROCESSING"]},
    {"id": "fingerprint", "label": "Authentication Stage 2 (Fingerprint)", "states": ["AUTHENTICATION_PROCESSING"]},
    {"id": "face", "label": "Authentication Stage 3 (Face Recognition)", "states": ["AUTHENTICATION_PROCESSING"]},
    {"id": "behavior", "label": "Behavioral Analysis", "states": ["AUTHENTICATION_PROCESSING"]},
    {"id": "chamber", "label": "Secure Chamber", "states": ["WAIT_INNER_BUTTON_CONFIRM", "AUTHENTICATION_FAILED_WAIT_BACK"]},
    {"id": "inner_door", "label": "Inner Door", "states": ["INNER_DOOR_UNLOCKED"]},
    {"id": "granted", "label": "Access Granted", "states": []},
    {"id": "lockdown", "label": "Security Lockdown", "states": ["SECURITY_LOCKDOWN", "ERROR_STATE"]},
]

STATE_TO_STAGE = {
    "IDLE_OUTER_OPEN": "outer_door",
    "AI_START_DELAY": "outer_door",
    "PERSON_COUNTING": "occupancy",
    "MULTI_PERSON_WARNING": "occupancy",
    "MULTI_PERSON_EXIT_RELEASE": "occupancy",
    "AUTHENTICATION_READY": "rfid",
    "AUTHENTICATION_PROCESSING": "rfid",
    "AUTHENTICATION_FAILED_WAIT_BACK": "chamber",
    "WAIT_INNER_BUTTON_CONFIRM": "chamber",
    "INNER_DOOR_UNLOCKED": "inner_door",
    "CANCEL_AND_EXIT": "outer_door",
    "SECURITY_LOCKDOWN": "lockdown",
    "ERROR_STATE": "lockdown",
    "SYSTEM_OFF": "outer_door",
}


def get_workflow_view(status):
    workflow_state = status.get("fsm_state", "SYSTEM_OFF")
    active_stage = STATE_TO_STAGE.get(workflow_state, "outer_door")

    if workflow_state == "INNER_DOOR_UNLOCKED":
        active_stage = "granted"

    stages = []

    for stage in WORKFLOW_STAGES:
        item = dict(stage)
        item["active"] = stage["id"] == active_stage
        item["completed"] = _is_completed(stage["id"], active_stage)
        stages.append(item)

    return {
        "workflow_state": workflow_state,
        "workflow_label": workflow_state_label(workflow_state),
        "active_stage": active_stage,
        "stages": stages,
    }


def _is_completed(stage_id, active_stage):
    order = [stage["id"] for stage in WORKFLOW_STAGES]
    if stage_id not in order or active_stage not in order:
        return False
    return order.index(stage_id) < order.index(active_stage)
