from web_dashboard.config import Config
from web_dashboard.utils.path_setup import ensure_project_root_on_path
from web_dashboard.utils.validators import ALLOWED_SETTING_KEYS, validate_setting_value

ensure_project_root_on_path()

from config import settings as mantrap_settings  # noqa: E402
from database.audit_repository import create_audit  # noqa: E402
from database.system_setting_repository import get_all_settings, save_setting  # noqa: E402


def get_settings_for_display():
    db_settings = {row["SettingKey"]: row for row in get_all_settings()}

    display_settings = []

    for key in sorted(ALLOWED_SETTING_KEYS):
        row = db_settings.get(key)
        display_settings.append({
            "key": key,
            "value": row["SettingValue"] if row else "",
            "description": row["Description"] if row else "",
        })

    fsm_timing = [
        {"key": "AI_START_DELAY", "value": str(mantrap_settings.AI_START_DELAY), "readonly": True},
        {"key": "LOCKDOWN_DELAY", "value": str(mantrap_settings.LOCKDOWN_DELAY), "readonly": True},
        {"key": "INNER_CONFIRM_TIMEOUT", "value": str(mantrap_settings.INNER_CONFIRM_TIMEOUT), "readonly": True},
        {"key": "MAX_AUTH_ATTEMPTS", "value": str(mantrap_settings.MAX_AUTH_ATTEMPTS), "readonly": True},
    ]

    return {
        "editable": display_settings,
        "readonly": fsm_timing,
        "stream_url": Config.YOLO_STREAM_BASE_URL,
    }


def update_settings(admin_user_id, settings_payload):
    updated = []
    errors = []

    for key, raw_value in settings_payload.items():
        is_valid, normalized_value = validate_setting_value(key, str(raw_value).strip())

        if not is_valid:
            errors.append(f"{key}: {normalized_value}")
            continue

        old_row = next(
            (row for row in get_all_settings() if row["SettingKey"] == key),
            None,
        )

        save_setting(key, normalized_value, old_row["Description"] if old_row else None)

        create_audit(
            admin_user_id=admin_user_id,
            action_type="UPDATE_SETTING",
            table_name="SystemSetting",
            record_id=None,
            old_value=old_row["SettingValue"] if old_row else None,
            new_value=normalized_value,
            description=f"Setting {key} updated.",
        )

        updated.append(key)

    return updated, errors
