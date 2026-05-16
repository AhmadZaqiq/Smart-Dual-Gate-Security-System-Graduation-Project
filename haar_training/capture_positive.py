import cv2
import os
import time
import RPi.GPIO as GPIO

CAMERA_PATH = "/dev/video2"
SAVE_DIR = "positives"

TOTAL_IMAGES = 500
CAPTURE_DELAY = 3

BUZZER_PIN = 17

os.makedirs(SAVE_DIR, exist_ok=True)

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

cap = cv2.VideoCapture(CAMERA_PATH, cv2.CAP_V4L2)

if not cap.isOpened():
    print("[ERROR] Cannot open camera")
    GPIO.cleanup()
    exit()

count = len([f for f in os.listdir(SAVE_DIR) if f.endswith(".jpg")])

def beep():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(0.15)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

print("[INFO] Positive auto capture started")
print("[INFO] Put ONE figure only")
print("[INFO] No preview because SSH has no display")
print("[INFO] Press CTRL+C to stop")

try:
    while count < TOTAL_IMAGES:
        beep()
        print(f"[INFO] Ready for image {count + 1}/{TOTAL_IMAGES}")
        print("[INFO] Capturing in 3 seconds...")

        time.sleep(CAPTURE_DELAY)

        ret, frame = cap.read()

        if not ret:
            print("[ERROR] Failed to read frame")
            continue

        filename = f"{SAVE_DIR}/pos_{count}.jpg"
        cv2.imwrite(filename, frame)

        print(f"[INFO] Saved: {filename}")
        count += 1

except KeyboardInterrupt:
    print("\n[INFO] Stopped by user")

cap.release()
GPIO.cleanup()

print("[INFO] Positive capture finished")
