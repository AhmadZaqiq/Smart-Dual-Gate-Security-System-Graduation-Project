import cv2
import time
import threading
from flask import Flask, Response
from ultralytics import YOLO

MODEL_PATH = "ai/human_figure_yolo.pt"
CAMERA_PATH = "/dev/video2"
CONFIDENCE_THRESHOLD = 0.50

app = Flask(__name__)

model = None
camera = None
monitor_running = False

latest_count = 0
latest_frame = None
lock = threading.Lock()


def load_model():
    global model

    if model is None:
        print("[AI] Loading YOLO model...")
        model = YOLO(MODEL_PATH)
        print("[AI] YOLO model loaded")


def open_camera():
    global camera

    if camera is None:
        camera = cv2.VideoCapture(CAMERA_PATH, cv2.CAP_V4L2)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


def start_room_monitor():
    global monitor_running

    if monitor_running:
        return

    load_model()
    open_camera()

    monitor_running = True

    monitor_thread = threading.Thread(
        target=room_monitor_loop,
        daemon=True
    )

    monitor_thread.start()

    flask_thread = threading.Thread(
        target=start_flask_server,
        daemon=True
    )

    flask_thread.start()

    print("[AI] YOLO room monitor started")
    print("[AI] Open stream: http://192.168.1.28:5000")


def stop_room_monitor():
    global monitor_running

    monitor_running = False
    print("[AI] YOLO room monitor stopped")


def get_detected_count():
    return latest_count


def is_exactly_one_detected():
    return latest_count == 1


def is_multiple_detected():
    return latest_count > 1


def room_monitor_loop():
    global latest_count
    global latest_frame

    while monitor_running:
        success, frame = camera.read()

        if not success:
            print("[AI] Failed to read InnerCam frame")
            time.sleep(0.2)
            continue

        results = model(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            imgsz=320,
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
            latest_frame = annotated_frame.copy()

        time.sleep(0.05)


def generate_frames():
    while True:
        with lock:
            frame = None if latest_frame is None else latest_frame.copy()

        if frame is None:
            time.sleep(0.1)
            continue

        ret, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 70]
        )

        if not ret:
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
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )
