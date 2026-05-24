"""Standalone FaceCam MJPEG stream server."""

import atexit
import os
import signal
import sys
import threading
import time
from pathlib import Path

import cv2
from flask import Flask, Response, jsonify

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings  # noqa: E402

FACE_DEVICE = settings.FACE_CAM_DEVICE
PORT = int(os.environ.get("FACE_STREAM_PORT", "5001"))
HOST = "0.0.0.0"
PID_FILE = PROJECT_ROOT / "runtime" / "face_stream.pid"

FRAME_WIDTH = 320
FRAME_HEIGHT = 240
FPS = 10
JPEG_QUALITY = 65

app = Flask(__name__)

def open_camera_with_fallback():
    candidates = [
        FACE_DEVICE,
        "/dev/mantrap-facecam",
    ]

    for candidate in candidates:
        print(f"[FACE_STREAM] Trying FaceCam candidate: {candidate}", flush=True)

        cam = cv2.VideoCapture(candidate, cv2.CAP_V4L2)

        if cam.isOpened():
            cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cam.set(cv2.CAP_PROP_FPS, 10)
            cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            ok, frame = cam.read()

            if ok and frame is not None:
                print(f"[FACE_STREAM] FaceCam opened successfully: {candidate}", flush=True)
                return cam

        cam.release()

    return None



camera = None
latest_frame = None
running = True
frame_lock = threading.Lock()


def log(message):
    print(f"[FACE_STREAM] {message}", flush=True)


def write_pid():
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    log(f"PID registered: {os.getpid()}")


def remove_pid():
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
            log("PID file removed")
    except OSError:
        pass


def cleanup():
    global running, camera

    running = False

    if camera is not None:
        try:
            camera.release()
            log("Face camera released")
        except Exception:
            pass
        camera = None

    remove_pid()


def handle_stop_signal(signum, frame):
    log(f"Stop signal received: {signum}")
    cleanup()
    sys.exit(0)


def open_camera():
    global camera, latest_frame

    log(f"Opening FaceCam: {FACE_DEVICE}")

    camera = cv2.VideoCapture(FACE_DEVICE, cv2.CAP_V4L2)

    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, FPS)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    time.sleep(1)

    if not camera.isOpened():
        log("Failed to open FaceCam")
        return False

    for _ in range(20):
        success, frame = camera.read()

        if success and frame is not None:
            with frame_lock:
                latest_frame = frame.copy()

            log("FaceCam opened and first frame received")
            return True

        time.sleep(0.15)

    log("FaceCam opened but no frame received")
    return False


def capture_loop():
    global latest_frame

    while running:
        if camera is None:
            time.sleep(0.2)
            continue

        success, frame = camera.read()

        if success and frame is not None:
            with frame_lock:
                latest_frame = frame.copy()
        else:
            log("Failed to read FaceCam frame")
            time.sleep(0.2)

        time.sleep(1 / FPS)


def has_frame():
    with frame_lock:
        return latest_frame is not None


def generate_frames():
    while running:
        with frame_lock:
            frame = None if latest_frame is None else latest_frame.copy()

        if frame is None:
            time.sleep(0.1)
            continue

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
        )

        if not success:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )


@app.route("/health")
def health():
    return jsonify({
        "running": running,
        "camera": str(FACE_DEVICE),
        "has_frame": has_frame(),
    })


@app.route("/video")
def video():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_stop_signal)
    signal.signal(signal.SIGTERM, handle_stop_signal)
    atexit.register(cleanup)

    if not open_camera():
        cleanup()
        sys.exit(1)

    write_pid()

    threading.Thread(target=capture_loop, daemon=True).start()

    try:
        app.run(host=HOST, port=PORT, debug=False, threaded=True, use_reloader=False)
    finally:
        cleanup()
