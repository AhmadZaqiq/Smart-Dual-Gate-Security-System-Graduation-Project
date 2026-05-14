import time
from pyfingerprint.pyfingerprint import PyFingerprint

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
        print(f"FINGER_OK:{position}:{accuracy}", flush=True)
    else:
        print("FINGER_DENIED", flush=True)

    exit(0)

except Exception as e:
    print(f"FINGER_ERROR:{e}", flush=True)
    exit(1)
