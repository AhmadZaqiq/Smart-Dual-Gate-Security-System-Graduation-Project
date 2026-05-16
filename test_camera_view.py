import cv2
from flask import Flask, Response

CAMERA_DEVICE = "/dev/video2"

app = Flask(__name__)


def generate_frames():
    cap = cv2.VideoCapture(CAMERA_DEVICE, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("[TEST] Error: Camera could not be opened")
        return

    while True:
        ret, frame = cap.read()

        if not ret:
            continue

        frame = cv2.resize(frame, (640, 480))

        success, buffer = cv2.imencode(".jpg", frame)

        if not success:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


@app.route("/")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    print("[TEST] Camera View Started")
    print("[TEST] Open: http://192.168.1.28:5000")

    app.run(host="0.0.0.0", port=5000)
