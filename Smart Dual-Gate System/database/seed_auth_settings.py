import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.system_setting_repository import save_setting


def seed_authentication_settings():
    settings = [
        (
            "MAX_RFID_ATTEMPTS",
            "3",
            "Maximum RFID failed attempts"
        ),

        (
            "MAX_FINGERPRINT_ATTEMPTS",
            "3",
            "Maximum fingerprint failed attempts"
        ),

        (
            "MAX_FACE_ATTEMPTS",
            "3",
            "Maximum face recognition failed attempts"
        ),

        (
            "MAX_BEHAVIOR_ATTEMPTS",
            "1",
            "Maximum behavior analysis failed attempts"
        ),

        (
            "MAX_AUTH_TOTAL_ATTEMPTS",
            "10",
            "Maximum total authentication failed attempts"
        ),

        (
            "REQUIRE_RFID",
            "1",
            "Require RFID authentication module"
        ),

        (
            "REQUIRE_FINGERPRINT",
            "1",
            "Require fingerprint authentication module"
        ),

        (
            "REQUIRE_FACE_RECOGNITION",
            "1",
            "Require face recognition module"
        ),

        (
            "REQUIRE_BEHAVIOR_ANALYSIS",
            "1",
            "Require behavior analysis module"
        ),
    ]

    for key, value, description in settings:
        save_setting(
            key,
            value,
            description
        )

        print(
            f"[SETTING] {key} = {value}",
            flush=True
        )

    print(
        "[DATABASE] Authentication settings seeded successfully",
        flush=True
    )


if __name__ == "__main__":
    seed_authentication_settings()
