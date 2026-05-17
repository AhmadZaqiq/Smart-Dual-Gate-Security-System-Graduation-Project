from flask import Flask, Response
import cv2
import os
import time
import threading
import RPi.GPIO as GPIO

CAMERA_PATH = "/dev/video2"
SAVE_DIR = "yolo_dataset/images/raw"

TOTAL_IMAGES = 230
CAPTURE_DELAY = 10
BUZZER_PIN = 17

app = Flask(__name__)

os.makedirs(SAVE_DIR, exist_ok=True)

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

cap = cv2.VideoCapture(CAMERA_PATH, cv2.CAP_V4L2)

latest_frame = None
capture_started = False

def beep():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(0.15)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def camera_loop():
    global latest_frame

    while True:
        ret, frame = cap.read()
        if ret:
            latest_frame = frame

def wait_for_start():
    global capture_started

    input("[INFO] Live is running. Adjust camera, then press ENTER to start capture...")
    capture_started = True

def capture_loop():
    saved_count = len([f for f in os.listdir(SAVE_DIR) if f.endswith(".jpg")])

    while not capture_started:
        time.sleep(0.2)

    print("[INFO] Capture started")

    while saved_count < TOTAL_IMAGES:
        beep()
        print(f"[INFO] Capturing image {saved_count + 1}/{TOTAL_IMAGES} in {CAPTURE_DELAY} seconds...")
        time.sleep(CAPTURE_DELAY)

        if latest_frame is None:
            print("[ERROR] No frame yet")
            continue

        filename = f"{SAVE_DIR}/img_{saved_count:04d}.jpg"
        cv2.imwrite(filename, latest_frame)

        print(f"[INFO] Saved: {filename}")
        saved_count += 1

    print("[INFO] Capture finished")

def generate_frames():
    while True:
        if latest_frame is None:
            time.sleep(0.05)
            continue

        frame = latest_frame.copy()

        status = "LIVE ONLY - Press ENTER in terminal to start"
        if capture_started:
            status = "CAPTURING"

        cv2.putText(frame, status, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )

@app.route("/")
def video():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    threading.Thread(target=camera_loop, daemon=True).start()
    threading.Thread(target=wait_for_start, daemon=True).start()
    threading.Thread(target=capture_loop, daemon=True).start()

    print("[INFO] Open stream:")
    print("[INFO] http://192.168.1.28:5000")

    try:
        app.run(host="0.0.0.0", port=5000)
    finally:
        cap.release()
        GPIO.cleanup()
