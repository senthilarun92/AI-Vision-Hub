from ultralytics import YOLO
import cv2
import os


# ============================================================
# SETTINGS
# ============================================================

MODEL_PATH = "backend/weights/plate.pt"

IMAGE_PATH = "backend/uploads/26e027ef4764454ead7de03f739efcfa.jpg"

OUTPUT_PATH = "backend/outputs/plate_detection_test.jpg"


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 60)
print("Loading Plate Detection Model...")

model = YOLO(MODEL_PATH)

print("Model loaded successfully.")
print("Classes:", model.names)

print("=" * 60)


# ============================================================
# LOAD IMAGE
# ============================================================

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("ERROR: Image not found!")
    print("Path:", IMAGE_PATH)
    exit()

print("Image loaded.")
print("Image size:", image.shape)


# ============================================================
# RUN DETECTION
# ============================================================

print("=" * 60)
print("Running plate detection...")

results = model.predict(
    source=image,
    conf=0.01,
    imgsz=1280,
    verbose=False
)


# ============================================================
# DRAW ALL DETECTIONS
# ============================================================

result_image = image.copy()

count = 0

for result in results:

    boxes = result.boxes

    if boxes is None:
        continue

    for box in boxes:

        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

        confidence = float(
            box.conf[0].cpu().numpy()
        )

        class_id = int(
            box.cls[0].cpu().numpy()
        )

        class_name = model.names[class_id]

        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)

        count += 1

        print(
            f"Detection {count}: "
            f"conf={confidence:.4f} "
            f"bbox=({x1},{y1},{x2},{y2}) "
            f"size={x2-x1}x{y2-y1}"
        )

        # ----------------------------------------------------
        # Draw box
        # ----------------------------------------------------

        cv2.rectangle(
            result_image,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            3
        )

        # ----------------------------------------------------
        # Label
        # ----------------------------------------------------

        label = f"{class_name} {confidence:.2f}"

        cv2.putText(
            result_image,
            label,
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


# ============================================================
# SAVE RESULT
# ============================================================

os.makedirs(
    "backend/outputs",
    exist_ok=True
)

cv2.imwrite(
    OUTPUT_PATH,
    result_image
)


# ============================================================
# FINAL
# ============================================================

print("=" * 60)
print("TOTAL DETECTIONS:", count)
print("Output saved:")
print(OUTPUT_PATH)
print("=" * 60)