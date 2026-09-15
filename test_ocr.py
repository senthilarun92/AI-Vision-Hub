import cv2
import easyocr
import os

# ============================================================
# OCR TEST
# ============================================================

IMAGE_PATH = "backend/uploads/detected_plate_crop.jpg"

print("=" * 60)
print("LICENSE PLATE OCR TEST")
print("=" * 60)

# ------------------------------------------------------------
# CHECK IMAGE
# ------------------------------------------------------------

if not os.path.exists(IMAGE_PATH):
    print("❌ Detected plate crop not found")
    print("Path:", IMAGE_PATH)
    exit()

print("✅ Detected plate crop found")
print("Image:", IMAGE_PATH)

# ------------------------------------------------------------
# LOAD IMAGE
# ------------------------------------------------------------

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("❌ Could not read image")
    exit()

print("\nOriginal image size")
print("-" * 60)
print("Width :", image.shape[1])
print("Height:", image.shape[0])

# ------------------------------------------------------------
# UPSCALE
# ------------------------------------------------------------

scale = 4

upscaled = cv2.resize(
    image,
    None,
    fx=scale,
    fy=scale,
    interpolation=cv2.INTER_CUBIC
)

# ------------------------------------------------------------
# SAVE UPSCALED IMAGE
# ------------------------------------------------------------

upscaled_path = "backend/uploads/ocr_upscaled.jpg"

cv2.imwrite(
    upscaled_path,
    upscaled
)

print("\n✅ Upscaled image saved")
print("Path:", upscaled_path)

# ------------------------------------------------------------
# GRAYSCALE
# ------------------------------------------------------------

gray = cv2.cvtColor(
    upscaled,
    cv2.COLOR_BGR2GRAY
)

gray_path = "backend/uploads/ocr_gray.jpg"

cv2.imwrite(
    gray_path,
    gray
)

print("✅ Grayscale image saved")
print("Path:", gray_path)

# ------------------------------------------------------------
# THRESHOLD
# ------------------------------------------------------------

threshold = cv2.threshold(
    gray,
    0,
    255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)[1]

threshold_path = "backend/uploads/ocr_threshold.jpg"

cv2.imwrite(
    threshold_path,
    threshold
)

print("✅ Threshold image saved")
print("Path:", threshold_path)

# ------------------------------------------------------------
# LOAD EASY OCR
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("LOADING EASYOCR")
print("=" * 60)

reader = easyocr.Reader(
    ['en'],
    gpu=False
)

print("✅ EasyOCR loaded")

# ------------------------------------------------------------
# OCR FUNCTION
# ------------------------------------------------------------

def run_ocr(image, name):

    print("\n" + "-" * 60)
    print("OCR TEST:", name)
    print("-" * 60)

    results = reader.readtext(
        image,
        detail=1,
        paragraph=False,
        allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )

    if not results:
        print("❌ No text detected")
        return

    print("✅ Text detected")

    for i, result in enumerate(results):

        bbox = result[0]
        text = result[1]
        confidence = result[2]

        print("\nDetection #", i + 1)
        print("Text       :", text)
        print("Confidence :", f"{confidence:.4f}")
        print("Confidence%:", f"{confidence * 100:.2f}%")
        print("Bounding Box:", bbox)


# ------------------------------------------------------------
# RUN OCR ON ORIGINAL CROP
# ------------------------------------------------------------

run_ocr(
    image,
    "Original Plate Crop"
)

# ------------------------------------------------------------
# RUN OCR ON UPSCALED
# ------------------------------------------------------------

run_ocr(
    upscaled,
    "Upscaled Plate Crop"
)

# ------------------------------------------------------------
# RUN OCR ON GRAYSCALE
# ------------------------------------------------------------

run_ocr(
    gray,
    "Grayscale"
)

# ------------------------------------------------------------
# RUN OCR ON THRESHOLD
# ------------------------------------------------------------

run_ocr(
    threshold,
    "Threshold"
)

# ------------------------------------------------------------
# FINISHED
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("OCR TEST COMPLETED")
print("=" * 60)