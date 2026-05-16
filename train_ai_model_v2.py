import cv2
import os
import numpy as np
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
import joblib

DATASET_PATH = "ai_training"
MODEL_OUTPUT = "ai_person_counter_model_v2.pkl"

IMAGE_SIZE = 128

hog = cv2.HOGDescriptor(
    (IMAGE_SIZE, IMAGE_SIZE),
    (16, 16),
    (8, 8),
    (8, 8),
    9
)

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

        features = hog.compute(resized)
        features = features.flatten()

        X.append(features)
        y.append(int(label))

print(f"[AI] Total training images: {len(X)}")

X = np.array(X)
y = np.array(y)

print("[AI] Training SVM model...")

model = SVC(kernel="linear", probability=True)
model.fit(X, y)

joblib.dump(model, MODEL_OUTPUT)

predictions = model.predict(X)
accuracy = accuracy_score(y, predictions) * 100

print(f"[AI] Model saved as: {MODEL_OUTPUT}")
print(f"[AI] Training Accuracy: {accuracy:.2f}%")
