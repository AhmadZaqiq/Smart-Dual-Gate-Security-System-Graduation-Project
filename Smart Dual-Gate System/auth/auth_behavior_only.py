import cv2
import dlib
import math
import os
import sys
import time
from collections import deque

import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.settings import FACE_CAM_DEVICE
except ImportError:
    FACE_CAM_DEVICE = "/dev/video0"

PREDICTOR_PATH = "ai/models/shape_predictor_68_face_landmarks.dat"

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

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
    return math.hypot(
        p1[0] - p2[0],
        p1[1] - p2[1]
    )


def get_points(landmarks):
    return {
        index: (landmarks.part(index).x, landmarks.part(index).y)
        for index in range(68)
    }


def eye_aspect_ratio(points):
    left_eye = [points[index] for index in [36, 37, 38, 39, 40, 41]]
    right_eye = [points[index] for index in [42, 43, 44, 45, 46, 47]]

    def calculate_eye_ratio(eye):
        vertical_1 = distance(eye[1], eye[5])
        vertical_2 = distance(eye[2], eye[4])
        horizontal = distance(eye[0], eye[3])

        if horizontal == 0:
            return 0

        return (vertical_1 + vertical_2) / (2.0 * horizontal)

    left_ratio = calculate_eye_ratio(left_eye)
    right_ratio = calculate_eye_ratio(right_eye)

    return (left_ratio + right_ratio) / 2.0


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

    success, rotation_vector, _ = cv2.solvePnP(
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


def calculate_decision(yaw, avg_movement, blink_count, gasp_frames, face_missing):
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


def load_behavior_models():
    if not os.path.exists(PREDICTOR_PATH):
        print("[BEHAVIOR] Predictor file not found", flush=True)
        return None, None

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(PREDICTOR_PATH)

    return detector, predictor


def open_face_camera():
    camera = cv2.VideoCapture(FACE_CAM_DEVICE, cv2.CAP_V4L2)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not camera.isOpened():
        print("[BEHAVIOR] Failed to open FaceCam", flush=True)
        return None

    print("[BEHAVIOR] FaceCam opened", flush=True)

    return camera


def get_largest_face(faces):
    return max(
        faces,
        key=lambda face: (
            face.right() - face.left()
        ) * (
            face.bottom() - face.top()
        )
    )


def get_face_center(face):
    return (
        (face.left() + face.right()) // 2,
        (face.top() + face.bottom()) // 2
    )


def print_behavior_result(status, score, blink_count, gasp_frames,
                          max_mar, avg_movement, yaw, reasons):
    print("========== BEHAVIOR RESULT ==========", flush=True)
    print(f"[BEHAVIOR] Status: {status}", flush=True)
    print(f"[BEHAVIOR] Score: {score}", flush=True)
    print(f"[BEHAVIOR] Blinks: {blink_count}", flush=True)
    print(f"[BEHAVIOR] Gasp Frames: {gasp_frames}", flush=True)
    print(f"[BEHAVIOR] Max MAR: {max_mar:.2f}", flush=True)
    print(f"[BEHAVIOR] Avg Movement: {avg_movement:.2f}", flush=True)
    print(f"[BEHAVIOR] Yaw: {yaw:.2f}", flush=True)
    print(f"[BEHAVIOR] Reasons: {reasons if reasons else ['OK']}", flush=True)


def run_behavior_check():
    print("BEHAVIOR_READY", flush=True)

    detector, predictor = load_behavior_models()

    if detector is None or predictor is None:
        print("BEHAVIOR_DANGER", flush=True)
        return False

    camera = open_face_camera()

    if camera is None:
        print("BEHAVIOR_DANGER", flush=True)
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
            success, frame = camera.read()

            if not success or frame is None:
                continue

            frame_height, frame_width = frame.shape[:2]

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray, 0)

            current_time = time.time()

            if len(faces) == 0:
                if no_face_start is None:
                    no_face_start = current_time

                if current_time - no_face_start >= NO_FACE_DANGER_SECONDS:
                    face_missing = True

                continue

            no_face_start = None

            face = get_largest_face(faces)
            landmarks = predictor(gray, face)
            points = get_points(landmarks)

            ear = eye_aspect_ratio(points)
            mar = mouth_aspect_ratio(points)
            yaw = get_head_yaw(points, frame_width, frame_height)

            face_center = get_face_center(face)

            if last_face_center is not None:
                movement = distance(face_center, last_face_center)
                movement_history.append(movement)

                if movement_history:
                    avg_movement = sum(movement_history) / len(movement_history)

            last_face_center = face_center

            if mar > max_mar:
                max_mar = mar

            if ear < EAR_THRESHOLD:
                eye_closed = True
            else:
                if eye_closed:
                    blink_count += 1
                    print(
                        f"[BEHAVIOR] Blink detected | Count: {blink_count}",
                        flush=True
                    )

                eye_closed = False

            if mar >= GASP_MAR_THRESHOLD:
                gasp_frames += 1
                print(
                    f"[BEHAVIOR] Gasp detected | MAR: {mar:.2f}",
                    flush=True
                )

        status, score, reasons = calculate_decision(
            yaw=yaw,
            avg_movement=avg_movement,
            blink_count=blink_count,
            gasp_frames=gasp_frames,
            face_missing=face_missing
        )

        print_behavior_result(
            status=status,
            score=score,
            blink_count=blink_count,
            gasp_frames=gasp_frames,
            max_mar=max_mar,
            avg_movement=avg_movement,
            yaw=yaw,
            reasons=reasons
        )

        if status == "NORMAL":
            print("BEHAVIOR_NORMAL", flush=True)
            return True

        if status == "MEDIUM":
            print("BEHAVIOR_MEDIUM", flush=True)
            return True

        print("BEHAVIOR_DANGER", flush=True)
        return False

    finally:
        camera.release()
        print("[BEHAVIOR] FaceCam released", flush=True)


if __name__ == "__main__":
    result = run_behavior_check()

    if result:
        sys.exit(0)

    sys.exit(1)
