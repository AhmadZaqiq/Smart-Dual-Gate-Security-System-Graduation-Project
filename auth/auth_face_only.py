import warnings
warnings.filterwarnings("ignore")

import cv2
import face_recognition
import os
import sys
import time

REFERENCE_IMAGE = os.path.expanduser(
    "~/mantrap_project/auth/face_data/reference_face.jpg"
)

FACE_CAM_DEVICE = "/dev/video0"

print("FACE_READY", flush=True)

if not os.path.exists(REFERENCE_IMAGE):
    print("FACE_FAIL", flush=True)
    sys.exit(1)

reference_image = face_recognition.load_image_file(REFERENCE_IMAGE)
reference_encodings = face_recognition.face_encodings(reference_image)

if len(reference_encodings) == 0:
    print("FACE_FAIL", flush=True)
    sys.exit(1)

reference_encoding = reference_encodings[0]

cap = cv2.VideoCapture(FACE_CAM_DEVICE, cv2.CAP_V4L2)

if not cap.isOpened():
    print("FACE_FAIL", flush=True)
    sys.exit(1)

time.sleep(1)

matched = False

for _ in range(40):
    ret, frame = cap.read()

    if not ret or frame is None:
        continue

    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    face_encodings = face_recognition.face_encodings(
        rgb_frame,
        face_locations
    )

    for face_encoding in face_encodings:
        match = face_recognition.compare_faces(
            [reference_encoding],
            face_encoding,
            tolerance=0.5
        )[0]

        if match:
            matched = True
            break

    if matched:
        break

cap.release()

if matched:
    print("FACE_OK", flush=True)
    sys.exit(0)

print("FACE_FAIL", flush=True)
sys.exit(1)
