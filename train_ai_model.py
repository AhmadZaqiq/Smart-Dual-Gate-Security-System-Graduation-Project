import cv2
import os
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import joblib

DATASET_PATH = "ai_training"
MODEL_OUTPUT = "ai_person_counter_model.pkl"

IMAGE_SIZE = 64

X = []
y = []


print("[AI] Loading dataset...")

for label in sorted(os.listdir(DATASET_PATH)):
    label_path = os.path.join(DATASET_PATH, label)

    if not os.path.isdir(label_path):
        continue

    for image_name in os.listdir(label_path):
        image_path = os.path.join(label_path, image_name)

        image = cv2.imread(image_path)

        if image is None:
            continue

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        resized = cv2.resize(gray, (IMAGE_SIZE, IMAGE_SIZE))

        flattened = resized.flatten()

        X.append(flattened)
        y.append(int(label))

print(f"[AI] Total training images: {len(X)}")

X = np.array(X)
y = np.array(y)

print("[AI] Training model...")

model = KNeighborsClassifier(n_neighbors=3)

model.fit(X, y)

joblib.dump(model, MODEL_OUTPUT)

print(f"[AI] Model saved as: {MODEL_OUTPUT}")

predictions = model.predict(X)

accuracy = np.mean(predictions == y) * 100

print(f"[AI] Training Accuracy: {accuracy:.2f}%")
