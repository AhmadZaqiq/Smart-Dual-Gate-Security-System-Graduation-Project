import cv2
from flask import Flask, Response

CAMERA_DEVICE = "/dev/video2"

app = Flask(__name__)

hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())


def generate_frames():
    cap = cv2.VideoCapture(CAMERA_DEVICE, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("[TEST] Error: Camera could not be opened")
        return

    while True:
        ret, frame = cap.read()

        if not ret:
            print("[TEST] Error: Could not read frame")
            continue

        frame = cv2.resize(frame, (640, 480))

        boxes, weights = hog.detectMultiScale(
            frame,
            winStride=(4, 4),
            padding=(8, 8),
            scale=1.05
        )

        count = len(boxes)

        for (x, y, w, h) in boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.putText(
            frame,
            f"People Count: {count}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

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
    print("[TEST] Person Counter Camera View Started")
    print("[TEST] Open this link on your PC:")
    print("[TEST] http://192.168.1.28:5000")

    app.run(host="0.0.0.0", port=5000)
