from fastapi import APIRouter, UploadFile, File, HTTPException

import os
import shutil
import cv2
import uuid

from backend.ai.plate_detector import plate_detector
from backend.ai.ocr_engine import ocr_engine
from backend.database.connection import SessionLocal
from backend.models.detection import Detection
from backend.utils.responses import success_response


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/plate",
    tags=["Plate Detection"]
)


# ============================================================
# FOLDERS
# ============================================================

UPLOAD_FOLDER = "backend/uploads"
OUTPUT_FOLDER = "backend/outputs"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)


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
# DETECTION SETTINGS
# ============================================================

# Very weak YOLO detections are usually false detections.
# Only detections above this confidence will go to OCR.
MIN_PLATE_CONFIDENCE = 0.40

# Maximum number of plate detections to process.
MAX_PLATES_TO_PROCESS = 3


# ============================================================
# PLATE DETECTION API
# ============================================================

@router.post("/detect")
async def detect_plate(
    file: UploadFile = File(...)
):

    db = SessionLocal()

    try:

        # ====================================================
        # 1. CHECK FILE
        # ====================================================

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


        # ====================================================
        # 2. SAVE UPLOADED IMAGE
        # ====================================================

        unique_filename = (
            f"{uuid.uuid4().hex}{extension}"
        )


        file_path = os.path.join(
            UPLOAD_FOLDER,
            unique_filename
        )


        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )


        print(
            "======================================"
        )

        print(
            "[plate route] Image saved:"
        )

        print(
            file_path
        )

        print(
            "======================================"
        )


        # ====================================================
        # 3. READ IMAGE
        # ====================================================

        image = cv2.imread(
            file_path
        )


        if image is None:

            raise HTTPException(
                status_code=400,
                detail="Unable to read uploaded image."
            )


        print(
            f"[plate route] Image size: "
            f"{image.shape[1]} x {image.shape[0]}"
        )


        # ====================================================
        # 4. YOLO PLATE DETECTION
        # ====================================================

        try:

            detections = plate_detector.detect(
                image
            )

        except Exception as model_error:

            print(
                "[plate route] PLATE MODEL ERROR:",
                model_error
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Plate detection model error: "
                    f"{model_error}"
                )
            )


        print(
            "======================================"
        )

        print(
            f"[plate route] Total YOLO detections: "
            f"{len(detections)}"
        )

        print(
            "======================================"
        )


        # ====================================================
        # 5. NO PLATE FOUND
        # ====================================================

        if not detections:

            return success_response(

                message="No number plate detected.",

                data={
                    "total_plates": 0,
                    "plates": []
                }
            )


        # ====================================================
        # 6. FILTER WEAK DETECTIONS
        # ====================================================

        strong_detections = []


        for plate in detections:

            confidence = float(
                plate.get(
                    "confidence",
                    0.0
                )
            )


            print(
                f"[plate route] YOLO detection "
                f"confidence = {confidence:.4f}"
            )


            # -----------------------------------------------
            # Ignore weak detection
            # -----------------------------------------------

            if confidence < MIN_PLATE_CONFIDENCE:

                print(
                    f"[plate route] SKIPPED weak "
                    f"detection: {confidence:.4f}"
                )

                continue


            strong_detections.append(
                plate
            )


        # ====================================================
        # 7. SORT BY CONFIDENCE
        # ====================================================

        strong_detections.sort(
            key=lambda x: float(
                x.get(
                    "confidence",
                    0.0
                )
            ),
            reverse=True
        )


        # ====================================================
        # 8. LIMIT NUMBER OF PLATES
        # ====================================================

        strong_detections = (
            strong_detections[
                :MAX_PLATES_TO_PROCESS
            ]
        )


        print(
            "======================================"
        )

        print(
            f"[plate route] Strong detections: "
            f"{len(strong_detections)}"
        )

        print(
            "======================================"
        )


        # ====================================================
        # 9. IF ALL DETECTIONS WERE WEAK
        # ====================================================

        if not strong_detections:

            return success_response(

                message=(
                    "Number plate was not detected "
                    "with sufficient confidence."
                ),

                data={
                    "total_plates": 0,
                    "plates": []
                }
            )


        # ====================================================
        # 10. PROCESS EACH STRONG PLATE
        # ====================================================

        final_results = []


        for index, plate in enumerate(
            strong_detections
        ):

            print(
                "--------------------------------------"
            )

            print(
                f"[plate route] Processing plate "
                f"{index + 1}"
            )


            # =================================================
            # GET YOLO CONFIDENCE
            # =================================================

            plate_confidence = float(
                plate.get(
                    "confidence",
                    0.0
                )
            )


            print(
                f"[plate route] YOLO confidence: "
                f"{plate_confidence:.4f}"
            )


            # =================================================
            # GET CROPPED PLATE IMAGE PATH
            # =================================================

            plate_image_path = plate.get(
                "image_path"
            )


            if not plate_image_path:

                print(
                    "[plate route] No image_path "
                    "returned by plate detector."
                )

                continue


            # =================================================
            # CHECK CROP EXISTS
            # =================================================

            if not os.path.exists(
                plate_image_path
            ):

                print(
                    "[plate route] Crop does not exist:"
                )

                print(
                    plate_image_path
                )

                continue


            # =================================================
            # READ PLATE CROP
            # =================================================

            plate_image = cv2.imread(
                plate_image_path
            )


            if plate_image is None:

                print(
                    "[plate route] Unable to read "
                    "plate crop:"
                )

                print(
                    plate_image_path
                )

                continue


            print(
                f"[plate route] Plate crop size: "
                f"{plate_image.shape[1]} x "
                f"{plate_image.shape[0]}"
            )


            # =================================================
            # OCR
            # =================================================

            try:

                print(
                    "[plate route] Starting OCR..."
                )


                ocr_result = (
                    ocr_engine.read_plate(
                        plate_image
                    )
                )


            except Exception as ocr_error:

                print(
                    "[plate route] OCR ERROR:",
                    ocr_error
                )


                ocr_result = {

                    "plate_number":
                        "Not Recognized",

                    "confidence":
                        0.0,

                    "raw":
                        []
                }


            # =================================================
            # GET OCR RESULT
            # =================================================

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


            # =================================================
            # CLEAN OCR RESULT
            # =================================================

            if not plate_number:

                plate_number = (
                    "Not Recognized"
                )


            plate_number = str(
                plate_number
            ).strip()


            if plate_number == "":

                plate_number = (
                    "Not Recognized"
                )


            # =================================================
            # OCR STATUS
            # =================================================

            if (
                plate_number
                == "Not Recognized"
            ):

                ocr_status = "Failed"

            else:

                ocr_status = "Successful"


            # =================================================
            # PRINT OCR RESULT
            # =================================================

            print(
                f"[plate route] OCR result: "
                f"{plate_number}"
            )

            print(
                f"[plate route] OCR confidence: "
                f"{ocr_confidence:.4f}"
            )

            print(
                f"[plate route] OCR status: "
                f"{ocr_status}"
            )


            # =================================================
            # IMAGE URL
            # =================================================

            image_url = plate.get(
                "image_url",
                ""
            )


            # =================================================
            # CLASS NAME
            # =================================================

            class_name = plate.get(
                "class_name",
                "License Plate"
            )


            # =================================================
            # SAVE TO DATABASE
            # =================================================

            try:

                detection = Detection(

                    detection_type="plate",

                    plate_number=plate_number,

                    plate_confidence=(
                        plate_confidence
                    ),

                    plate_image_path=(
                        image_url
                    ),

                    image_path=(
                        image_url
                    )
                )


                db.add(
                    detection
                )

                db.commit()

                db.refresh(
                    detection
                )


            except Exception as db_error:

                db.rollback()

                print(
                    "[plate route] DATABASE ERROR:",
                    db_error
                )

                continue


            # =================================================
            # FINAL RESULT
            # =================================================

            final_results.append({

                "id":
                    detection.id,

                "bbox":
                    plate.get(
                        "bbox",
                        []
                    ),

                "confidence":
                    plate_confidence,

                "class_name":
                    class_name,

                "image_url":
                    image_url,

                "plate_number":
                    plate_number,

                "ocr":
                    plate_number,

                "ocr_status":
                    ocr_status,

                "ocr_confidence":
                    ocr_confidence,

                "created_at":
                    str(
                        detection.created_at
                    )
            })


            print(
                f"[plate route] Plate "
                f"{index + 1} completed."
            )


        # ====================================================
        # 11. NO SUCCESSFUL PROCESSING
        # ====================================================

        if not final_results:

            return success_response(

                message=(
                    "Number plate detected, "
                    "but processing failed."
                ),

                data={
                    "total_plates": 0,
                    "plates": []
                }
            )


        # ====================================================
        # 12. FINAL SUCCESS RESPONSE
        # ====================================================

        print(
            "======================================"
        )

        print(
            f"[plate route] FINAL PLATES: "
            f"{len(final_results)}"
        )

        print(
            "======================================"
        )


        return success_response(

            message=(
                "Plate detection completed "
                "successfully."
            ),

            data={

                "total_plates":
                    len(final_results),

                "plates":
                    final_results
            }
        )


    # ========================================================
    # HTTP EXCEPTION
    # ========================================================

    except HTTPException:

        db.rollback()

        raise


    # ========================================================
    # OTHER ERRORS
    # ========================================================

    except Exception as e:

        db.rollback()

        print(
            "======================================"
        )

        print(
            "[plate route] ERROR:",
            str(e)
        )

        print(
            "======================================"
        )


        raise HTTPException(

            status_code=500,

            detail=(
                f"Unable to process image: {e}"
            )
        )


    # ========================================================
    # CLOSE DATABASE
    # ========================================================

    finally:

        db.close()