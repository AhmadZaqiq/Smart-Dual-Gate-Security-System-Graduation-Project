import cv2
import dlib
import time
import math
import numpy as np
from collections import deque
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.settings import FACE_CAM_DEVICE
except ImportError:
    FACE_CAM_DEVICE = "/dev/video0"


PREDICTOR_PATH = "ai/models/shape_predictor_68_face_landmarks.dat"

ANALYSIS_SECONDS = 5.0

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


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


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

    return angles[1]


def calculate_decision(
    yaw,
    avg_movement,
    blink_count,
    gasp_frames,
    face_missing
):
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


def run_behavior_check():
    print("BEHAVIOR_READY")

    if not os.path.exists(PREDICTOR_PATH):
        print("[BEHAVIOR] Predictor file not found")
        print("BEHAVIOR_DANGER")
        return False

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(PREDICTOR_PATH)

    cap = cv2.VideoCapture(FACE_CAM_DEVICE, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("[BEHAVIOR] Failed to open FaceCam")
        print("BEHAVIOR_DANGER")
        return False

    start_time = time.time()
    no_face_start = None

    blink_count = 0
    eye_closed = False
    gasp_frames = 0
    max_mar = 0

    movement_history = deque(maxlen=10)
    last_face_center = None

    yaw = 0
    avg_movement = 0
    face_missing = False

    try:
        while time.time() - start_time < ANALYSIS_SECONDS:
            ret, frame = cap.read()

            if not ret:
                continue

            frame_height, frame_width = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray, 0)

            now = time.time()

            if len(faces) == 0:
                if no_face_start is None:
                    no_face_start = now

                if now - no_face_start >= NO_FACE_DANGER_SECONDS:
                    face_missing = True

                continue

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

            ear = eye_aspect_ratio(points)
            mar = mouth_aspect_ratio(points)
            yaw = get_head_yaw(points, frame_width, frame_height)

            face_center = (
                (face.left() + face.right()) // 2,
                (face.top() + face.bottom()) // 2
            )

            if last_face_center is not None:
                movement = distance(face_center, last_face_center)
                movement_history.append(movement)

                if len(movement_history) > 0:
                    avg_movement = sum(movement_history) / len(movement_history)

            last_face_center = face_center

            if mar > max_mar:
                max_mar = mar

            if ear < EAR_THRESHOLD:
                eye_closed = True
            else:
                if eye_closed:
                    blink_count += 1
                    print(f"[BEHAVIOR] Blink detected | Count: {blink_count}")
                eye_closed = False

            if mar >= GASP_MAR_THRESHOLD:
                gasp_frames += 1
                print(f"[BEHAVIOR] Gasp detected | MAR: {mar:.2f}")

        status, score, reasons = calculate_decision(
            yaw,
            avg_movement,
            blink_count,
            gasp_frames,
            face_missing
        )

        print("========== BEHAVIOR RESULT ==========")
        print(f"[BEHAVIOR] Status: {status}")
        print(f"[BEHAVIOR] Score: {score}")
        print(f"[BEHAVIOR] Blinks: {blink_count}")
        print(f"[BEHAVIOR] Gasp Frames: {gasp_frames}")
        print(f"[BEHAVIOR] Max MAR: {max_mar:.2f}")
        print(f"[BEHAVIOR] Avg Movement: {avg_movement:.2f}")
        print(f"[BEHAVIOR] Yaw: {yaw:.2f}")
        print(f"[BEHAVIOR] Reasons: {reasons if reasons else ['OK']}")

        if status == "NORMAL":
            print("BEHAVIOR_NORMAL")
            return True

        if status == "MEDIUM":
            print("BEHAVIOR_MEDIUM")
            return True

        print("BEHAVIOR_DANGER")
        return False

    finally:
        cap.release()


if __name__ == "__main__":
    ok = run_behavior_check()

    if ok:
        sys.exit(0)

    sys.exit(1)
