import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


import atexit
import subprocess

def force_restore_uart_pins_after_rfid():
    try:
        subprocess.run(["pinctrl", "set", "14", "a0"], check=False)
        subprocess.run(["pinctrl", "set", "15", "a0"], check=False)
        print("[RFID_ENROLL] UART pins forced to ALT0 after RFID")
    except Exception as error:
        print(f"[RFID_ENROLL] UART force restore warning: {error}")

atexit.register(force_restore_uart_pins_after_rfid)

"""
RFID enrollment helper.
Waits for any RFID card and writes the detected UID to runtime/enrollment_status.json.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import RPi.GPIO as GPIO
from mfrc522 import MFRC522

from hardware import gpio_map

def restore_uart_after_rfid():
    try:
        import subprocess
        import RPi.GPIO as GPIO

        try:
            GPIO.setwarnings(False)
            GPIO.cleanup()
        except Exception:
            pass

        subprocess.run(["pinctrl", "set", "14", "a0"], check=False)
        subprocess.run(["pinctrl", "set", "15", "a0"], check=False)

        print("[RFID_ENROLL] UART pins restored after RFID")
    except Exception as error:
        print(f"[RFID_ENROLL] UART restore warning: {error}")



PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATUS_FILE = PROJECT_ROOT / "runtime" / "enrollment_status.json"

POLL_DELAY = 0.1
RESET_DELAY = 1
TIMEOUT_SECONDS = 30

reader = None


def write_status(state, message, uid=None):
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "type": "rfid",
        "state": state,
        "message": message,
        "uid": str(uid) if uid is not None else None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(STATUS_FILE, "w", encoding="utf-8") as status_file:
        json.dump(payload, status_file, indent=2)

    print(f"[RFID_ENROLL] {state}: {message}", flush=True)


def setup_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)


def reset_rfid_hardware():
    setup_gpio()

    GPIO.setup(gpio_map.RFID_RST_PIN, GPIO.OUT)

    GPIO.output(gpio_map.RFID_RST_PIN, GPIO.LOW)
    time.sleep(RESET_DELAY)

    GPIO.output(gpio_map.RFID_RST_PIN, GPIO.HIGH)
    time.sleep(RESET_DELAY)

    print("[RFID_ENROLL] RFID hardware reset done", flush=True)


def initialize_reader():
    global reader

    reader = MFRC522()
    print("[RFID_ENROLL] RFID reader initialized", flush=True)


def cleanup_rfid():
    global reader

    try:
        if reader is not None:
            reader.MFRC522_StopCrypto1()
    except Exception:
        pass

    try:
        GPIO.cleanup(gpio_map.RFID_RST_PIN)
    except Exception:
        pass

    reader = None
    time.sleep(0.3)

    print("[RFID_ENROLL] UART pins restored after RFID and cleanup done", flush=True)


def get_card_id(uid):
    return int("".join(str(value) for value in uid))


def main():
    start_time = time.time()

    try:
        write_status("starting", "Starting RFID reader...")
        reset_rfid_hardware()
        initialize_reader()

        write_status("waiting", "Waiting for RFID card...")

        while time.time() - start_time < TIMEOUT_SECONDS:
            status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)

            if status != reader.MI_OK:
                time.sleep(POLL_DELAY)
                continue

            print("[RFID_ENROLL] Card detected", flush=True)

            status, uid_raw = reader.MFRC522_Anticoll()

            if status != reader.MI_OK or uid_raw is None:
                write_status("waiting", "Card detected, but UID read failed. Try again.")
                time.sleep(POLL_DELAY)
                continue

            card_id = get_card_id(uid_raw)

            print(f"[RFID_ENROLL] UID RAW: {uid_raw}", flush=True)
            print(f"[RFID_ENROLL] UID ID: {card_id}", flush=True)

            write_status("success", "RFID card detected successfully.", card_id)
            cleanup_rfid()
            raise SystemExit(0)

        write_status("timeout", "RFID registration timed out. Please try again.")
        cleanup_rfid()
        raise SystemExit(1)

    except KeyboardInterrupt:
        write_status("cancelled", "RFID enrollment cancelled.")
        cleanup_rfid()
        raise SystemExit(1)

    except Exception as error:
        write_status("error", f"RFID enrollment failed: {error}")
        cleanup_rfid()
        raise SystemExit(1)


if __name__ == "__main__":
    main()


restore_uart_after_rfid()
