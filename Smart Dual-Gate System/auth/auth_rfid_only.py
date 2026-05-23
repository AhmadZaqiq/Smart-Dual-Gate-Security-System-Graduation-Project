import time

import RPi.GPIO as GPIO
from mfrc522 import MFRC522

RFID_RST_PIN = 25

AUTHORIZED_RFID_IDS = {
    682511166205,
    151122205133
}

POLL_DELAY = 0.1
RESET_DELAY = 1

reader = None


def setup_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)


def reset_rfid_hardware():
    setup_gpio()

    GPIO.setup(RFID_RST_PIN, GPIO.OUT)

    GPIO.output(RFID_RST_PIN, GPIO.LOW)
    time.sleep(RESET_DELAY)

    GPIO.output(RFID_RST_PIN, GPIO.HIGH)
    time.sleep(RESET_DELAY)

    print("RFID_HARDWARE_RESET", flush=True)


def initialize_reader():
    global reader

    reader = MFRC522()

    print("RFID_READER_INITIALIZED", flush=True)


def cleanup_rfid():
    global reader

    try:
        if reader is not None:
            reader.MFRC522_StopCrypto1()
    except Exception:
        pass

    try:
        GPIO.cleanup(RFID_RST_PIN)
    except Exception:
        pass

    reader = None

    time.sleep(0.5)

    print("RFID_CLEANUP_DONE", flush=True)


def get_card_id(uid):
    return int("".join(str(value) for value in uid))


def wait_for_card():
    while True:
        status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)

        if status == reader.MI_OK:
            print("RFID_CARD_DETECTED", flush=True)
            return True

        time.sleep(POLL_DELAY)


def read_card_uid():
    status, uid = reader.MFRC522_Anticoll()

    if status != reader.MI_OK:
        return None

    return uid


def process_card(uid):
    card_id = get_card_id(uid)

    print(f"RFID_UID:{uid}", flush=True)
    print(f"RFID_ID:{card_id}", flush=True)

    if card_id in AUTHORIZED_RFID_IDS:
        print(f"RFID_OK:{card_id}", flush=True)
        return True

    print(f"RFID_DENIED:{card_id}", flush=True)
    return False


def main():
    try:
        reset_rfid_hardware()
        initialize_reader()

        print("RFID_READY", flush=True)

        while True:
            wait_for_card()

            uid = read_card_uid()

            if uid is None:
                print("RFID_READ_FAILED", flush=True)
                continue

            access_granted = process_card(uid)

            cleanup_rfid()

            if access_granted:
                exit(0)

            exit(1)

    except KeyboardInterrupt:
        print("RFID_STOPPED", flush=True)

        cleanup_rfid()
        exit(1)

    except Exception as error:
        print(f"RFID_ERROR:{error}", flush=True)

        cleanup_rfid()
        exit(1)


if __name__ == "__main__":
    main()
