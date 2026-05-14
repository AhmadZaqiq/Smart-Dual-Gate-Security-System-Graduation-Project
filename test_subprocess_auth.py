import time
import subprocess
import RPi.GPIO as GPIO
from mfrc522 import MFRC522

AUTHORIZED_RFID = [682511166205, 151122205133]


def test_rfid(timeout=10):
    print("[RFID] Put card near reader...")

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    reader = MFRC522()
    start = time.time()

    while time.time() - start < timeout:
        status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)

        if status == reader.MI_OK:
            status, uid = reader.MFRC522_Anticoll()

            if status == reader.MI_OK:
                card_id = int("".join(str(x) for x in uid))
                print(f"[RFID] Detected ID: {card_id}")

                if card_id in AUTHORIZED_RFID:
                    print("[RFID] Accepted")
                    return True
                else:
                    print("[RFID] Rejected")
                    return False

        time.sleep(0.1)

    print("[RFID] Timeout")
    return False


def test_fingerprint_subprocess():
    print("\n[FINGER] Starting isolated fingerprint process...")

    result = subprocess.run(
        ["python3", "fingerprint_only.py"],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.stderr:
        print("[STDERR]")
        print(result.stderr)

    return result.returncode == 0


try:
    print("=== RFID + Fingerprint Subprocess Test ===")

    rfid_ok = test_rfid()

    time.sleep(2)

    finger_ok = test_fingerprint_subprocess()

    print("\n=== RESULT ===")
    print(f"RFID: {rfid_ok}")
    print(f"Fingerprint: {finger_ok}")

finally:
    GPIO.cleanup()
    print("GPIO cleaned")
