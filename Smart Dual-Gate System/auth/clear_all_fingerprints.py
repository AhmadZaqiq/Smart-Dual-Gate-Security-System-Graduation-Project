import time
import subprocess

from pyfingerprint.pyfingerprint import PyFingerprint


FINGERPRINT_PORT = "/dev/serial0"
FINGERPRINT_BAUDRATE = 57600


def restore_uart_pins():
    try:
        subprocess.run(["pinctrl", "set", "14", "a0"], check=False)
        subprocess.run(["pinctrl", "set", "15", "a0"], check=False)
        print("UART_PINS_RESTORED")
    except Exception as error:
        print(f"UART_RESTORE_WARNING:{error}")


def open_sensor():
    sensor = PyFingerprint(
        FINGERPRINT_PORT,
        FINGERPRINT_BAUDRATE,
        0xFFFFFFFF,
        0x00000000
    )

    if not sensor.verifyPassword():
        raise Exception("Fingerprint sensor password verification failed")

    return sensor


def main():
    print("CLEAR_FINGERPRINTS_STARTING")
    restore_uart_pins()
    time.sleep(0.5)

    sensor = open_sensor()

    print("FINGER_SENSOR_OPENED")
    print(f"TEMPLATE_COUNT_BEFORE:{sensor.getTemplateCount()}")
    print(f"STORAGE_CAPACITY:{sensor.getStorageCapacity()}")

    deleted_count = 0
    capacity = sensor.getStorageCapacity()

    for position in range(capacity):
        try:
            sensor.deleteTemplate(position)
            deleted_count += 1
            print(f"DELETED_POSITION:{position}")
        except Exception:
            pass

    print(f"DELETED_COUNT:{deleted_count}")
    print(f"TEMPLATE_COUNT_AFTER:{sensor.getTemplateCount()}")
    print("CLEAR_FINGERPRINTS_DONE")


if __name__ == "__main__":
    main()
