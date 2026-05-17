import cv2
import dlib
import time
import math
import numpy as np
from collections import deque
from flask import Flask, Response

try:
    from config.settings import FACE_CAM_DEVICE
except ImportError:
    FACE_CAM_DEVICE = "/dev/video0"


PREDICTOR_PATH = "ai/models/shape_predictor_68_face_landmarks.dat"

ANALYSIS_SECONDS = 5.0
PRINT_INTERVAL = 0.7

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

app = Flask(__name__)

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)

analysis_start_time = time.time()
last_print_time = 0
no_face_start = None

blink_count = 0
eye_closed = False
gasp_frames = 0
max_mar = 0

movement_history = deque(maxlen=10)
last_face_center = None


def distance(p1, p2):
    return math.hypot(
        p1[0] - p2[0],
        p1[1] - p2[1]
    )


def get_points(landmarks):
    return {
        i: (landmarks.part(i).x, landmarks.part(i).y)
        for i in range(68)
    }


def eye_aspect_ratio(points):
    left_eye = [points[i] for i in [36, 37, 38, 39, 40, 41]]
    right_eye = [points[i] for i in [42, 43, 44, 45, 46, 47]]

    def calc_eye(eye):
        a = distance(eye[1], eye[5])
        b = distance(eye[2], eye[4])
        c = distance(eye[0], eye[3])

        if c == 0:
            return 0

        return (a + b) / (2.0 * c)

    return (calc_eye(left_eye) + calc_eye(right_eye)) / 2.0


def mouth_aspect_ratio(points):
    vertical_1 = distance(points[62], points[66])
    vertical_2 = distance(points[63], points[65])
    horizontal = distance(points[60], points[64])

    if horizontal == 0:
        return 0

    return (vertical_1 + vertical_2) / (2.0 * horizontal)


def get_head_yaw(points, frame_width, frame_height):
    image_points = np.array([
        points[30],
        points[8],
        points[36],
        points[45],
        points[48],
        points[54]
    ], dtype="double")

    model_points = np.array([
        (0.0, 0.0, 0.0),
        (0.0, -330.0, -65.0),
        (-225.0, 170.0, -135.0),
        (225.0, 170.0, -135.0),
        (-150.0, -150.0, -125.0),
        (150.0, -150.0, -125.0)
    ], dtype="double")

    focal_length = frame_width
    center = (frame_width / 2, frame_height / 2)

    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype="double")

    success, rotation_vector, translation_vector = cv2.solvePnP(
        model_points,
        image_points,
        camera_matrix,
        np.zeros((4, 1)),
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return 0

    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rotation_matrix)

    yaw = angles[1]

    return yaw


def get_face_movement(face):
    global last_face_center

    center = (
        (face.left() + face.right()) // 2,
        (face.top() + face.bottom()) // 2
    )

    if last_face_center is None:
        last_face_center = center
        return 0

    movement = distance(center, last_face_center)

    last_face_center = center
    movement_history.append(movement)

    if len(movement_history) == 0:
        return 0

    return sum(movement_history) / len(movement_history)


def reset_analysis():
    global analysis_start_time
    global blink_count
    global gasp_frames
    global max_mar
    global last_face_center
    global movement_history

    analysis_start_time = time.time()
    blink_count = 0
    gasp_frames = 0
    max_mar = 0
    last_face_center = None
    movement_history.clear()


def get_final_decision(yaw, avg_movement, face_missing):
    score = 0
    reasons = []

    if face_missing:
        score += 6
        reasons.append("FACE_MISSING")

    if abs(yaw) >= YAW_DANGER:
        score += 4
        reasons.append("HEAD_TURNED_DANGER")
    elif abs(yaw) >= YAW_MEDIUM:
        score += 2
        reasons.append("HEAD_TURNED_MEDIUM")

    if avg_movement >= SHAKE_DANGER:
        score += 4
        reasons.append("FACE_SHAKING_DANGER")
    elif avg_movement >= SHAKE_MEDIUM:
        score += 2
        reasons.append("FACE_SHAKING_MEDIUM")

    if blink_count >= BLINKS_DANGER:
        score += 4
        reasons.append("TOO_MANY_BLINKS")
    elif blink_count >= BLINKS_MEDIUM:
        score += 2
        reasons.append("BLINKING_MEDIUM")

    if gasp_frames >= GASP_DANGER_FRAMES:
        score += 4
        reasons.append("GASPING_DANGER")
    elif gasp_frames >= GASP_MEDIUM_FRAMES:
        score += 2
        reasons.append("GASPING_MEDIUM")

    if score >= DANGER_SCORE:
        return "DANGER", score, reasons

    if score >= MEDIUM_SCORE:
        return "MEDIUM", score, reasons

    return "NORMAL", score, reasons


def draw_landmarks(frame, points):
    for i in range(68):
        cv2.circle(
            frame,
            points[i],
            1,
            (0, 255, 0),
            -1
        )


def draw_frame_info(
    frame,
    status,
    score,
    ear,
    mar,
    yaw,
    avg_movement,
    reasons
):
    color = (0, 255, 0)

    if status == "MEDIUM":
        color = (0, 255, 255)

    elif status == "DANGER":
        color = (0, 0, 255)

    cv2.putText(
        frame,
        f"STATUS: {status}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        color,
        3
    )

    cv2.putText(
        frame,
        f"Score: {score}",
        (20, 85),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2
    )

    cv2.putText(
        frame,
        f"EAR: {ear:.2f} MAR: {mar:.2f}",
        (20, 125),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Blinks: {blink_count} Gasp: {gasp_frames}",
        (20, 165),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Move: {avg_movement:.1f} Yaw: {yaw:.1f}",
        (20, 205),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    reason_text = ",".join(reasons[:2]) if reasons else "OK"

    cv2.putText(
        frame,
        f"Reason: {reason_text}",
        (20, 245),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2
    )


def print_live_status(
    ear,
    mar,
    yaw,
    avg_movement,
    status,
    score,
    reasons
):
    print("\n========== LIVE FACE ANALYSIS ==========")
    print(f"[AI] EAR: {ear:.2f}")
    print(f"[AI] MAR: {mar:.2f}")
    print(f"[AI] Max MAR: {max_mar:.2f}")
    print(f"[AI] Yaw: {yaw:.2f}")
    print(f"[AI] Avg Movement: {avg_movement:.2f}")
    print(f"[AI] Blinks in current window: {blink_count}")
    print(f"[AI] Gasp Frames: {gasp_frames}")
    print(f"[AI] Current STATUS: {status}")
    print(f"[AI] Current Score: {score}")
    print(f"[AI] Reasons: {reasons if reasons else ['OK']}")


def print_final_status(
    status,
    score,
    yaw,
    avg_movement,
    reasons
):
    print("\n========== 5 SECOND FINAL RESULT ==========")
    print(f"[AI] STATUS: {status}")
    print(f"[AI] Score: {score}")
    print(f"[AI] Blinks in 5s: {blink_count}")
    print(f"[AI] Gasp Frames: {gasp_frames}")
    print(f"[AI] Max MAR: {max_mar:.2f}")
    print(f"[AI] Avg Movement: {avg_movement:.2f}")
    print(f"[AI] Yaw: {yaw:.2f}")
    print(f"[AI] Reasons: {reasons if reasons else ['OK']}")


def generate_frames():
    global last_print_time
    global no_face_start
    global blink_count
    global eye_closed
    global gasp_frames
    global max_mar

    cap = cv2.VideoCapture(FACE_CAM_DEVICE, cv2.CAP_V4L2)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("[AI] Balanced face behavior analysis started")

    yaw = 0
    ear = 0
    mar = 0
    avg_movement = 0
    status = "NORMAL"
    score = 0
    reasons = []

    while True:
        ret, frame = cap.read()

        if not ret:
            continue

        now = time.time()

        frame_height, frame_width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = detector(gray, 0)

        face_missing = False

        if len(faces) == 0:
            if no_face_start is None:
                no_face_start = now

            if now - no_face_start >= NO_FACE_DANGER_SECONDS:
                face_missing = True

        else:
            no_face_start = None

            face = max(
                faces,
                key=lambda r: (
                    r.right() - r.left()
                ) * (
                    r.bottom() - r.top()
                )
            )

            landmarks = predictor(gray, face)
            points = get_points(landmarks)

            draw_landmarks(frame, points)

            cv2.rectangle(
                frame,
                (face.left(), face.top()),
                (face.right(), face.bottom()),
                (255, 0, 0),
                2
            )

            ear = eye_aspect_ratio(points)
            mar = mouth_aspect_ratio(points)
            yaw = get_head_yaw(points, frame_width, frame_height)
            avg_movement = get_face_movement(face)

            if mar > max_mar:
                max_mar = mar

            if ear < EAR_THRESHOLD:
                eye_closed = True

            else:
                if eye_closed:
                    blink_count += 1
                    print(
                        f"[AI] Blink detected | Window blinks: {blink_count}"
                    )

                eye_closed = False

            if mar >= GASP_MAR_THRESHOLD:
                gasp_frames += 1
                print(
                    f"[AI] Gasp detected | MAR: {mar:.2f} | Frames: {gasp_frames}"
                )

        elapsed = now - analysis_start_time

        if elapsed >= ANALYSIS_SECONDS:
            status, score, reasons = get_final_decision(
                yaw,
                avg_movement,
                face_missing
            )

            print_final_status(
                status,
                score,
                yaw,
                avg_movement,
                reasons
            )

            reset_analysis()

        if now - last_print_time >= PRINT_INTERVAL:
            print_live_status(
                ear,
                mar,
                yaw,
                avg_movement,
                status,
                score,
                reasons
            )

            last_print_time = now

        draw_frame_info(
            frame,
            status,
            score,
            ear,
            mar,
            yaw,
            avg_movement,
            reasons
        )

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 70]
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
            <title>Balanced Face Behavior Analysis</title>
        </head>

        <body style="background:#111;color:white;text-align:center;">
            <h2>Balanced Face Behavior Analysis</h2>
            <img src="/video" width="640">
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
    app.run(
        host="0.0.0.0",
        port=5001,
        threaded=True,
        debug=False
    )
