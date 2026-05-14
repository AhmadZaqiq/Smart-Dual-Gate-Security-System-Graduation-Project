import time
import RPi.GPIO as GPIO
from mfrc522 import MFRC522

AUTHORIZED_RFID = [682511166205, 151122205133]
RFID_RST_PIN = 25

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Hard reset for RC522
GPIO.setup(RFID_RST_PIN, GPIO.OUT)
GPIO.output(RFID_RST_PIN, GPIO.LOW)
time.sleep(0.5)
GPIO.output(RFID_RST_PIN, GPIO.HIGH)
time.sleep(0.5)

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

                print(f"RFID_ID:{card_id}", flush=True)

                if card_id in AUTHORIZED_RFID:
                    print("RFID_OK", flush=True)
                    exit(0)
                else:
                    print("RFID_DENIED", flush=True)
                    exit(1)

        time.sleep(0.2)

except Exception as e:
    print(f"RFID_ERROR:{e}", flush=True)
    exit(1)
