from ultralytics import YOLO
import cv2
import os


# ============================================
# PATHS
# ============================================

MODEL_PATH = "backend/weights/plate.pt"
IMAGE_PATH = "backend/uploads/488eec3ea021415f8baa08ed679da5cc.jpg"
OUTPUT_PATH = "backend/outputs/plate_model_test.jpg"


# ============================================
# LOAD MODEL
# ============================================

print("=" * 60)
print("Loading Plate Model...")
print("=" * 60)

model = YOLO(MODEL_PATH)

print("Model loaded!")
print("Classes:", model.names)


# ============================================
# LOAD IMAGE
# ============================================

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("ERROR: Image not found")
    exit()

print("Image size:", image.shape)


# ============================================
# RUN DETECTION
# ============================================

print("=" * 60)
print("Running plate detection...")
print("=" * 60)

results = model.predict(
    source=image,
    conf=0.25,
    imgsz=640,
    iou=0.45,
    max_det=20,
    verbose=False
)


result = results[0]

print("Total boxes:", len(result.boxes))


# ============================================
# PRINT DETECTIONS
# ============================================

for i, box in enumerate(result.boxes):

    confidence = float(box.conf[0])

    class_id = int(box.cls[0])

    x1, y1, x2, y2 = box.xyxy[0].tolist()

    print()
    print("Detection:", i + 1)
    print("Class:", class_id)
    print("Class name:", model.names[class_id])
    print("Confidence:", confidence)
    print(
        "BBox:",
        [
            round(x1),
            round(y1),
            round(x2),
            round(y2)
        ]
    )

    # Draw box

    cv2.rectangle(
        image,
        (int(x1), int(y1)),
        (int(x2), int(y2)),
        (0, 255, 0),
        3
    )

    label = f"Plate {confidence:.3f}"

    cv2.putText(
        image,
        label,
        (int(x1), max(int(y1) - 10, 25)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )


# ============================================
# SAVE RESULT
# ============================================

os.makedirs(
    os.path.dirname(OUTPUT_PATH),
    exist_ok=True
)

cv2.imwrite(
    OUTPUT_PATH,
    image
)

print()
print("=" * 60)
print("Result saved:")
print(OUTPUT_PATH)
print("=" * 60)