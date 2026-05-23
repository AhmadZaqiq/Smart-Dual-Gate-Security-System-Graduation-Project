ALLOWED_SETTING_KEYS = {
    "MAX_RFID_ATTEMPTS",
    "MAX_FINGERPRINT_ATTEMPTS",
    "MAX_FACE_ATTEMPTS",
    "MAX_BEHAVIOR_ATTEMPTS",
    "MAX_AUTH_TOTAL_ATTEMPTS",
    "REQUIRE_RFID",
    "REQUIRE_FINGERPRINT",
    "REQUIRE_FACE_RECOGNITION",
    "REQUIRE_BEHAVIOR_ANALYSIS",
    "YOLO_CONFIDENCE_THRESHOLD",
    "YOLO_IMAGE_SIZE",
    "DASHBOARD_STREAM_URL",
}


def validate_setting_value(setting_key, setting_value):
    if setting_key not in ALLOWED_SETTING_KEYS:
        return False, "Setting key is not allowed."

    if setting_key.startswith("REQUIRE_"):
        if setting_value not in ("0", "1"):
            return False, "Boolean settings must be 0 or 1."
        return True, setting_value

    if setting_key.startswith("MAX_"):
        try:
            value = int(setting_value)
        except ValueError:
            return False, "Attempt limits must be integers."

        if value < 1 or value > 20:
            return False, "Attempt limits must be between 1 and 20."

        return True, str(value)

    if setting_key == "YOLO_CONFIDENCE_THRESHOLD":
        try:
            value = float(setting_value)
        except ValueError:
            return False, "Confidence must be a number."

        if value < 0.1 or value > 0.99:
            return False, "Confidence must be between 0.1 and 0.99."

        return True, str(value)

    if setting_key == "YOLO_IMAGE_SIZE":
        try:
            value = int(setting_value)
        except ValueError:
            return False, "Image size must be an integer."

        if value not in (160, 320, 416, 640):
            return False, "Image size must be 160, 320, 416, or 640."

        return True, str(value)

    if setting_key == "DASHBOARD_STREAM_URL":
        if not setting_value.startswith("http"):
            return False, "Stream URL must start with http or https."
        return True, setting_value.strip().rstrip("/")

    return False, "Unknown validation rule."


def sanitize_search_text(search_text):
    if not search_text:
        return None

    cleaned = search_text.strip()

    if not cleaned:
        return None

    return cleaned[:100]
