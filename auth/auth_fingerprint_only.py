import sys
import time
import subprocess
from pathlib import Path

from pyfingerprint.pyfingerprint import PyFingerprint


PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR))
sys.path.append(str(PROJECT_DIR / "database"))

from employee_auth_repository import get_employee_by_fingerprint_position


FINGERPRINT_PORT = "/dev/ttyAMA0"
FINGERPRINT_BAUD = 57600


def restore_fingerprint_uart_pins():
    try:
        subprocess.run(["pinctrl", "set", "14", "a0", "pn"], check=False)
        subprocess.run(["pinctrl", "set", "15", "a0", "pn"], check=False)
        print("UART_PINS_RESTORED", flush=True)
        time.sleep(1)
    except Exception as error:
        print(f"UART_PINS_RESTORE_WARNING:{error}", flush=True)


try:
    restore_fingerprint_uart_pins()

    fingerprint = PyFingerprint(FINGERPRINT_PORT, FINGERPRINT_BAUD)

    if not fingerprint.verifyPassword():
        print("FINGER_PASSWORD_FAILED", flush=True)
        exit(1)

    print("FINGER_READY", flush=True)
    print("PUT_FINGER", flush=True)

    while not fingerprint.readImage():
        time.sleep(0.1)

    fingerprint.convertImage(0x01)

    position, accuracy = fingerprint.searchTemplate()

    if position >= 0:
        employee = get_employee_by_fingerprint_position(position)

        if employee:
            employee_id = employee["EmployeeID"]
            print(f"FINGER_OK:{employee_id}:{position}:{accuracy}", flush=True)
            exit(0)

    print("FINGER_DENIED", flush=True)
    exit(1)

except KeyboardInterrupt:
    print("FINGER_STOPPED", flush=True)
    exit(1)

except Exception as error:
    print(f"FINGER_ERROR:{error}", flush=True)
    exit(1)
