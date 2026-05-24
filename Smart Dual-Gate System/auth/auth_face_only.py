import os
from pathlib import Path
import sys
import time
import sqlite3
import warnings
from pathlib import Path

import cv2
import face_recognition

warnings.filterwarnings("ignore")


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "database" / "mantrap.db"

try:
    from config.settings import FACE_CAM_DEVICE
except ImportError:
    FACE_CAM_DEVICE = "/dev/mantrap-facecam"

FRAME_SCALE = 0.5
FACE_TOLERANCE = 0.5

MAX_FRAMES_TO_SCAN = 40
CAMERA_WARMUP_DELAY = 1


def get_employee_id():
    if len(sys.argv) >= 2:
        return int(sys.argv[1])

    employee_id = os.environ.get("FACE_EMPLOYEE_ID")

    if employee_id:
        return int(employee_id)

    print("FACE_EMPLOYEE_ID_REQUIRED", flush=True)
    return None


def get_reference_image_path(employee_id):
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT FaceImagePath
            FROM EmployeeAuthentication
            WHERE EmployeeID = ?
            LIMIT 1
            """,
            (employee_id,)
        )

        row = cursor.fetchone()

        if row is None:
            print("FACE_EMPLOYEE_AUTH_NOT_FOUND", flush=True)
            return None

        face_image_path = row["FaceImagePath"]

        if not face_image_path:
            print("FACE_IMAGE_PATH_EMPTY", flush=True)
            return None

        path = Path(face_image_path)

        if not path.is_absolute():
            path = PROJECT_DIR / face_image_path

        return path

    finally:
        connection.close()


def load_reference_encoding(reference_image_path):
    if not reference_image_path.exists():
        print(f"FACE_REFERENCE_NOT_FOUND:{reference_image_path}", flush=True)
        return None

    reference_image = face_recognition.load_image_file(str(reference_image_path))
    reference_encodings = face_recognition.face_encodings(reference_image)

    if len(reference_encodings) == 0:
        print("FACE_REFERENCE_ENCODING_FAILED", flush=True)
        return None

    print("FACE_REFERENCE_READY", flush=True)
    return reference_encodings[0]



def process_frame(frame):
    small_frame = cv2.resize(
        frame,
        (0, 0),
        fx=FRAME_SCALE,
        fy=FRAME_SCALE
    )

    rgb_frame = cv2.cvtColor(
        small_frame,
        cv2.COLOR_BGR2RGB
    )

    face_locations = face_recognition.face_locations(
        rgb_frame,
        model="hog"
    )

    face_encodings = face_recognition.face_encodings(
        rgb_frame,
        face_locations
    )

    return face_encodings


def is_face_match(reference_encoding, face_encoding):
    return face_recognition.compare_faces(
        [reference_encoding],
        face_encoding,
        tolerance=FACE_TOLERANCE
    )[0]


def cleanup_camera(camera):
    if camera is not None:
        camera.release()

    print("FACE_CAMERA_RELEASED", flush=True)









FACE_DEBUG_DIR = Path("runtime/face_debug")
FACE_DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def save_face_debug_frame(frame, name="last_face_auth_frame.jpg"):
    try:
        debug_path = FACE_DEBUG_DIR / name
        cv2.imwrite(str(debug_path), frame)
        print(f"FACE_DEBUG_FRAME_SAVED:{debug_path}", flush=True)
    except Exception as error:
        print(f"FACE_DEBUG_SAVE_FAILED:{error}", flush=True)


def open_face_camera():
    candidates = [
        FACE_CAM_DEVICE,
        "/dev/mantrap-facecam",
    ]

    for candidate in candidates:
        print(f"FACE_TRYING_CAMERA:{candidate}", flush=True)

        camera = cv2.VideoCapture(candidate, cv2.CAP_V4L2)

        if not camera.isOpened():
            print(f"FACE_CAMERA_FAILED:{candidate}", flush=True)
            camera.release()
            continue

        camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"YUYV"))
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 10)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        for _ in range(10):
            ok, frame = camera.read()

            if ok and frame is not None:
                print(f"FACE_CAMERA_OPENED:{candidate}", flush=True)
                save_face_debug_frame(frame, "camera_open_test.jpg")
                return camera

        print(f"FACE_CAMERA_NO_FRAME:{candidate}", flush=True)
        camera.release()

    return None


def open_camera():
    print("FACE_OPENING_CAMERA", flush=True)

    camera = open_face_camera()

    if camera is None:
        print("FACE_CAMERA_OPEN_FAILED", flush=True)

    return camera



def main():
    print("FACE_READY", flush=True)

    employee_id = get_employee_id()

    if employee_id is None:
        print("FACE_FAIL", flush=True)
        sys.exit(1)

    print(f"FACE_EMPLOYEE_ID:{employee_id}", flush=True)

    reference_image_path = get_reference_image_path(employee_id)

    if reference_image_path is None:
        print("FACE_FAIL", flush=True)
        sys.exit(1)

    print(f"FACE_REFERENCE_PATH:{reference_image_path}", flush=True)

    reference_encoding = load_reference_encoding(reference_image_path)

    if reference_encoding is None:
        print("FACE_FAIL", flush=True)
        sys.exit(1)

    camera = open_camera()

    if camera is None:
        print("FACE_FAIL", flush=True)
        sys.exit(1)

    matched = False

    try:
        for frame_number in range(MAX_FRAMES_TO_SCAN):
            success, frame = camera.read()

            if not success or frame is None:
                print(
                    f"FACE_FRAME_READ_FAILED:{frame_number}",
                    flush=True
                )
                continue

            face_encodings = process_frame(frame)

            if len(face_encodings) == 0:
                continue

            for face_encoding in face_encodings:
                if is_face_match(reference_encoding, face_encoding):
                    matched = True
                    print("FACE_MATCH_FOUND", flush=True)
                    break

            if matched:
                break

    finally:
        cleanup_camera(camera)

    if matched:
        print("FACE_OK", flush=True)
        sys.exit(0)

    print("FACE_FAIL", flush=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
