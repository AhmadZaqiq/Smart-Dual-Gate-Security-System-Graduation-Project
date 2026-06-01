import sys
import os
import time
import threading
import signal
import atexit
import math
from pathlib import Path
from collections import deque
import cv2
import numpy as np
import dlib
from flask import Flask, Response, render_template_string, jsonify

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config.settings import FACE_CAM_DEVICE
except ImportError:
    FACE_CAM_DEVICE = "/dev/mantrap-facecam"

PREDICTOR_PATH = "ai/models/shape_predictor_68_face_landmarks.dat"
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

EAR_THRESHOLD = 0.23
GASP_MAR_THRESHOLD = 0.35
BLINKS_MEDIUM = 5
BLINKS_DANGER = 8
GASP_MEDIUM_FRAMES = 2
GASP_DANGER_FRAMES = 5
SHAKE_MEDIUM = 12
SHAKE_DANGER = 22
YAW_MEDIUM = 20
YAW_DANGER = 35
NO_FACE_DANGER_SECONDS = 1.0
MEDIUM_SCORE = 3
DANGER_SCORE = 6

PORT = 5001
HOST = "0.0.0.0"

app = Flask(__name__)
camera = None
latest_frame = None
running = True
frame_lock = threading.Lock()

current_behavior_status = "NORMAL"
current_score = 0
current_reasons = ["OK"]

detector = dlib.get_frontal_face_detector()
try:
    predictor = dlib.shape_predictor(PREDICTOR_PATH)
except Exception as e:
    print(f"[ERROR] Could not load predictor from {PREDICTOR_PATH}: {e}")
    sys.exit(1)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Face & Behavior Monitor</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: white; text-align: center; padding-top: 20px; }
        .container { display: inline-block; background: #1e1e1e; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5); }
        img { border: 3px solid #333; border-radius: 5px; width: 640px; height: 480px; }
        .status-box { margin-top: 15px; padding: 12px; font-size: 22px; font-weight: bold; border-radius: 5px; text-transform: uppercase; }
        .NORMAL { background-color: #2e7d32; }
        .MEDIUM { background-color: #ef6c00; }
        .DANGER { background-color: #c62828; animation: blink 1s infinite; }
        .info-panel { margin-top: 10px; font-size: 14px; color: #aaa; text-align: left; background: #2a2a2a; padding: 10px; border-radius: 5px; }
        @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    </style>
    <script>
        setInterval(function() {
            fetch('/status_api')
                .then(r => r.json())
                .then(d => {
                    var el = document.getElementById("status_display");
                    el.innerText = "STATUS: " + d.status + " (Score: " + d.score + ")";
                    el.className = "status-box " + d.status;
                    document.getElementById("reasons_display").innerText = "Reasons: " + JSON.stringify(d.reasons);
                });
        }, 200);
    </script>
</head>
<body>
    <div class="container">
        <h2>Smart System - Live Behavior Analytics</h2>
        <img src="/video_feed">
        <div id="status_display" class="status-box NORMAL">STATUS: NORMAL</div>
        <div class="info-panel" id="reasons_display">Reasons: ["OK"]</div>
    </div>
</body>
</html>
"""

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def get_points(landmarks):
    return {i: (landmarks.part(i).x, landmarks.part(i).y) for i in range(68)}

def eye_aspect_ratio(points):
    left_eye = [points[i] for i in [36, 37, 38, 39, 40, 41]]
    right_eye = [points[i] for i in [42, 43, 44, 45, 46, 47]]
    def calc_eye(eye):
        v1 = distance(eye[1], eye[5])
        v2 = distance(eye[2], eye[4])
        h = distance(eye[0], eye[3])
        return (v1 + v2) / (2.0 * h) if h != 0 else 0
    return (calc_eye(left_eye) + calc_eye(right_eye)) / 2.0

def mouth_aspect_ratio(points):
    v1 = distance(points[62], points[66])
    v2 = distance(points[63], points[65])
    h = distance(points[60], points[64])
    return (v1 + v2) / (2.0 * h) if h != 0 else 0

def get_head_yaw(points, frame_width, frame_height):
    image_points = np.array([points[30], points[8], points[36], points[45], points[48], points[54]], dtype="double")
    model_points = np.array([(0.0, 0.0, 0.0), (0.0, -330.0, -65.0), (-225.0, 170.0, -135.0), (225.0, 170.0, -135.0), (-150.0, -150.0, -125.0), (150.0, -150.0, -125.0)], dtype="double")
    focal_length = frame_width
    center = (frame_width / 2, frame_height / 2)
    camera_matrix = np.array([[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]], dtype="double")
    success, rotation_vector, _ = cv2.solvePnP(model_points, image_points, camera_matrix, np.zeros((4, 1)), flags=cv2.SOLVEPNP_ITERATIVE)
    if not success: return 0
    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rotation_matrix)
    return angles[1]

def calculate_decision(yaw, avg_movement, blink_count, gasp_frames, face_missing):
    score = 0
    reasons = []
    if face_missing:
        score += 6; reasons.append("FACE_MISSING")
    if abs(yaw) >= YAW_DANGER:
        score += 4; reasons.append("HEAD_TURNED_DANGER")
    elif abs(yaw) >= YAW_MEDIUM:
        score += 2; reasons.append("HEAD_TURNED_MEDIUM")
    if avg_movement >= SHAKE_DANGER:
        score += 4; reasons.append("FACE_SHAKING_DANGER")
    elif avg_movement >= SHAKE_MEDIUM:
        score += 2; reasons.append("FACE_SHAKING_MEDIUM")
    if blink_count >= BLINKS_DANGER:
        score += 4; reasons.append("TOO_MANY_BLINKS")
    elif blink_count >= BLINKS_MEDIUM:
        score += 2; reasons.append("BLINKING_MEDIUM")
    if gasp_frames >= GASP_DANGER_FRAMES:
        score += 4; reasons.append("GASPING_DANGER")
    elif gasp_frames >= GASP_MEDIUM_FRAMES:
        score += 2; reasons.append("GASPING_MEDIUM")

    if score >= DANGER_SCORE: return "DANGER", score, reasons
    if score >= MEDIUM_SCORE: return "MEDIUM", score, reasons
    return "NORMAL", score, reasons

def get_largest_face(faces):
    return max(faces, key=lambda f: (f.right() - f.left()) * (f.bottom() - f.top()))

def get_face_center(face):
    return ((face.left() + face.right()) // 2, (face.top() + face.bottom()) // 2)

def open_camera():
    global camera
    camera = cv2.VideoCapture(FACE_CAM_DEVICE, cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    return camera.isOpened()

def process_loop():
    global latest_frame, current_behavior_status, current_score, current_reasons
    no_face_start = None
    eye_closed = False
    
    # استخدام Deque لتتبع آخر 30 إطار فقط (حوالي ثانيتين) وجعل العدادات تفاعلية ولحظية
    recent_blinks = deque(maxlen=30)
    recent_gasps = deque(maxlen=30)
    movement_history = deque(maxlen=10)
    last_face_center = None

    while running:
        if camera is None: time.sleep(0.1); continue
        success, frame = camera.read()
        if not success or frame is None: continue

        frame_height, frame_width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray, 0)
        current_time = time.time()
        face_missing = False

        if len(faces) == 0:
            if no_face_start is None: no_face_start = current_time
            if current_time - no_face_start >= NO_FACE_DANGER_SECONDS:
                face_missing = True
            recent_blinks.append(0)
            recent_gasps.append(0)
        else:
            no_face_start = None
            face = get_largest_face(faces)
            landmarks = predictor(gray, face)
            points = get_points(landmarks)

            ear = eye_aspect_ratio(points)
            mar = mouth_aspect_ratio(points)
            yaw = get_head_yaw(points, frame_width, frame_height)
            face_center = get_face_center(face)

            avg_movement = 0
            if last_face_center is not None:
                movement_history.append(distance(face_center, last_face_center))
                if movement_history:
                    avg_movement = sum(movement_history) / len(movement_history)
            last_face_center = face_center

            # فحص الرمش اللحظي وإضافته للنافذة الزمنية
            blink_detected = 0
            if ear < EAR_THRESHOLD:
                eye_closed = True
            else:
                if eye_closed: 
                    blink_detected = 1
                eye_closed = False
            recent_blinks.append(blink_detected)

            # فحص الشهقة اللحظية وإضافتها للنافذة الزمنية
            gasp_detected = 1 if mar >= GASP_MAR_THRESHOLD else 0
            recent_gasps.append(gasp_detected)

            # رسم المربع والنقاط للـ Web Stream
            cv2.rectangle(frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 255, 0), 2)
            for n in range(68):
                cv2.circle(frame, points[n], 2, (0, 255, 255), -1)

            # حساب المجموع بناءً على مجموع الأحداث في آخر 30 إطار فقط ليعود السستم طبيعياً
            current_behavior_status, current_score, current_reasons = calculate_decision(
                yaw=yaw, 
                avg_movement=avg_movement, 
                blink_count=sum(recent_blinks), 
                gasp_frames=sum(recent_gasps), 
                face_missing=face_missing
            )

        if face_missing:
            current_behavior_status, current_score, current_reasons = "DANGER", 6, ["FACE_MISSING"]

        with frame_lock:
            latest_frame = frame.copy()
        time.sleep(1 / 15)

def generate_frames():
    while running:
        with frame_lock: frame = None if latest_frame is None else latest_frame.copy()
        if frame is None: time.sleep(0.05); continue
        c = (0, 255, 0) if current_behavior_status == "NORMAL" else (0, 165, 255) if current_behavior_status == "MEDIUM" else (0, 0, 255)
        cv2.putText(frame, f"STATUS: {current_behavior_status} | SCORE: {current_score}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, c, 2)
        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not success: continue
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

@app.route("/")
def index(): return render_template_string(HTML_TEMPLATE)
@app.route("/video_feed")
def video_feed(): return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")
@app.route("/status_api")
def status_api(): return jsonify({"status": current_behavior_status, "score": current_score, "reasons": current_reasons if current_reasons else ["OK"]})

def cleanup():
    global running; running = False
    if camera is not None: camera.release()
def handle_stop_signal(signum, frame): cleanup(); sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_stop_signal); signal.signal(signal.SIGTERM, handle_stop_signal)
    atexit.register(cleanup)
    if not open_camera(): print("[ERROR] Camera failed"); sys.exit(1)
    threading.Thread(target=process_loop, daemon=True).start()
    app.run(host=HOST, port=PORT, debug=False, threaded=True, use_reloader=False)
