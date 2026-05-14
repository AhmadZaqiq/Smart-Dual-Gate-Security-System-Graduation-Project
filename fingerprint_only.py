import time
from pyfingerprint.pyfingerprint import PyFingerprint

FINGER_PORT = "/dev/serial0"
FINGER_BAUD = 57600

try:
    finger = PyFingerprint(FINGER_PORT, FINGER_BAUD, 0xFFFFFFFF, 0x00000000)

    if not finger.verifyPassword():
        print("FINGER_FAIL")
        exit(1)

    print("FINGER_READY")
    print("Put finger...")

    start = time.time()
    while not finger.readImage():
        if time.time() - start > 10:
            print("FINGER_TIMEOUT")
            exit(1)
        time.sleep(0.2)

    finger.convertImage(0x01)
    result = finger.searchTemplate()

    position = result[0]
    accuracy = result[1]

    if position >= 0:
        print(f"FINGER_OK:{position}:{accuracy}")
        exit(0)
    else:
        print("FINGER_NOT_FOUND")
        exit(1)

except Exception as e:
    print(f"FINGER_ERROR:{e}")
    exit(1)
