import cv2
import face_recognition
import os
import time

REFERENCE_IMAGE = os.path.expanduser(
    "~/mantrap_project/auth/face_data/reference_face.jpg"
)

FACE_CAM_DEVICE = "/dev/video0"

print("Loading reference image...")

reference_image = face_recognition.load_image_file(REFERENCE_IMAGE)

reference_encodings = face_recognition.face_encodings(reference_image)

print("Reference faces found:", len(reference_encodings))

if len(reference_encodings) == 0:
    print("No face found in reference image")
    exit()

reference_encoding = reference_encodings[0]

cap = cv2.VideoCapture(FACE_CAM_DEVICE, cv2.CAP_V4L2)

if not cap.isOpened():
    print("Camera not opened")
    exit()

print("Look at the camera...")
time.sleep(2)

matched = False

for i in range(30):

    ret, frame = cap.read()

    if not ret or frame is None:
        print("Frame failed")
        continue

    small_frame = cv2.resize(
        frame,
        (0, 0),
        fx=0.5,
        fy=0.5
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

    print(f"Frame {i+1}: Faces found = {len(face_encodings)}")

    for face_encoding in face_encodings:

        match = face_recognition.compare_faces(
            [reference_encoding],
            face_encoding,
            tolerance=0.5
        )[0]

        distance = face_recognition.face_distance(
            [reference_encoding],
            face_encoding
        )[0]

        print(
            "Match:",
            match,
            "| Distance:",
            round(distance, 3)
        )

        if match:
            matched = True
            break

    if matched:
        break

cap.release()

if matched:
    print("FACE_OK")
else:
    print("FACE_FAIL")
