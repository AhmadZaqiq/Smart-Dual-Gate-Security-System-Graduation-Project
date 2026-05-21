import sys
import time
import subprocess
from pathlib import Path

from pyfingerprint.pyfingerprint import PyFingerprint

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR))

from database.employee_auth_repository import get_employee_by_fingerprint_position

FINGERPRINT_PORT = "/dev/ttyAMA0"
FINGERPRINT_BAUD = 57600

UART_TX_PIN = "14"
UART_RX_PIN = "15"

FINGER_WAIT_DELAY = 0.1
UART_STABILIZE_DELAY = 3


def restore_fingerprint_uart_pins():
    try:
        subprocess.run(["pinctrl", "set", UART_TX_PIN, "a0", "pn"], check=False)
        subprocess.run(["pinctrl", "set", UART_RX_PIN, "a0", "pn"], check=False)

        subprocess.run(
            ["stty", "-F", FINGERPRINT_PORT, str(FINGERPRINT_BAUD)],
            check=False
        )

        print("UART_PINS_RESTORED", flush=True)
        time.sleep(UART_STABILIZE_DELAY)

    except Exception as error:
        print(f"UART_PINS_RESTORE_WARNING:{error}", flush=True)


def initialize_fingerprint_sensor():
    fingerprint = PyFingerprint(FINGERPRINT_PORT, FINGERPRINT_BAUD)

    if not fingerprint.verifyPassword():
        print("FINGER_PASSWORD_FAILED", flush=True)
        return None

    print("FINGER_READY", flush=True)
    return fingerprint


def wait_for_finger(fingerprint):
    print("PUT_FINGER", flush=True)

    while not fingerprint.readImage():
        time.sleep(FINGER_WAIT_DELAY)


def search_fingerprint(fingerprint):
    fingerprint.convertImage(0x01)

    position, accuracy = fingerprint.searchTemplate()

    if position < 0:
        return None, None

    return position, accuracy


def get_employee_id_by_position(position):
    employee = get_employee_by_fingerprint_position(position)

    if not employee:
        return None

    return employee["EmployeeID"]


def main():
    try:
        restore_fingerprint_uart_pins()

        fingerprint = initialize_fingerprint_sensor()

        if fingerprint is None:
            exit(1)

        wait_for_finger(fingerprint)

        position, accuracy = search_fingerprint(fingerprint)

        if position is None:
            print("FINGER_DENIED", flush=True)
            exit(1)

        employee_id = get_employee_id_by_position(position)

        if employee_id is None:
            print(f"FINGER_UNKNOWN_EMPLOYEE:{position}", flush=True)
            exit(1)

        print(f"FINGER_OK:{employee_id}:{position}:{accuracy}", flush=True)
        exit(0)

    except KeyboardInterrupt:
        print("FINGER_STOPPED", flush=True)
        exit(1)

    except Exception as error:
        print(f"FINGER_ERROR:{error}", flush=True)
        exit(1)


if __name__ == "__main__":
    main()
