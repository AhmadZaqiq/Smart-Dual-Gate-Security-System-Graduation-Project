import sys
import time
from pathlib import Path

from pyfingerprint.pyfingerprint import PyFingerprint


PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR / "database"))

from employee_repository import get_employee_by_fingerprint_position


try:
    fingerprint = PyFingerprint('/dev/serial0', 57600)

    if not fingerprint.verifyPassword():
        print("FINGER_PASSWORD_FAILED", flush=True)
        exit(1)

    print("FINGER_READY", flush=True)
    print("PUT_FINGER", flush=True)

    while not fingerprint.readImage():
        time.sleep(0.1)

    fingerprint.convertImage(0x01)

    result = fingerprint.searchTemplate()

    position = result[0]
    accuracy = result[1]

    if position >= 0:
        employee = get_employee_by_fingerprint_position(position)

        if employee:
            print(
                f"FINGER_OK:"
                f"{employee['EmployeeID']}:"
                f"{position}:"
                f"{accuracy}",
                flush=True
            )

            exit(0)

    print("FINGER_DENIED", flush=True)
    exit(1)

except Exception as e:
    print(f"FINGER_ERROR:{e}", flush=True)
    exit(1)
