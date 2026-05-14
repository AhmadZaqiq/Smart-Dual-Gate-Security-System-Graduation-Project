import os
import sys
import time
import subprocess
import textwrap
import RPi.GPIO as GPIO
from mfrc522 import MFRC522

AUTHORIZED_RFID_IDS = {
    296276461261,
    650600317217,
}

FINGERPRINT_SCRIPT = "/tmp/fingerprint_check.py"

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


def create_fingerprint_helper():
    code = r'''
import time
import serial
from pyfingerprint.pyfingerprint import PyFingerprint

PORT = "/dev/serial0"
BAUD = 57600

try:
    # Clean serial buffer before PyFingerprint opens it
    ser = serial.Serial(PORT, BAUD, timeout=1)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.close()
    time.sleep(0.2)

    f = PyFingerprint(PORT, BAUD, 0xFFFFFFFF, 0x00000000)

    if not f.verifyPassword():
        print("FP_FAIL_PASSWORD")
        exit(2)

    print("FP_READY")
    start = time.time()

    while time.time() - start < 10:
        if f.readImage():
            f.convertImage(0x01)
            result = f.searchTemplate()
            position = result[0]
            accuracy = result[1]

            if position >= 0:
                print(f"FP_OK position={position} accuracy={accuracy}")
                exit(0)
            else:
                print("FP_NOT_FOUND")
                exit(1)

        time.sleep(0.2)

    print("FP_TIMEOUT")
    exit(1)

except Exception as e:
    print(f"FP_ERROR {e}")
    exit(3)
'''
    with open(FINGERPRINT_SCRIPT, "w") as file:
        file.write(code)


def uid_to_number(uid):
    number = 0
    for part in uid:
        number = number * 256 + part
    return number


def check_rfid(timeout=10):
    print("\n[RFID] Starting RFID check...")
    reader = MFRC522()
    start = time.time()

    while time.time() - start < timeout:
        status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)

        if status == reader.MI_OK:
            status, uid = reader.MFRC522_Anticoll()

            if status == reader.MI_OK:
                card_id = uid_to_number(uid)
                print(f"[RFID] Detected ID: {card_id}")

                if card_id in AUTHORIZED_RFID_IDS:
                    print("[RFID] Accepted")
                    return True
                else:
                    print("[RFID] Rejected")
                    return False

        time.sleep(0.2)

    print("[RFID] Timeout")
    return False


def check_fingerprint():
    print("\n[FINGERPRINT] Starting fingerprint subprocess...")

    result = subprocess.run(
        [sys.executable, FINGERPRINT_SCRIPT],
        capture_output=True,
        text=True,
        timeout=15
    )

    print(result.stdout.strip())

    if result.returncode == 0:
        print("[FINGERPRINT] Accepted")
        return True

    print("[FINGERPRINT] Failed")
    if result.stderr.strip():
        print(result.stderr.strip())

    return False


def main():
    create_fingerprint_helper()

    print("=== RFID + Fingerprint Together Test ===")
    print("Step 1: Scan RFID card/tag")

    rfid_ok = check_rfid()

    if not rfid_ok:
        print("\nFINAL RESULT: FAILED AT RFID")
        return

    print("\nStep 2: Place your finger on AS608 sensor")

    fingerprint_ok = check_fingerprint()

    if not fingerprint_ok:
        print("\nFINAL RESULT: FAILED AT FINGERPRINT")
        return

    print("\nFINAL RESULT: RFID + FINGERPRINT BOTH ACCEPTED")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        # Do not use GPIO.cleanup() here during testing.
        # Full cleanup should only happen when the whole system exits.
        pass
