import cv2
import os
import time
import sys

CAMERA_DEVICE = "/dev/video2"
BASE_DIR = "ai_training"
CAPTURE_DELAY = 0.3


def get_next_image_number(folder_path):
    files = os.listdir(folder_path)
    jpg_files = [file for file in files if file.endswith(".jpg")]
    return len(jpg_files) + 1


def flush_camera_buffer(cap, frames_count=10):
    for _ in range(frames_count):
        cap.read()
        time.sleep(0.05)


def capture_images(label, count):
    folder_path = os.path.join(BASE_DIR, str(label))
    os.makedirs(folder_path, exist_ok=True)

    cap = cv2.VideoCapture(CAMERA_DEVICE, cv2.CAP_V4L2)

    if not cap.isOpened():
        print("[AI] Error: Camera could not be opened")
        return

    print(f"[AI] Capturing {count} images for label {label}")

    for i in range(count):
        print(f"\n[AI] Prepare image {i + 1}/{count}")
        print(f"[AI] You have {CAPTURE_DELAY} seconds to change position...")
        time.sleep(CAPTURE_DELAY)

        flush_camera_buffer(cap)

        ret, frame = cap.read()

        if not ret:
            print("[AI] Error: Could not read frame")
            continue

        image_number = get_next_image_number(folder_path)
        image_path = os.path.join(folder_path, f"{image_number}.jpg")

        cv2.imwrite(image_path, frame)
        print(f"[AI] Saved: {image_path}")

    cap.release()
    print("\n[AI] Capture finished")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage:")
        print("python3 capture_ai_training.py <label> <count>")
        sys.exit(1)

    label = int(sys.argv[1])
    count = int(sys.argv[2])

    if label not in [0, 1, 2, 3, 4]:
        print("[AI] Error: label must be 0, 1, 2, 3 or 4")
        sys.exit(1)

    capture_images(label, count)
