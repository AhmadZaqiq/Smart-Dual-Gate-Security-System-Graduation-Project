import cv2
import time
import threading
import os
import signal
import subprocess
import socket
from collections import deque
from flask import Flask, Response
from ultralytics import YOLO

MODEL_PATH = "ai/models/human_figure_yolo.pt"
CAMERA_PATH = "/dev/mantrap-innercam"
CONFIDENCE_THRESHOLD = 0.50

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
YOLO_IMAGE_SIZE = 320
JPEG_QUALITY = 70
CAMERA_FPS = 10

STREAM_HOST = "0.0.0.0"
STREAM_PORT = 5000

app = Flask(__name__)

model = None
camera = None

monitor_running = False
flask_server_started = False

latest_count = 0
latest_frame = None
recent_counts = deque(maxlen=15)

lock = threading.Lock()

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as network_socket:
            network_socket.connect(("8.8.8.8", 80))
            return network_socket.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def get_stream_url():
    return f"http://{get_local_ip()}:{STREAM_PORT}"



def is_monitor_running():
    return monitor_running


def load_model():
    global model

    if model is None:
        print("[AI] Loading YOLO model...", flush=True)
        model = YOLO(MODEL_PATH)
        print("[AI] YOLO model loaded", flush=True)


def get_process_command(pid):
    try:
        cmdline_path = f"/proc/{pid}/cmdline"

        with open(cmdline_path, "rb") as file:
            raw_command = file.read()

        command = raw_command.replace(b"\x00", b" ").decode(errors="ignore").strip()
        return command

    except Exception:
        return ""


def get_camera_owner_pids(camera_path):
    pids = set()

    camera_paths = {
        camera_path,
        os.path.realpath(camera_path),
    }

    for path in camera_paths:
        if not path or not os.path.exists(path):
            continue

        try:
            result = subprocess.run(
                ["fuser", path],
                capture_output=True,
                text=True,
                timeout=3
            )

            output = f"{result.stdout} {result.stderr}"

            for token in output.replace(":", " ").split():
                if token.isdigit():
                    pids.add(int(token))

        except Exception as error:
            print(f"[AI] Failed to check InnerCam owner for {path}: {error}", flush=True)

    return sorted(pids)


def force_release_inner_camera():
    current_pid = os.getpid()
    owner_pids = get_camera_owner_pids(CAMERA_PATH)

    if not owner_pids:
        print("[AI] InnerCam is free", flush=True)
        return

    print(f"[AI] InnerCam owner processes detected: {owner_pids}", flush=True)

    target_pids = []

    for pid in owner_pids:
        if pid == current_pid:
            continue

        command = get_process_command(pid)

        if "main.py" in command:
            print(f"[AI] Skipping main.py process using InnerCam: PID {pid}", flush=True)
            continue

        target_pids.append(pid)
        print(f"[AI] Releasing InnerCam from PID {pid}: {command}", flush=True)

    if not target_pids:
        return

    for pid in target_pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception as error:
            print(f"[AI] Failed to terminate PID {pid}: {error}", flush=True)

    time.sleep(2)

    for pid in target_pids:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        except Exception:
            continue

        try:
            print(f"[AI] Force killing InnerCam owner PID {pid}", flush=True)
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except Exception as error:
            print(f"[AI] Failed to kill PID {pid}: {error}", flush=True)

    time.sleep(1)

def open_camera():
    global camera

    if camera is not None and camera.isOpened():
        return True

    print(f"[AI] Opening InnerCam: {CAMERA_PATH}", flush=True)
    force_release_inner_camera()

    camera = cv2.VideoCapture(CAMERA_PATH, cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    time.sleep(1)

    if not camera.isOpened():
        print("[AI] Failed to open InnerCam", flush=True)
        camera = None
        return False

    print("[AI] InnerCam opened successfully", flush=True)
    return True


def release_camera():
    global camera

    if camera is not None:
        camera.release()
        camera = None
        print("[AI] InnerCam released", flush=True)


def reset_latest_detection():
    global latest_count
    global latest_frame
    global recent_counts

    with lock:
        latest_count = 0
        latest_frame = None
        recent_counts.clear()


def start_room_monitor():
    global monitor_running
    global flask_server_started

    if monitor_running:
        return

    reset_latest_detection()
    load_model()

    if not open_camera():
        return

    monitor_running = True

    monitor_thread = threading.Thread(
        target=room_monitor_loop,
        daemon=True
    )
    monitor_thread.start()

    if not flask_server_started:
        flask_server_started = True

        flask_thread = threading.Thread(
            target=start_flask_server,
            daemon=True
        )
        flask_thread.start()

    print("[AI] YOLO room monitor started", flush=True)
    print(f"[AI] Open stream: {get_stream_url()}", flush=True)


def stop_room_monitor():
    global monitor_running

    monitor_running = False

    time.sleep(0.3)

    release_camera()
    reset_latest_detection()

    try:
        from core import system_status
        system_status.update_status_snapshot(
            yolo_running=False,
            yolo_person_count=0,
            stream_available=False,
        )
    except Exception:
        pass

    print("[AI] YOLO room monitor stopped", flush=True)


def get_detected_count():
    with lock:
        if len(recent_counts) == 0:
            return latest_count

        return max(recent_counts)


def get_latest_detected_count():
    with lock:
        return latest_count

def save_latest_frame_snapshot(output_path):
    with lock:
        if latest_frame is None:
            return False

        frame_copy = latest_frame.copy()

    try:
        cv2.imwrite(str(output_path), frame_copy)
        return True
    except Exception as error:
        print(f"[AI] Failed to save YOLO latest frame snapshot: {error}", flush=True)
        return False


def is_exactly_one_detected():
    return get_detected_count() == 1


def is_invalid_count_detected():
    return get_detected_count() != 1


def room_monitor_loop():
    global latest_count
    global latest_frame

    print("[AI] YOLO monitor loop started", flush=True)

    while monitor_running:
        if camera is None:
            time.sleep(0.2)
            continue

        success, frame = camera.read()

        if not success:
            print("[AI] Failed to read InnerCam frame", flush=True)
            time.sleep(0.2)
            continue

        results = model(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            imgsz=YOLO_IMAGE_SIZE,
            verbose=False
        )

        count = len(results[0].boxes)
        annotated_frame = results[0].plot()

        cv2.putText(
            annotated_frame,
            f"Figures: {count}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        with lock:
            latest_count = count
            recent_counts.append(count)
            latest_frame = annotated_frame.copy()

        try:
            from core import system_status
            system_status.update_status_snapshot(
                yolo_running=True,
                yolo_person_count=get_detected_count(),
                stream_available=True,
            )
        except Exception:
            pass

        time.sleep(0.05)

    print("[AI] YOLO monitor loop stopped", flush=True)


def generate_frames():
    while True:
        with lock:
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


@app.route("/")
def index():
    return """
    <html>
        <head>
            <title>YOLO Mantrap Room Monitor</title>
        </head>
        <body style="background:#111; color:white; text-align:center;">
            <h1>YOLO Room Monitor</h1>
            <h3>InnerCam Live Detection</h3>
            <img src="/video" width="900">
        </body>
    </html>
    """


@app.route("/video")
def video():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def start_flask_server():
    app.run(
        host=STREAM_HOST,
        port=STREAM_PORT,
        debug=False,
        threaded=True,
        use_reloader=False
    )
