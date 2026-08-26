from ultralytics import YOLO
import cv2
import os
import uuid

# ------------------------------------------------------------------
# Model Path (relative to project root — run uvicorn from there)
# ------------------------------------------------------------------

MODEL_PATH = "backend/weights/vehicle.pt"

OUTPUT_FOLDER = "backend/outputs"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ------------------------------------------------------------------
# Load YOLO Model (loaded once when the server starts)
# ------------------------------------------------------------------

print("=" * 60)
print("Loading Vehicle Detection Model...")
print("Model Path:", MODEL_PATH)

model = YOLO(MODEL_PATH)

print("Model Loaded Successfully!")
print("Model Classes:", model.names)
print("=" * 60)


class VehicleDetector:

    def detect(self, image_path: str):

        image = cv2.imread(image_path)

        if image is None:
            raise Exception("Image could not be loaded.")

        results = model.predict(
            source=image,
            conf=0.25,
            iou=0.45,
            verbose=False
        )[0]

        detections = []

        # Per-class counts, e.g. {"car": 3, "motorcycle": 1}
        class_counts = {}

        for box in results.boxes:

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = model.names.get(class_id, "vehicle")

            class_counts[class_name] = class_counts.get(class_name, 0) + 1

            detections.append({
                "vehicle_type": class_name,
                "confidence": round(confidence, 4),
                "bbox": [x1, y1, x2, y2]
            })

            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                image,
                f"{class_name} {confidence:.2f}",
                (x1, max(0, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        # Unique filename every time — never overwrites previous results
        filename = f"vehicle_{uuid.uuid4().hex[:10]}.jpg"
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        cv2.imwrite(output_path, image)

        image_url = f"http://127.0.0.1:8000/outputs/{filename}"

        return {
            "total_vehicles": len(detections),
            "class_counts": class_counts,
            "detections": detections,
            "output_image": image_url
        }


vehicle_detector = VehicleDetector()
