import subprocess
import time
import RPi.GPIO as GPIO

BUZZER_PIN = 17

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.output(BUZZER_PIN, GPIO.LOW)


def beep(times, delay=0.12):
    for _ in range(times):
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        time.sleep(delay)


def run_script(script_name):
    print(f"\nRunning {script_name}...")

    process = subprocess.Popen(
        ["python3", script_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        print(line, end="")

    process.wait()
    return process.returncode == 0


try:
    print("=== ISOLATED AUTH TEST ===")

    # ================= RFID FIRST =================

    print("\nStep 1: RFID first")

    rfid_ok = run_script("auth_rfid_only.py")

    if not rfid_ok:
        print("RFID failed")
        beep(5)
        exit(1)

    print("RFID success")
    beep(2)

    time.sleep(3)

    # ================= FINGERPRINT SECOND =================

    print("\nStep 2: Fingerprint second")

    finger_ok = run_script("auth_fingerprint_only.py")

    if not finger_ok:
        print("Fingerprint failed")
        beep(5)
        exit(1)

    print("Fingerprint success")
    beep(3)

    print("\nFINAL RESULT: AUTH SUCCESS")

except Exception as e:
    print("MAIN ERROR:", e)
    beep(6)

finally:
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    GPIO.cleanup()
