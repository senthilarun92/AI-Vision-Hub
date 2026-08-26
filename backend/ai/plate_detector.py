from ultralytics import YOLO
import cv2
import os
import uuid


class PlateDetector:

    def __init__(self):

        self.model_path = "backend/weights/plate.pt"
        self.output_folder = "backend/outputs"

        os.makedirs(
            self.output_folder,
            exist_ok=True
        )

        print("=" * 60)
        print("[plate_detector] Loading plate model...")
        print("[plate_detector] Model path:", self.model_path)

        self.model = YOLO(self.model_path)

        print(
            "[plate_detector] Model classes:",
            self.model.names
        )

        print("=" * 60)

    # ============================================================
    # PLATE DETECTION
    # ============================================================

    def detect(self, image):

        if image is None:
            print("[plate_detector] ERROR: Image is None")
            return []

        original_h, original_w = image.shape[:2]

        print("=" * 60)
        print(
            f"[plate_detector] Original image: "
            f"{original_w}x{original_h}"
        )

        # ========================================================
        # YOLO - ORIGINAL IMAGE ONLY
        # ========================================================

        results = self.model.predict(
            source=image,
            conf=0.25,
            iou=0.45,
            imgsz=640,
            max_det=10,
            verbose=False
        )

        result = results[0]

        print(
            "[plate_detector] Detected boxes:",
            len(result.boxes)
        )

        detections = []

        # ========================================================
        # READ DETECTIONS
        # ========================================================

        for box in result.boxes:

            confidence = float(box.conf[0])

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            x1 = max(0, int(x1))
            y1 = max(0, int(y1))
            x2 = min(original_w, int(x2))
            y2 = min(original_h, int(y2))

            width = x2 - x1
            height = y2 - y1

            if width <= 0 or height <= 0:
                continue

            aspect_ratio = width / height

            print("=" * 60)
            print(
                f"[plate_detector] "
                f"conf={confidence:.4f}"
            )

            print(
                f"[plate_detector] "
                f"bbox=({x1},{y1},{x2},{y2})"
            )

            print(
                f"[plate_detector] "
                f"size={width}x{height}"
            )

            print(
                f"[plate_detector] "
                f"aspect_ratio={aspect_ratio:.2f}"
            )

            # ====================================================
            # BASIC FILTER
            # ====================================================

            if width < 40:
                print("[plate_detector] Removed: too small")
                continue

            if height < 10:
                print("[plate_detector] Removed: too short")
                continue

            # ====================================================
            # PLATE CROP
            # ====================================================

            plate_crop = image[
                y1:y2,
                x1:x2
            ]

            if plate_crop.size == 0:
                continue

            # ====================================================
            # SAVE CROP
            # ====================================================

            filename = (
                f"plate_"
                f"{uuid.uuid4().hex[:10]}"
                f".jpg"
            )

            plate_path = os.path.join(
                self.output_folder,
                filename
            )

            cv2.imwrite(
                plate_path,
                plate_crop
            )

            image_url = f"/outputs/{filename}"

            # ====================================================
            # RESULT
            # ====================================================

            detections.append({

                "bbox": [
                    x1,
                    y1,
                    x2,
                    y2
                ],

                "confidence": round(
                    confidence,
                    4
                ),

                "class_id": int(box.cls[0]),

                "class_name": self.model.names.get(
                    int(box.cls[0]),
                    "Number Plate"
                ),

                "image_path": plate_path,

                "image_url": image_url
            })

            print(
                f"[plate_detector] "
                f"Plate crop saved: {plate_path}"
            )

        # ========================================================
        # SORT
        # ========================================================

        detections.sort(
            key=lambda x: x["confidence"],
            reverse=True
        )

        # Maximum 3 plates
        detections = detections[:3]

        print("=" * 60)
        print(
            "[plate_detector] FINAL PLATES:",
            len(detections)
        )

        for i, detection in enumerate(detections):

            print(
                f"[plate_detector] "
                f"Plate {i + 1}: "
                f"confidence={detection['confidence']} "
                f"bbox={detection['bbox']}"
            )

        print("=" * 60)

        return detections

    # ============================================================
    # DRAW DETECTIONS
    # ============================================================

    def draw_detections(
        self,
        image,
        detections
    ):

        output = image.copy()

        for i, detection in enumerate(detections):

            x1, y1, x2, y2 = detection["bbox"]

            confidence = detection["confidence"]

            cv2.rectangle(
                output,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                3
            )

            label = (
                f"Plate {i + 1} "
                f"{confidence:.2f}"
            )

            cv2.putText(
                output,
                label,
                (
                    x1,
                    max(y1 - 10, 25)
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        return output


# ================================================================
# GLOBAL INSTANCE
# ================================================================

plate_detector = PlateDetector()