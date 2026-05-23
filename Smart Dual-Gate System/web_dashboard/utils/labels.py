"""
Human-readable labels for dashboard UI.
Backend identifiers remain unchanged; only display text is transformed.
"""

SETTING_LABELS = {
    "MAX_RFID_ATTEMPTS": "Maximum RFID Attempts",
    "MAX_FINGERPRINT_ATTEMPTS": "Maximum Fingerprint Attempts",
    "MAX_FACE_ATTEMPTS": "Maximum Face Recognition Attempts",
    "MAX_BEHAVIOR_ATTEMPTS": "Maximum Behavior Analysis Attempts",
    "MAX_AUTH_TOTAL_ATTEMPTS": "Maximum Total Authentication Attempts",
    "REQUIRE_RFID": "Require RFID",
    "REQUIRE_FINGERPRINT": "Require Fingerprint",
    "REQUIRE_FACE_RECOGNITION": "Require Face Recognition",
    "REQUIRE_BEHAVIOR_ANALYSIS": "Require Behavior Analysis",
    "YOLO_CONFIDENCE_THRESHOLD": "YOLO Confidence Threshold",
    "YOLO_IMAGE_SIZE": "YOLO Image Size",
    "DASHBOARD_STREAM_URL": "Dashboard Stream URL",
    "AI_START_DELAY": "Workflow Start Delay (seconds)",
    "LOCKDOWN_DELAY": "Lockdown Delay (seconds)",
    "INNER_CONFIRM_TIMEOUT": "Inner Confirmation Timeout (seconds)",
    "MAX_AUTH_ATTEMPTS": "Maximum Authentication Attempts",
}

WORKFLOW_STATE_LABELS = {
    "SYSTEM_OFF": "System Off",
    "IDLE_OUTER_OPEN": "Standby — Outer Access",
    "AI_START_DELAY": "Preparing Detection",
    "PERSON_COUNTING": "Occupancy Detection",
    "MULTI_PERSON_WARNING": "Multi-Person Warning",
    "MULTI_PERSON_EXIT_RELEASE": "Exit Release",
    "AUTHENTICATION_READY": "Authentication Ready",
    "AUTHENTICATION_PROCESSING": "Authentication In Progress",
    "AUTHENTICATION_FAILED_WAIT_BACK": "Authentication Failed",
    "WAIT_INNER_BUTTON_CONFIRM": "Awaiting Inner Confirmation",
    "INNER_DOOR_UNLOCKED": "Inner Access Granted",
    "CANCEL_AND_EXIT": "Cancel & Exit",
    "SECURITY_LOCKDOWN": "Security Lockdown",
    "ERROR_STATE": "System Error",
}

EVENT_TYPE_LABELS = {
    "INVALID_ROOM_COUNT": "Invalid Room Count",
    "SECURITY_LOCKDOWN": "Security Lockdown",
    "ACCESS_GRANTED": "Access Granted",
    "ACCESS_DENIED": "Access Denied",
}

AUTH_STATUS_LABELS = {
    "RFID_OK": "RFID Verified",
    "RFID_FAILED": "RFID Failed",
    "FINGER_OK": "Fingerprint Verified",
    "FINGER_FAILED": "Fingerprint Failed",
    "FACE_OK": "Face Verified",
    "FACE_FAILED": "Face Failed",
    "BEHAVIOR_NORMAL": "Behavior Normal",
    "BEHAVIOR_MEDIUM": "Behavior Warning",
    "BEHAVIOR_DANGER": "Behavior Alert",
    "SKIPPED": "Skipped",
    "NOT_STARTED": "Not Started",
}

ACTIVITY_TYPE_LABELS = {
    "ACCESS_SESSION": "Access Session",
    "SECURITY_EVENT": "Security Event",
    "AUTHENTICATION_ATTEMPT": "Authentication Attempt",
}


def humanize(value):
    if value is None or value == "":
        return "—"

    text = str(value).strip()

    if text in SETTING_LABELS:
        return SETTING_LABELS[text]
    if text in WORKFLOW_STATE_LABELS:
        return WORKFLOW_STATE_LABELS[text]
    if text in EVENT_TYPE_LABELS:
        return EVENT_TYPE_LABELS[text]
    if text in AUTH_STATUS_LABELS:
        return AUTH_STATUS_LABELS[text]
    if text in ACTIVITY_TYPE_LABELS:
        return ACTIVITY_TYPE_LABELS[text]

    if text.isupper() and "_" in text:
        return text.replace("_", " ").title()

    return text


def workflow_state_label(state):
    return WORKFLOW_STATE_LABELS.get(state, humanize(state))
