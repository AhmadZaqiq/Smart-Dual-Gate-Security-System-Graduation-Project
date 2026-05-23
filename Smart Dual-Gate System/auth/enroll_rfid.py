"""
RFID enrollment helper — waits for card and writes status to runtime file.
Run as subprocess only.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATUS_FILE = PROJECT_ROOT / "runtime" / "enrollment_status.json"


def write_status(state, message, uid=None):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": "rfid",
        "state": state,
        "message": message,
        "uid": uid,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as status_file:
        json.dump(payload, status_file, indent=2)


def main():
    write_status("waiting", "Waiting for RFID card...")

    try:
        import RPi.GPIO as GPIO
        from mfrc522 import MFRC522
    except ImportError:
        write_status("error", "RFID hardware libraries are unavailable on this machine.")
        return 1

    try:
        from hardware import gpio_map

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(gpio_map.RFID_RST_PIN, GPIO.OUT)
        reader = MFRC522()

        deadline = time.time() + 60

        while time.time() < deadline:
            (status, _) = reader.MFRC522_Request(reader.PICC_REQIDL)

            if status == reader.MI_OK:
                (status, uid_raw) = reader.MFRC522_Anticoll()
                if status == reader.MI_OK:
                    card_id = "".join(f"{byte:02X}" for byte in uid_raw)
                    write_status("success", "RFID card detected successfully.", card_id)
                    return 0

            time.sleep(0.2)

        write_status("timeout", "RFID registration timed out. Please try again.")
        return 2
    except Exception as error:
        write_status("error", f"RFID enrollment failed: {error}")
        return 1
    finally:
        try:
            GPIO.cleanup()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
