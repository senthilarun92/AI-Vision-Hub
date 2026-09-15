import cv2
import os

IMAGE_PATH = "backend/uploads/ac4a268e74064f75b500aaae820e9f33.jpg"

OUTPUT_PATH = "backend/uploads/plate_test_crop.jpg"
LARGE_OUTPUT_PATH = "backend/uploads/plate_test_crop_large.jpg"

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("❌ Image not found")
    exit()

print("=" * 60)
print("NUMBER PLATE MANUAL CROP TEST")
print("=" * 60)

print("\nOriginal image size")
print("-" * 60)
print("Width :", image.shape[1])
print("Height:", image.shape[0])

# -------------------------------------------------
# MANUAL CROP
# -------------------------------------------------

# Full number plate area
x1 = 180
y1 = 650
x2 = 470
y2 = 850

crop = image[y1:y2, x1:x2]

if crop.size == 0:
    print("❌ Invalid crop coordinates")
    exit()

# -------------------------------------------------
# SAVE ORIGINAL CROP
# -------------------------------------------------

cv2.imwrite(OUTPUT_PATH, crop)

# -------------------------------------------------
# CREATE ENLARGED PREVIEW
# -------------------------------------------------

large_crop = cv2.resize(
    crop,
    None,
    fx=3,
    fy=3,
    interpolation=cv2.INTER_CUBIC
)

cv2.imwrite(LARGE_OUTPUT_PATH, large_crop)

print("\n" + "=" * 60)
print("CROP CREATED SUCCESSFULLY")
print("=" * 60)

print("Crop coordinates")
print("-" * 60)
print("x1 :", x1)
print("y1 :", y1)
print("x2 :", x2)
print("y2 :", y2)

print("\nCrop size")
print("-" * 60)
print("Width :", crop.shape[1])
print("Height:", crop.shape[0])

print("\nSaved files")
print("-" * 60)
print("Crop       :", OUTPUT_PATH)
print("Large crop :", LARGE_OUTPUT_PATH)

print("\n" + "=" * 60)
print("CROP TEST COMPLETED")
print("=" * 60)