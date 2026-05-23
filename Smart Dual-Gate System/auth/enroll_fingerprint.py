"""
AS608 fingerprint enrollment helper.
Enrolls a new fingerprint and writes progress to runtime/enrollment_status.json.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from pyfingerprint.pyfingerprint import PyFingerprint

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = PROJECT_ROOT / "runtime" / "enrollment_status.json"

FINGERPRINT_PORT = "/dev/serial0"
FINGERPRINT_BAUDRATE = 57600
TIMEOUT_SECONDS = 45


def write_status(state, message, position=None, step=None, total=None):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "type": "fingerprint",
        "state": state,
        "message": message,
        "position": position,
        "step": step,
        "total": total,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(STATUS_FILE, "w", encoding="utf-8") as status_file:
        json.dump(payload, status_file, indent=2)

    print(f"[FINGER_ENROLL] {state}: {message}", flush=True)


def open_sensor():
    write_status("starting", "Opening fingerprint sensor...", step=1, total=5)

    sensor = PyFingerprint(
        FINGERPRINT_PORT,
        FINGERPRINT_BAUDRATE,
        0xFFFFFFFF,
        0x00000000
    )

    if not sensor.verifyPassword():
        raise RuntimeError("Fingerprint sensor password verification failed.")

    print("[FINGER_ENROLL] Sensor opened and verified", flush=True)
    return sensor


def wait_for_finger(sensor, message, step, total):
    write_status("waiting", message, step=step, total=total)

    start_time = time.time()

    while time.time() - start_time < TIMEOUT_SECONDS:
        if sensor.readImage():
            return True

        time.sleep(0.15)

    return False


def wait_for_remove(sensor):
    write_status("waiting", "Remove finger from sensor...", step=3, total=5)

    start_time = time.time()

    while time.time() - start_time < TIMEOUT_SECONDS:
        if not sensor.readImage():
            return True

        time.sleep(0.15)

    return False


def enroll_fingerprint():
    sensor = open_sensor()

    if not wait_for_finger(
        sensor,
        "Place finger on sensor for first scan...",
        step=2,
        total=5
    ):
        write_status("timeout", "First fingerprint scan timed out.")
        return False

    sensor.convertImage(0x01)
    print("[FINGER_ENROLL] First image converted", flush=True)

    result = sensor.searchTemplate()
    existing_position = result[0]

    if existing_position >= 0:
        write_status(
            "error",
            f"This fingerprint already exists at position {existing_position}.",
            position=existing_position,
            step=2,
            total=5
        )
        return False

    if not wait_for_remove(sensor):
        write_status("timeout", "Finger removal timed out.")
        return False

    if not wait_for_finger(
        sensor,
        "Place the same finger again for second scan...",
        step=4,
        total=5
    ):
        write_status("timeout", "Second fingerprint scan timed out.")
        return False

    sensor.convertImage(0x02)
    print("[FINGER_ENROLL] Second image converted", flush=True)

    if not sensor.compareCharacteristics():
        write_status("error", "Fingerprints did not match. Please retry.", step=4, total=5)
        return False

    sensor.createTemplate()
    position = sensor.storeTemplate()

    write_status(
        "success",
        f"Fingerprint enrolled successfully at position {position}.",
        position=position,
        step=5,
        total=5
    )

    print(f"[FINGER_ENROLL] Stored at position: {position}", flush=True)
    return True


def main():
    try:
        ok = enroll_fingerprint()

        if ok:
            raise SystemExit(0)

        raise SystemExit(1)

    except KeyboardInterrupt:
        write_status("cancelled", "Fingerprint enrollment cancelled.")
        raise SystemExit(1)

    except Exception as error:
        write_status("error", f"Fingerprint enrollment failed: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
