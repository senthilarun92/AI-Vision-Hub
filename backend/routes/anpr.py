from fastapi import APIRouter, UploadFile, File, HTTPException

import shutil
import os
import uuid
import cv2
import time

from backend.ai.vehicle_detector import vehicle_detector
from backend.ai.plate_detector import plate_detector
from backend.database.connection import SessionLocal
from backend.models.detection import Detection
from backend.utils.responses import success_response


router = APIRouter(
    prefix="/anpr",
    tags=["ANPR"]
)


# ============================================================
# FOLDERS
# ============================================================

UPLOAD_FOLDER = "backend/uploads"
OUTPUT_FOLDER = "backend/outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ============================================================
# ALLOWED IMAGE TYPES
# ============================================================

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


# ============================================================
# ANPR ENDPOINT
# ============================================================

@router.post("/detect")
async def detect_anpr(
    file: UploadFile = File(...)
):
    """
    Complete ANPR pipeline:

    Image
        ↓
    Vehicle Detection
        ↓
    Plate Detection
        ↓
    PaddleOCR
        ↓
    SQLite Database
    """

    # ========================================================
    # TOTAL TIMER START
    # ========================================================

    total_start = time.perf_counter()

    db = SessionLocal()

    try:

        # ========================================================
        # 1. VALIDATE FILE
        # ========================================================

        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No file selected."
            )

        extension = os.path.splitext(
            file.filename
        )[1].lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Only JPG, JPEG, PNG and WEBP "
                    "images are supported."
                )
            )

        # ========================================================
        # 2. SAVE UPLOADED IMAGE
        # ========================================================

        upload_start = time.perf_counter()

        unique_filename = (
            f"anpr_{uuid.uuid4().hex}"
            f"{extension}"
        )

        image_path = os.path.join(
            UPLOAD_FOLDER,
            unique_filename
        )

        with open(
            image_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        upload_time = time.perf_counter() - upload_start

        print("=" * 60)
        print("[ANPR] Image uploaded successfully")
        print("[ANPR] Image:", image_path)
        print(
            f"[ANPR] Upload time: {upload_time:.2f} seconds"
        )
        print("=" * 60)

        # ========================================================
        # 3. VEHICLE DETECTION
        # ========================================================

        try:

            vehicle_start = time.perf_counter()

            print("[ANPR] Starting vehicle detection...")

            vehicle_result = vehicle_detector.detect(
                image_path
            )

            vehicle_time = (
                time.perf_counter()
                - vehicle_start
            )

            print(
                "[ANPR] Vehicles detected:",
                vehicle_result.get(
                    "total_vehicles",
                    0
                )
            )

            print(
                f"[ANPR] Vehicle detection time: "
                f"{vehicle_time:.2f} seconds"
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Vehicle detection failed: "
                    f"{str(e)}"
                )
            )

        # ========================================================
        # 4. LOAD ORIGINAL IMAGE
        # ========================================================

        image_load_start = time.perf_counter()

        image = cv2.imread(
            image_path
        )

        image_load_time = (
            time.perf_counter()
            - image_load_start
        )

        if image is None:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Uploaded image could not be loaded."
                )
            )

        print(
            f"[ANPR] Image loading time: "
            f"{image_load_time:.2f} seconds"
        )

        # ========================================================
        # 5. PLATE DETECTION + OCR
        # ========================================================

        try:

            plate_start = time.perf_counter()

            print(
                "[ANPR] Starting plate detection + OCR..."
            )

            plate_results = plate_detector.detect(
                image
            )

            plate_time = (
                time.perf_counter()
                - plate_start
            )

            print(
                "[ANPR] Plates detected:",
                len(plate_results)
            )

            print(
                f"[ANPR] Plate detection + OCR time: "
                f"{plate_time:.2f} seconds"
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Plate detection/OCR failed: "
                    f"{str(e)}"
                )
            )

        # ========================================================
        # 6. SAVE VEHICLE RESULTS
        # ========================================================

        vehicle_db_start = time.perf_counter()

        vehicle_saved_ids = []

        for vehicle in vehicle_result.get(
            "detections",
            []
        ):

            row = Detection(

                detection_type="vehicle",

                vehicle_type=vehicle.get(
                    "vehicle_type"
                ),

                vehicle_confidence=vehicle.get(
                    "confidence"
                ),

                image_path=vehicle_result.get(
                    "output_image"
                )
            )

            db.add(row)
            db.commit()
            db.refresh(row)

            vehicle_saved_ids.append(
                row.id
            )

        vehicle_db_time = (
            time.perf_counter()
            - vehicle_db_start
        )

        print(
            f"[ANPR] Vehicle database save time: "
            f"{vehicle_db_time:.2f} seconds"
        )

        # ========================================================
        # 7. SAVE PLATE RESULTS
        # ========================================================

        plate_db_start = time.perf_counter()

        plate_saved_ids = []

        final_plates = []

        for plate in plate_results:

            # ----------------------------------------------------
            # Plate number
            # ----------------------------------------------------

            plate_number = plate.get(
                "plate_number",
                "Not Recognized"
            )

            # ----------------------------------------------------
            # OCR confidence
            # ----------------------------------------------------

            ocr_confidence = float(
                plate.get(
                    "ocr_confidence",
                    0.0
                )
            )

            # ----------------------------------------------------
            # Plate detection confidence
            # ----------------------------------------------------

            detection_confidence = float(
                plate.get(
                    "confidence",
                    0.0
                )
            )

            # ----------------------------------------------------
            # Plate crop path
            # ----------------------------------------------------

            plate_image_path = plate.get(
                "image_path"
            )

            # ----------------------------------------------------
            # Save database row
            #
            # IMPORTANT:
            # Detection model does NOT have ocr_confidence
            # column.
            #
            # So OCR confidence is NOT inserted into Detection.
            # ----------------------------------------------------

            row = Detection(

                detection_type="plate",

                plate_number=plate_number,

                plate_confidence=detection_confidence,

                plate_image_path=plate_image_path,

                image_path=plate.get(
                    "image_url"
                )
            )

            db.add(row)
            db.commit()
            db.refresh(row)

            plate_saved_ids.append(
                row.id
            )

            # ----------------------------------------------------
            # API response
            #
            # OCR confidence can still be returned to frontend.
            # ----------------------------------------------------

            final_plates.append({

                "id": row.id,

                "plate_number": plate_number,

                "plate_confidence": round(
                    detection_confidence,
                    4
                ),

                "ocr_confidence": round(
                    ocr_confidence,
                    4
                ),

                "ocr_status": (
                    "Successful"
                    if (
                        plate_number
                        and plate_number != "Not Recognized"
                    )
                    else "Not Recognized"
                ),

                "bbox": plate.get(
                    "bbox"
                ),

                "image_url": plate.get(
                    "image_url"
                ),

                "plate_image_path": plate_image_path
            })

        plate_db_time = (
            time.perf_counter()
            - plate_db_start
        )

        print(
            f"[ANPR] Plate database save time: "
            f"{plate_db_time:.2f} seconds"
        )

        # ========================================================
        # 8. COMMIT DATABASE
        # ========================================================

        database_commit_start = time.perf_counter()

        db.commit()

        database_commit_time = (
            time.perf_counter()
            - database_commit_start
        )

        print(
            f"[ANPR] Final database commit time: "
            f"{database_commit_time:.2f} seconds"
        )

        # ========================================================
        # 9. FINAL MESSAGE
        # ========================================================

        total_vehicles = vehicle_result.get(
            "total_vehicles",
            0
        )

        total_plates = len(
            final_plates
        )

        if (
            total_vehicles > 0
            or total_plates > 0
        ):

            message = (
                "ANPR completed successfully."
            )

        else:

            message = (
                "No vehicles or number plates detected."
            )

        # ========================================================
        # 10. FINAL TIMING
        # ========================================================

        total_time = (
            time.perf_counter()
            - total_start
        )

        print("=" * 60)
        print("[ANPR] PROCESS COMPLETED")
        print("[ANPR] Vehicles:", total_vehicles)
        print("[ANPR] Plates:", total_plates)

        print("-" * 60)
        print(
            f"[ANPR] Upload time: "
            f"{upload_time:.2f} seconds"
        )
        print(
            f"[ANPR] Vehicle detection time: "
            f"{vehicle_time:.2f} seconds"
        )
        print(
            f"[ANPR] Image loading time: "
            f"{image_load_time:.2f} seconds"
        )
        print(
            f"[ANPR] Plate detection + OCR time: "
            f"{plate_time:.2f} seconds"
        )
        print(
            f"[ANPR] Vehicle DB save time: "
            f"{vehicle_db_time:.2f} seconds"
        )
        print(
            f"[ANPR] Plate DB save time: "
            f"{plate_db_time:.2f} seconds"
        )
        print(
            f"[ANPR] Final DB commit time: "
            f"{database_commit_time:.2f} seconds"
        )
        print("-" * 60)
        print(
            f"[ANPR] TOTAL PROCESS TIME: "
            f"{total_time:.2f} seconds"
        )
        print("=" * 60)

        # ========================================================
        # 11. FINAL RESPONSE
        # ========================================================

        return success_response(

            message=message,

            data={

                # ------------------------------------------------
                # VEHICLE RESULT
                # ------------------------------------------------

                "vehicle_detection": {

                    "total_vehicles":
                        total_vehicles,

                    "class_counts":
                        vehicle_result.get(
                            "class_counts",
                            {}
                        ),

                    "detections":
                        vehicle_result.get(
                            "detections",
                            []
                        ),

                    "output_image":
                        vehicle_result.get(
                            "output_image"
                        ),

                    "saved_ids":
                        vehicle_saved_ids
                },

                # ------------------------------------------------
                # PLATE RESULT
                # ------------------------------------------------

                "plate_detection": {

                    "total_plates":
                        total_plates,

                    "plates":
                        final_plates,

                    "saved_ids":
                        plate_saved_ids
                }

            }
        )

    # ============================================================
    # HTTP ERROR
    # ============================================================

    except HTTPException:

        db.rollback()

        raise

    # ============================================================
    # OTHER ERROR
    # ============================================================

    except Exception as e:

        db.rollback()

        print(
            "[ANPR] UNEXPECTED ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to process ANPR image: "
                f"{str(e)}"
            )
        )

    # ============================================================
    # CLOSE DATABASE
    # ============================================================

    finally:

        db.close()