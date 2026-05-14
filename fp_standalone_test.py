from pyfingerprint.pyfingerprint import PyFingerprint

PORT = "/dev/serial0"
BAUD = 57600

try:
    print("Opening fingerprint...")
    f = PyFingerprint(PORT, BAUD, 0xFFFFFFFF, 0x00000000)

    print("Verifying password...")
    if f.verifyPassword():
        print("Fingerprint sensor OK")
    else:
        print("Wrong fingerprint password")

except Exception as e:
    print("Fingerprint error:", e)
