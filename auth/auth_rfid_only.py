import time
import RPi.GPIO as GPIO
from mfrc522 import MFRC522


RFID_RST_PIN = 25

AUTHORIZED_RFID_IDS = {
    682511166205,
    151122205133
}


reader = None


def reset_rfid_hardware():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(RFID_RST_PIN, GPIO.OUT)

    GPIO.output(RFID_RST_PIN, GPIO.LOW)
    time.sleep(1)

    GPIO.output(RFID_RST_PIN, GPIO.HIGH)
    time.sleep(1)


def cleanup_rfid():
    global reader

    try:
        if reader is not None:
            reader.MFRC522_StopCrypto1()
    except Exception:
        pass

    try:
        reset_rfid_hardware()
    except Exception:
        pass

    try:
        GPIO.cleanup(RFID_RST_PIN)
    except Exception:
        pass

    time.sleep(1)


def get_card_id(uid):
    return int("".join(str(value) for value in uid))


try:
    reset_rfid_hardware()

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    reader = MFRC522()

    print("RFID_READY", flush=True)

    while True:
        status, tag_type = reader.MFRC522_Request(reader.PICC_REQIDL)

        if status == reader.MI_OK:
            print("RFID_CARD_DETECTED", flush=True)

            status, uid = reader.MFRC522_Anticoll()

            if status == reader.MI_OK:
                card_id = get_card_id(uid)

                print(f"RFID_UID:{uid}", flush=True)
                print(f"RFID_ID:{card_id}", flush=True)

                if card_id in AUTHORIZED_RFID_IDS:
                    print(f"RFID_OK:{card_id}", flush=True)

                    cleanup_rfid()
                    exit(0)

                print(f"RFID_DENIED:{card_id}", flush=True)

                cleanup_rfid()
                exit(1)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("RFID_STOPPED", flush=True)

    cleanup_rfid()
    exit(1)

except Exception as error:
    print(f"RFID_ERROR:{error}", flush=True)

    cleanup_rfid()
    exit(1)
