from ultralytics import YOLO
import cv2

MODEL_PATH = r"C:\Users\senth\Downloads\best.pt"
IMAGE_PATH = r"backend\uploads\f33d0d9bdeb244b1a632dd15bb26548b.jpg"

model = YOLO(MODEL_PATH)

image = cv2.imread(IMAGE_PATH)

if image is None:
    print("Image not found!")
    exit()

h, w = image.shape[:2]
print("Original:", w, "x", h)

# Plate area crop
crop = image[250:600, 150:950]

cv2.imwrite("backend/outputs/plate_crop.jpg", crop)

print("Crop saved")

results = model.predict(
    source=crop,
    conf=0.25,
    imgsz=640,
    iou=0.45,
    max_det=10,
    verbose=True
)

result = results[0]

print("==============================")
print("TOTAL BOXES:", len(result.boxes))
print("==============================")

for i, box in enumerate(result.boxes):
    print(
        "Box", i + 1,
        "confidence =", float(box.conf[0]),
        "bbox =", box.xyxy[0].tolist()
    )

result.save(filename="backend/outputs/plate_crop_result.jpg")

print("Result saved")