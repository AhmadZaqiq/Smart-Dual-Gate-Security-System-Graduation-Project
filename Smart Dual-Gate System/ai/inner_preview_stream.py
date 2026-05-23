"""Standalone InnerCam preview MJPEG — only when YOLO monitor is not active."""

import cv2
import os
import sys
import time
from pathlib import Path

from flask import Flask, Response

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings

INNER_DEVICE = settings.INNER_CAM_DEVICE
PORT = int(os.environ.get("INNER_PREVIEW_PORT", "5002"))
HOST = "0.0.0.0"
PID_FILE = PROJECT_ROOT / "runtime" / "inner_preview_stream.pid"

app = Flask(__name__)
camera = None
latest_frame = None
running = True


def write_pid():
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def remove_pid():
    if PID_FILE.exists():
        PID_FILE.unlink()


def capture_loop():
    global camera, latest_frame, running

    camera = cv2.VideoCapture(INNER_DEVICE, cv2.CAP_V4L2)

    while running and camera.isOpened():
        success, frame = camera.read()
        if success:
            latest_frame = frame
        time.sleep(0.05)

    if camera:
        camera.release()


def generate_frames():
    while running:
        if latest_frame is None:
            time.sleep(0.1)
            continue

        success, buffer = cv2.imencode(".jpg", latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not success:
            continue

        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


@app.route("/video")
def video():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    import threading

    write_pid()
    threading.Thread(target=capture_loop, daemon=True).start()
    time.sleep(1)

    try:
        app.run(host=HOST, port=PORT, debug=False, threaded=True, use_reloader=False)
    finally:
        running = False
        remove_pid()
