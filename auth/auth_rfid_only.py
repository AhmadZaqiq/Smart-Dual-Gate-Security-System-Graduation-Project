import sys
import time
from pathlib import Path

import RPi.GPIO as GPIO
from mfrc522 import MFRC522


PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR / "database"))

from employee_repository import get_employee_by_rfid_uid


GPIO.setwarnings(False)

reader = MFRC522()

print("RFID_READY", flush=True)

try:
    while True:
        status, tag_type = reader.MFRC522_Request(reader.PICC_REQIDL)

        if status == reader.MI_OK:
            print("RFID_CARD_DETECTED", flush=True)

            status, uid = reader.MFRC522_Anticoll()

            if status == reader.MI_OK:
                card_id = int("".join(str(x) for x in uid))

                print(f"RFID_UID:{uid}", flush=True)
                print(f"RFID_ID:{card_id}", flush=True)

                employee = get_employee_by_rfid_uid(str(card_id))

                if employee:
                    print(f"RFID_OK:{employee['EmployeeID']}", flush=True)
                    exit(0)

                print("RFID_DENIED", flush=True)
                exit(1)

        time.sleep(0.2)

except KeyboardInterrupt:
    print("RFID_STOPPED", flush=True)

except Exception as e:
    print(f"RFID_ERROR:{e}", flush=True)
    exit(1)
