from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import uuid

from backend.ai.vehicle_detector import vehicle_detector
from backend.database.connection import SessionLocal
from backend.models.detection import Detection
from backend.utils.responses import success_response

router = APIRouter(
    prefix="/vehicle",
    tags=["Vehicle Detection"]
)

UPLOAD_FOLDER = "backend/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@router.post("/detect")
async def detect_vehicle(file: UploadFile = File(...)):
    """
    Uses proper HTTP status codes (400 for bad input, 500 for server
    errors) — main.py has a global exception handler that wraps every
    error into the same {success:false, message:...} JSON shape, so
    the frontend never has to guess the response format.
    """

    db = SessionLocal()

    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected.")

        extension = os.path.splitext(file.filename)[1].lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Only JPG, JPEG, PNG and WEBP images are supported."
            )

        unique_filename = f"{uuid.uuid4().hex}{extension}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            result = vehicle_detector.detect(file_path)
        except Exception as model_error:
            raise HTTPException(
                status_code=500,
                detail=f"Vehicle detection model error: {model_error}"
            )

        saved_ids = []

        for det in result["detections"]:
            row = Detection(
                detection_type="vehicle",
                vehicle_type=det["vehicle_type"],
                vehicle_confidence=det["confidence"],
                image_path=result["output_image"]
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            saved_ids.append(row.id)

        return success_response(
            message=(
                "Vehicle detection completed successfully."
                if result["total_vehicles"] > 0
                else "No vehicles detected in this image."
            ),
            data={
                "total_vehicles": result["total_vehicles"],
                "class_counts": result["class_counts"],
                "detections": result["detections"],
                "output_image": result["output_image"],
                "saved_ids": saved_ids
            }
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unable to process image: {e}")

    finally:
        db.close()
