import cv2
from backend.ai.plate_detector import plate_detector


IMAGE_PATH = "backend/uploads/26e027ef4764454ead7de03f739efcfa.jpg"


print("=" * 60)
print("PLATE DETECTION + PADDLE OCR INTEGRATION TEST")
print("=" * 60)


# --------------------------------------------------
# LOAD IMAGE
# --------------------------------------------------

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("ERROR: Image not found!")
    print("Path:", IMAGE_PATH)
    exit()

print("Image loaded successfully.")
print("Image size:", image.shape)


# --------------------------------------------------
# RUN PLATE DETECTION + OCR
# --------------------------------------------------

print("=" * 60)
print("RUNNING PLATE DETECTION + OCR...")
print("=" * 60)

detections = plate_detector.detect(image)


# --------------------------------------------------
# FINAL RESULTS
# --------------------------------------------------

print("=" * 60)
print("FINAL RESULTS")
print("=" * 60)

print("Total plates:", len(detections))


for index, detection in enumerate(detections):

    print("-" * 60)
    print("Plate:", index + 1)

    print(
        "Plate Number:",
        detection.get("plate_number", "Not Recognized")
    )

    print(
        "Detection Confidence:",
        detection.get("confidence", 0.0)
    )

    print(
        "OCR Confidence:",
        detection.get("ocr_confidence", 0.0)
    )

    print(
        "Plate Image:",
        detection.get("image_path", "")
    )

    print(
        "Image URL:",
        detection.get("image_url", "")
    )


print("=" * 60)
print("TEST COMPLETED")
print("=" * 60)