from ultralytics import YOLO
import cv2
import os

# ============================================================
# PLATE MODEL - MANUAL CROP TEST
# ============================================================

MODEL_PATH = "backend/weights/plate.pt"
IMAGE_PATH = "backend/uploads/plate_test_crop.jpg"

OUTPUT_DIR = "runs/plate_crop_test"
OUTPUT_IMAGE = os.path.join(
    OUTPUT_DIR,
    "plate_detection_result.jpg"
)

DETECTED_CROP = "backend/uploads/detected_plate_crop.jpg"


print("=" * 60)
print("PLATE MODEL - MANUAL CROP TEST")
print("=" * 60)


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(MODEL_PATH):
    print("❌ Plate model not found")
    print("Path:", MODEL_PATH)
    exit()

print("✅ Plate model found")
print("Model:", MODEL_PATH)


if not os.path.exists(IMAGE_PATH):
    print("❌ Crop image not found")
    print("Path:", IMAGE_PATH)
    exit()

print("✅ Crop image found")
print("Image:", IMAGE_PATH)


# ============================================================
# READ IMAGE
# ============================================================

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("❌ Unable to read image")
    exit()

height, width = image.shape[:2]

print("\nCrop Image Size")
print("-" * 60)
print("Width :", width)
print("Height:", height)


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# LOAD MODEL
# ============================================================

print("\n" + "=" * 60)
print("LOADING PLATE MODEL")
print("=" * 60)

model = YOLO(MODEL_PATH)

print("✅ Model loaded successfully")
print("Classes:", model.names)


# ============================================================
# RUN PREDICTION
# ============================================================

print("\n" + "=" * 60)
print("RUNNING PLATE DETECTION")
print("=" * 60)

CONFIDENCE = 0.01
IOU = 0.45
IMAGE_SIZE = 640

print("Confidence :", CONFIDENCE)
print("IoU        :", IOU)
print("Image Size :", IMAGE_SIZE)


results = model.predict(
    source=IMAGE_PATH,
    conf=CONFIDENCE,
    iou=IOU,
    imgsz=IMAGE_SIZE,
    max_det=10,
    save=True,
    project=OUTPUT_DIR,
    name="result",
    exist_ok=True,
    verbose=True
)


# ============================================================
# PROCESS RESULTS
# ============================================================

for result in results:

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)

    total = len(result.boxes)

    print("Total detections:", total)

    if total == 0:

        print("\n❌ NO PLATE DETECTED")

        print("\nPossible reasons:")
        print("1. Plate model is weak")
        print("2. Training dataset is different")
        print("3. Plate angle is difficult")
        print("4. Model was not trained properly")

        continue


    print("\n✅ DETECTIONS FOUND")

    best_box = None
    best_confidence = 0.0


    # ========================================================
    # PRINT ALL DETECTIONS
    # ========================================================

    for i, box in enumerate(result.boxes):

        confidence = float(box.conf[0])

        class_id = int(box.cls[0])

        class_name = model.names.get(
            class_id,
            "Number Plate"
        )

        x1, y1, x2, y2 = box.xyxy[0].tolist()

        x1 = int(max(0, x1))
        y1 = int(max(0, y1))
        x2 = int(min(width, x2))
        y2 = int(min(height, y2))

        box_width = x2 - x1
        box_height = y2 - y1

        aspect_ratio = (
            box_width / box_height
            if box_height > 0
            else 0
        )


        print("\n" + "-" * 60)
        print(f"Detection #{i + 1}")
        print("-" * 60)

        print(f"Confidence   : {confidence:.6f}")
        print(f"Confidence % : {confidence * 100:.2f}%")
        print(f"Class ID     : {class_id}")
        print(f"Class Name   : {class_name}")

        print(
            f"Coordinates  : "
            f"[{x1}, {y1}, {x2}, {y2}]"
        )

        print(f"Width        : {box_width}")
        print(f"Height       : {box_height}")
        print(f"Aspect Ratio : {aspect_ratio:.2f}")


        # Find best detection

        if confidence > best_confidence:

            best_confidence = confidence
            best_box = (
                x1,
                y1,
                x2,
                y2
            )


    # ========================================================
    # BEST DETECTION
    # ========================================================

    if best_box is not None:

        x1, y1, x2, y2 = best_box

        print("\n" + "=" * 60)
        print("BEST PLATE DETECTION")
        print("=" * 60)

        print(
            f"Confidence   : "
            f"{best_confidence:.6f}"
        )

        print(
            f"Confidence % : "
            f"{best_confidence * 100:.2f}%"
        )

        print(
            f"Coordinates   : "
            f"[{x1}, {y1}, {x2}, {y2}]"
        )


        # ====================================================
        # SAVE DETECTED PLATE CROP
        # ====================================================

        detected_crop = image[y1:y2, x1:x2]

        if detected_crop.size > 0:

            cv2.imwrite(
                DETECTED_CROP,
                detected_crop
            )

            crop_h, crop_w = detected_crop.shape[:2]

            print("\n✅ Detected plate crop saved")

            print(
                "Path:",
                DETECTED_CROP
            )

            print(
                "Crop size:",
                crop_w,
                "x",
                crop_h
            )


# ============================================================
# FINISHED
# ============================================================

print("\n" + "=" * 60)
print("TEST COMPLETED")
print("=" * 60)

print("\nAnnotated result saved inside:")

print(
    os.path.join(
        OUTPUT_DIR,
        "result"
    )
)