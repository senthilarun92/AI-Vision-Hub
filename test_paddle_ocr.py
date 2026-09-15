import cv2
from backend.ai.ocr_engine import ocr_engine


IMAGE_PATH = "backend/uploads/detected_plate_crop.jpg"


print("=" * 60)
print("PADDLE OCR PLATE TEST")
print("=" * 60)

# --------------------------------------------------
# LOAD IMAGE
# --------------------------------------------------

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("❌ Image not found")
    print("Path:", IMAGE_PATH)
    exit()

print("✅ Plate crop found")
print("Image:", IMAGE_PATH)

print("\nImage size")
print("-" * 60)
print("Width :", image.shape[1])
print("Height:", image.shape[0])


# --------------------------------------------------
# RUN OCR
# --------------------------------------------------

print("\n" + "=" * 60)
print("RUNNING PADDLE OCR")
print("=" * 60)

result = ocr_engine.read_plate(image)


# --------------------------------------------------
# RESULT
# --------------------------------------------------

print("\n" + "=" * 60)
print("FINAL RESULT")
print("=" * 60)

print("Plate Number :", result["plate_number"])
print("Confidence   :", result["confidence"])

print("\n" + "=" * 60)
print("RAW OCR RESULTS")
print("=" * 60)

for item in result["raw"]:
    print(
        f"Text={item['text']} | "
        f"Confidence={item['confidence']:.4f} | "
        f"Version={item['version']}"
    )

print("\n" + "=" * 60)
print("TEST COMPLETED")
print("=" * 60)