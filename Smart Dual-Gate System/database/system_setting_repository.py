from database.database_manager import (
    execute_insert,
    execute_non_query,
    execute_query,
    execute_query_one
)


def create_system_setting(setting_key, setting_value, description=None):
    query = """
        INSERT INTO SystemSetting
        (
            SettingKey,
            SettingValue,
            Description,
            CreationDate,
            LastUpdatedDate
        )
        VALUES
        (
            ?,
            ?,
            ?,
            datetime('now'),
            datetime('now')
        );
    """

    setting_id = execute_insert(
        query,
        (setting_key, setting_value, description)
    )

    if setting_id:
        print(f"[DATABASE] System setting created: {setting_key}", flush=True)

    return setting_id


def get_setting_by_key(setting_key):
    query = """
        SELECT
            SystemSettingID,
            SettingKey,
            SettingValue,
            Description,
            CreationDate,
            LastUpdatedDate
        FROM SystemSetting
        WHERE SettingKey = ?;
    """

    return execute_query_one(query, (setting_key,))


def get_setting_value(setting_key, default_value=None):
    setting = get_setting_by_key(setting_key)

    if setting is None:
        return default_value

    return setting["SettingValue"]


def get_all_settings():
    query = """
        SELECT
            SystemSettingID,
            SettingKey,
            SettingValue,
            Description,
            CreationDate,
            LastUpdatedDate
        FROM SystemSetting
        ORDER BY SettingKey;
    """

    return execute_query(query)


def update_setting_value(setting_key, setting_value):
    query = """
        UPDATE SystemSetting
        SET
            SettingValue = ?,
            LastUpdatedDate = datetime('now')
        WHERE SettingKey = ?;
    """

    rows = execute_non_query(
        query,
        (setting_value, setting_key)
    )

    if rows > 0:
        print(f"[DATABASE] System setting updated: {setting_key}", flush=True)

    return rows > 0


def save_setting(setting_key, setting_value, description=None):
    setting = get_setting_by_key(setting_key)

    if setting:
        return update_setting_value(setting_key, setting_value)

    setting_id = create_system_setting(
        setting_key,
        setting_value,
        description
    )

    return setting_id is not None
