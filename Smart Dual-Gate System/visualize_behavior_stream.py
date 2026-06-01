import cv2
import dlib
import numpy as np
import math
from flask import Flask, Response

CAMERA_PATH = "/dev/mantrap-facecam"
PREDICTOR_PATH = "ai/models/shape_predictor_68_face_landmarks.dat"

app = Flask(__name__)

detector = dlib.get_frontal_face_detector()
try:
    predictor = dlib.shape_predictor(PREDICTOR_PATH)
except Exception as e:
    print(f"[ERROR] Could not load model: {PREDICTOR_PATH}")
    exit(1)

def calculate_ear(eye_points, landmarks):
    p2_p6 = math.dist((landmarks.part(eye_points[1]).x, landmarks.part(eye_points[1]).y),
                      (landmarks.part(eye_points[5]).x, landmarks.part(eye_points[5]).y))
    p3_p5 = math.dist((landmarks.part(eye_points[2]).x, landmarks.part(eye_points[2]).y),
                      (landmarks.part(eye_points[4]).x, landmarks.part(eye_points[4]).y))
    p1_p4 = math.dist((landmarks.part(eye_points[0]).x, landmarks.part(eye_points[0]).y),
                      (landmarks.part(eye_points[3]).x, landmarks.part(eye_points[3]).y))
    return (p2_p6 + p3_p5) / (2.0 * p1_p4)

def calculate_mar(mouth_points, landmarks):
    p2_p8 = math.dist((landmarks.part(mouth_points[1]).x, landmarks.part(mouth_points[1]).y),
                      (landmarks.part(mouth_points[7]).x, landmarks.part(mouth_points[7]).y))
    p3_p7 = math.dist((landmarks.part(mouth_points[2]).x, landmarks.part(mouth_points[2]).y),
                      (landmarks.part(mouth_points[6]).x, landmarks.part(mouth_points[6]).y))
    p4_p6 = math.dist((landmarks.part(mouth_points[3]).x, landmarks.part(mouth_points[3]).y),
                      (landmarks.part(mouth_points[5]).x, landmarks.part(mouth_points[5]).y))
    p1_p5 = math.dist((landmarks.part(mouth_points[0]).x, landmarks.part(mouth_points[0]).y),
                      (landmarks.part(mouth_points[4]).x, landmarks.part(mouth_points[4]).y))
    return (p2_p8 + p3_p7 + p4_p6) / (3.0 * p1_p5)

def generate_frames():
    cap = cv2.VideoCapture(CAMERA_PATH)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        status_text = "BEHAVIOR_NORMAL"
        status_color = (0, 255, 0)

        for face in faces:
            landmarks = predictor(gray, face)
            
            for n in range(0, 68):
                x = landmarks.part(n).x
                y = landmarks.part(n).y
                cv2.circle(frame, (x, y), 2, (255, 255, 0), -1)
            
            left_ear = calculate_ear([36, 37, 38, 39, 40, 41], landmarks)
            right_ear = calculate_ear([42, 43, 44, 45, 46, 47], landmarks)
            avg_ear = (left_ear + right_ear) / 2.0
            mar = calculate_mar([48, 49, 50, 51, 52, 53, 54, 59, 58, 57, 56, 55], landmarks)

            if mar > 0.35 or avg_ear < 0.20:
                status_text = "BEHAVIOR_DANGER"
                status_color = (0, 0, 255)
            elif mar > 0.25 or avg_ear < 0.24:
                status_text = "BEHAVIOR_MEDIUM"
                status_color = (0, 165, 255)

            x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()
            cv2.rectangle(frame, (x1, y1), (x2, y2), status_color, 2)
            cv2.putText(frame, f"EAR: {avg_ear:.2f}", (x1, y1 - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"MAR: {mar:.2f}", (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Risk: {status_text}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

        cv2.rectangle(frame, (10, 10), (320, 85), (0, 0, 0), -1)
        cv2.putText(frame, "AI BEHAVIORAL RISK ANALYSIS", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(frame, f"SYSTEM STATUS: {status_text}", (15, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
        cv2.putText(frame, "MODEL: DLIB-68-LANDMARKS", (15, 74), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

@app.route('/')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
