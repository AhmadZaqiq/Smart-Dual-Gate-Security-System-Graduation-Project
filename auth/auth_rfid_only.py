import time

import RPi.GPIO as GPIO
from mfrc522 import MFRC522


AUTHORIZED_RFID_IDS = {
    "682511166205",
    "151122205133",
}


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
                card_id_text = str(card_id)

                print(f"RFID_UID:{uid}", flush=True)
                print(f"RFID_ID:{card_id_text}", flush=True)

                if card_id_text in AUTHORIZED_RFID_IDS:
                    print(f"RFID_OK:{card_id_text}", flush=True)
                    exit(0)

                print("RFID_DENIED", flush=True)
                exit(1)

        time.sleep(0.2)

except KeyboardInterrupt:
    print("RFID_STOPPED", flush=True)

except Exception as e:
    print(f"RFID_ERROR:{e}", flush=True)
    exit(1)
