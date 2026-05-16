import cv2
import joblib
import numpy as np
from flask import Flask, Response

CAMERA_DEVICE = "/dev/video2"
MODEL_PATH = "ai_person_counter_model_v2.pkl"
IMAGE_SIZE = 128

app = Flask(__name__)

model = joblib.load(MODEL_PATH)

hog = cv2.HOGDescriptor(
    (IMAGE_SIZE, IMAGE_SIZE),
    (16, 16),
    (8, 8),
    (8, 8),
    9
)


def predict_count(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (IMAGE_SIZE, IMAGE_SIZE))

    features = hog.compute(resized).flatten()
    features = np.array([features])

    prediction = model.predict(features)[0]

    return int(prediction)


def generate_frames():
    cap = cv2.VideoCapture(CAMERA_DEVICE, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("[AI] Error: Camera could not be opened")
        return

    print("[AI] Live AI Counter Started")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("[AI] Error: Could not read frame")
            continue

        frame = cv2.resize(frame, (640, 480))

        predicted_count = predict_count(frame)

        cv2.putText(
            frame,
            f"AI Count: {predicted_count}",
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
    print("[AI] Open: http://192.168.1.28:5000")
    app.run(host="0.0.0.0", port=5000)
