from fastapi import APIRouter
from sqlalchemy import func
from datetime import datetime

from backend.database.connection import SessionLocal
from backend.models.detection import Detection
from backend.utils.responses import success_response

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/stats")
def dashboard_stats():

    db = SessionLocal()

    try:
        total_detections = db.query(Detection).count()

        total_vehicles = db.query(Detection).filter(
            Detection.detection_type == "vehicle"
        ).count()

        total_plates = db.query(Detection).filter(
            Detection.detection_type == "plate"
        ).count()

        ocr_success = db.query(Detection).filter(
            Detection.detection_type == "plate",
            Detection.plate_number.isnot(None),
            Detection.plate_number != "Not Recognized"
        ).count()

        today = datetime.utcnow().date()

        today_detections = db.query(Detection).filter(
            func.date(Detection.created_at) == today
        ).count()

        latest = db.query(Detection).filter(
            Detection.detection_type == "plate"
        ).order_by(Detection.id.desc()).first()

        return success_response(
            message="Dashboard stats fetched successfully.",
            data={
                "total_detections": total_detections,
                "total_vehicles": total_vehicles,
                "total_plates": total_plates,
                "ocr_success": ocr_success,
                "today_detections": today_detections,
                "latest_plate": latest.plate_number if latest else None
            }
        )

    finally:
        db.close()
