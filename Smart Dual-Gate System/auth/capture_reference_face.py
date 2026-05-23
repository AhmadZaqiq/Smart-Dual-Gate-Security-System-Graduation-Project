import cv2
import os
import time

FACE_CAM_DEVICE = "/dev/video0"
SAVE_PATH = os.path.expanduser("~/mantrap_project/auth/face_data/reference_face.jpg")

cap = cv2.VideoCapture(FACE_CAM_DEVICE, cv2.CAP_V4L2)

if not cap.isOpened():
    print("ERROR: Face camera not opened")
    exit(1)

print("Camera opened. Look at the camera...")
time.sleep(2)

for _ in range(10):
    ret, frame = cap.read()

cap.release()

if not ret or frame is None:
    print("ERROR: Failed to capture frame")
    exit(1)

cv2.imwrite(SAVE_PATH, frame)
print(f"Reference face saved: {SAVE_PATH}")
