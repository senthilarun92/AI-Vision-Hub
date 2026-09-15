from ultralytics import YOLO
import cv2
import os
import uuid

from backend.ai.ocr_engine import ocr_engine


class PlateDetector:

    def __init__(self):

        # ============================================================
        # MODEL PATH
        # ============================================================

        self.model_path = "backend/weights/plate.pt"

        # ============================================================
        # OUTPUT FOLDERS
        # ============================================================

        self.output_folder = "backend/outputs"

        self.plates_folder = os.path.join(
            self.output_folder,
            "plates"
        )

        os.makedirs(
            self.output_folder,
            exist_ok=True
        )

        os.makedirs(
            self.plates_folder,
            exist_ok=True
        )

        # ============================================================
        # WEBSITE BASE URL
        # ============================================================

        self.base_url = "http://127.0.0.1:8000"

        # ============================================================
        # LOAD YOLO MODEL
        # ============================================================

        print("=" * 60)
        print("[plate_detector] Loading plate model...")
        print("[plate_detector] Model path:", self.model_path)

        self.model = YOLO(
            self.model_path
        )

        print(
            "[plate_detector] Model classes:",
            self.model.names
        )

        print(
            "[plate_detector] Plates folder:",
            self.plates_folder
        )

        print("=" * 60)


    # ============================================================
    # PLATE DETECTION + OCR
    # ============================================================

    def detect(self, image):

        # ========================================================
        # CHECK IMAGE
        # ========================================================

        if image is None:

            print(
                "[plate_detector] ERROR: Image is None"
            )

            return []


        # ========================================================
        # ORIGINAL IMAGE SIZE
        # ========================================================

        original_h, original_w = image.shape[:2]

        print("=" * 60)

        print(
            "[plate_detector] Starting plate detection..."
        )

        print(
            f"[plate_detector] Original image: "
            f"{original_w}x{original_h}"
        )


        # ========================================================
        # YOLO PREDICTION
        # ========================================================

        try:

            results = self.model.predict(

                source=image,

                conf=0.25,

                iou=0.45,

                imgsz=640,

                max_det=10,

                verbose=False
            )

        except Exception as e:

            print(
                "[plate_detector] YOLO ERROR:",
                str(e)
            )

            return []


        # ========================================================
        # CHECK RESULT
        # ========================================================

        if not results:

            print(
                "[plate_detector] No YOLO result returned."
            )

            return []


        result = results[0]

        print(
            "[plate_detector] Detected boxes:",
            len(result.boxes)
        )


        # ========================================================
        # DETECTION LIST
        # ========================================================

        detections = []


        # ========================================================
        # PROCESS EACH DETECTION
        # ========================================================

        for box_index, box in enumerate(
            result.boxes
        ):

            print("-" * 60)

            print(
                f"[plate_detector] Processing detection "
                f"#{box_index + 1}"
            )


            # ====================================================
            # CONFIDENCE
            # ====================================================

            confidence = float(
                box.conf[0]
            )


            # ====================================================
            # BOUNDING BOX
            # ====================================================

            x1, y1, x2, y2 = (
                box.xyxy[0].tolist()
            )

            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)


            # ====================================================
            # KEEP BBOX INSIDE IMAGE
            # ====================================================

            x1 = max(
                0,
                x1
            )

            y1 = max(
                0,
                y1
            )

            x2 = min(
                original_w,
                x2
            )

            y2 = min(
                original_h,
                y2
            )


            # ====================================================
            # WIDTH / HEIGHT
            # ====================================================

            width = x2 - x1
            height = y2 - y1


            print(
                f"[plate_detector] Confidence: "
                f"{confidence:.4f}"
            )

            print(
                f"[plate_detector] BBOX: "
                f"({x1}, {y1}, {x2}, {y2})"
            )

            print(
                f"[plate_detector] Size: "
                f"{width}x{height}"
            )


            # ====================================================
            # INVALID BBOX
            # ====================================================

            if width <= 0 or height <= 0:

                print(
                    "[plate_detector] Removed: invalid bbox"
                )

                continue


            # ====================================================
            # BASIC SIZE FILTER
            # ====================================================

            if width < 40:

                print(
                    "[plate_detector] Removed: "
                    "plate width too small"
                )

                continue


            if height < 10:

                print(
                    "[plate_detector] Removed: "
                    "plate height too small"
                )

                continue


            # ====================================================
            # ASPECT RATIO
            # ====================================================

            aspect_ratio = width / height

            print(
                f"[plate_detector] Aspect ratio: "
                f"{aspect_ratio:.2f}"
            )


            # ====================================================
            # CROP PLATE
            # ====================================================

            plate_crop = image[
                y1:y2,
                x1:x2
            ]


            # ====================================================
            # CHECK CROP
            # ====================================================

            if plate_crop is None:

                print(
                    "[plate_detector] Removed: "
                    "crop is None"
                )

                continue


            if plate_crop.size == 0:

                print(
                    "[plate_detector] Removed: "
                    "empty crop"
                )

                continue


            # ====================================================
            # SAVE PLATE CROP
            # ====================================================

            filename = (
                "plate_"
                + uuid.uuid4().hex[:10]
                + ".jpg"
            )

            plate_path = os.path.join(
                self.plates_folder,
                filename
            )


            save_success = cv2.imwrite(
                plate_path,
                plate_crop
            )


            if not save_success:

                print(
                    "[plate_detector] ERROR: "
                    "Failed to save plate image"
                )

                continue


            if not os.path.exists(
                plate_path
            ):

                print(
                    "[plate_detector] ERROR: "
                    "Saved file not found"
                )

                continue


            # ====================================================
            # WEBSITE URL
            # ====================================================

            image_url = (
                f"{self.base_url}"
                f"/outputs/plates/"
                f"{filename}"
            )


            # ====================================================
            # CLASS ID
            # ====================================================

            class_id = int(
                box.cls[0]
            )


            # ====================================================
            # CLASS NAME
            # ====================================================

            class_name = self.model.names.get(
                class_id,
                "Number Plate"
            )


            # ====================================================
            # OCR
            # ====================================================

            print("-" * 60)

            print(
                "[plate_detector] Starting PaddleOCR..."
            )

            try:

                ocr_result = ocr_engine.read_plate(
                    plate_crop
                )

            except Exception as e:

                print(
                    "[plate_detector] OCR ERROR:",
                    str(e)
                )

                ocr_result = {
                    "plate_number": "Not Recognized",
                    "confidence": 0.0,
                    "raw": []
                }


            # ====================================================
            # OCR RESULT
            # ====================================================

            plate_number = ocr_result.get(
                "plate_number",
                "Not Recognized"
            )

            ocr_confidence = float(
                ocr_result.get(
                    "confidence",
                    0.0
                )
            )


            print(
                "[plate_detector] OCR Plate:",
                plate_number
            )

            print(
                "[plate_detector] OCR Confidence:",
                ocr_confidence
            )


            # ====================================================
            # CREATE DETECTION OBJECT
            # ====================================================

            detection = {

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

                "class_id": class_id,

                "class_name": class_name,

                # Plate crop local path
                "image_path": plate_path,

                # Browser URL
                "image_url": image_url,

                # OCR result
                "plate_number": plate_number,

                "ocr_confidence": round(
                    ocr_confidence,
                    4
                ),

                # Raw OCR results
                "ocr_raw": ocr_result.get(
                    "raw",
                    []
                )
            }


            detections.append(
                detection
            )


            # ====================================================
            # SUCCESS LOG
            # ====================================================

            print(
                "[plate_detector] Plate processing completed."
            )

            print(
                "[plate_detector] Plate:",
                plate_number
            )

            print(
                "[plate_detector] Plate confidence:",
                confidence
            )

            print(
                "[plate_detector] OCR confidence:",
                ocr_confidence
            )

            print(
                "[plate_detector] Local path:",
                plate_path
            )

            print(
                "[plate_detector] Website URL:",
                image_url
            )


        # ========================================================
        # SORT
        # ========================================================

        detections.sort(
            key=lambda x: x["confidence"],
            reverse=True
        )


        # ========================================================
        # MAXIMUM 3 PLATES
        # ========================================================

        detections = detections[:3]


        # ========================================================
        # FINAL OUTPUT
        # ========================================================

        print("=" * 60)

        print(
            "[plate_detector] FINAL PLATES:",
            len(detections)
        )


        for index, detection in enumerate(
            detections
        ):

            print(
                f"[plate_detector] Plate {index + 1}"
            )

            print(
                "  Plate:",
                detection["plate_number"]
            )

            print(
                "  Detection Confidence:",
                detection["confidence"]
            )

            print(
                "  OCR Confidence:",
                detection["ocr_confidence"]
            )

            print(
                "  BBOX:",
                detection["bbox"]
            )

            print(
                "  Local path:",
                detection["image_path"]
            )

            print(
                "  Website URL:",
                detection["image_url"]
            )


        print("=" * 60)


        # ========================================================
        # RETURN
        # ========================================================

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


        for i, detection in enumerate(
            detections
        ):

            x1, y1, x2, y2 = (
                detection["bbox"]
            )

            detection_confidence = (
                detection["confidence"]
            )

            plate_number = detection.get(
                "plate_number",
                "Not Recognized"
            )

            ocr_confidence = detection.get(
                "ocr_confidence",
                0.0
            )


            # ====================================================
            # DRAW RECTANGLE
            # ====================================================

            cv2.rectangle(

                output,

                (x1, y1),

                (x2, y2),

                (0, 255, 0),

                3
            )


            # ====================================================
            # LABEL
            # ====================================================

            label = (
                f"{plate_number} "
                f"({ocr_confidence:.2f})"
            )


            # ====================================================
            # DRAW LABEL
            # ====================================================

            cv2.putText(

                output,

                label,

                (
                    x1,
                    max(
                        y1 - 10,
                        25
                    )
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