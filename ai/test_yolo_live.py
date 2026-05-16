import cv2
from flask import Flask, Response
from ultralytics import YOLO

MODEL_PATH = "ai/human_figure_yolo.pt"
CAMERA_PATH = "/dev/video2"

CONFIDENCE_THRESHOLD = 0.50
YOLO_IMAGE_SIZE = 320
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

app = Flask(__name__)

print("[AI] Loading YOLO model...")
model = YOLO(MODEL_PATH)

print("[AI] Opening InnerCam...")
camera = cv2.VideoCapture(CAMERA_PATH, cv2.CAP_V4L2)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
camera.set(cv2.CAP_PROP_FPS, 15)


def generate_frames():
    while True:
        success, frame = camera.read()

        if not success:
            print("[ERROR] Failed to read frame")
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

        ret, buffer = cv2.imencode(
            ".jpg",
            annotated_frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        )

        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


@app.route("/")
def index():
    return """
    <html>
        <head>
            <title>YOLO Mantrap Live Detection</title>
        </head>
        <body style="background:#111; color:white; text-align:center;">
            <h1>YOLO Human Figure Detection</h1>
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


if __name__ == "__main__":
    print("[AI] Starting YOLO Flask stream...")
    print("[AI] Open: http://192.168.1.28:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
