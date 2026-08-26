from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from backend.database.dependencies import get_db
from backend.models.detection import Detection
from backend.utils.responses import success_response

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/summary")
def analytics_summary(db: Session = Depends(get_db)):

    total_detections = db.query(func.count(Detection.id)).scalar() or 0

    total_vehicles = db.query(func.count(Detection.id)).filter(
        Detection.detection_type == "vehicle"
    ).scalar() or 0

    total_plates = db.query(func.count(Detection.id)).filter(
        Detection.detection_type == "plate"
    ).scalar() or 0

    ocr_success = db.query(func.count(Detection.id)).filter(
        Detection.detection_type == "plate",
        Detection.plate_number.isnot(None),
        Detection.plate_number != "Not Recognized"
    ).scalar() or 0

    ocr_failure = total_plates - ocr_success

    unique_plates = db.query(
        func.count(func.distinct(Detection.plate_number))
    ).filter(
        Detection.detection_type == "plate",
        Detection.plate_number.isnot(None),
        Detection.plate_number != "",
        Detection.plate_number != "Not Recognized"
    ).scalar() or 0

    today = datetime.utcnow().date()

    today_detections = db.query(func.count(Detection.id)).filter(
        func.date(Detection.created_at) == today
    ).scalar() or 0

    average_confidence = db.query(
        func.avg(Detection.plate_confidence)
    ).filter(Detection.detection_type == "plate").scalar()

    latest = db.query(Detection).filter(
        Detection.detection_type == "plate"
    ).order_by(Detection.id.desc()).first()

    return success_response(
        message="Analytics summary fetched successfully.",
        data={
            "total_detections": total_detections,
            "total_vehicles": total_vehicles,
            "total_plates": total_plates,
            "ocr_success": ocr_success,
            "ocr_failure": ocr_failure,
            "unique_plates": unique_plates,
            "today_detections": today_detections,
            "average_confidence": round(float(average_confidence or 0), 2),
            "latest_plate": latest.plate_number if latest else None
        }
    )


@router.get("/vehicles")
def analytics_vehicles(db: Session = Depends(get_db)):

    rows = db.query(
        Detection.vehicle_type, func.count(Detection.id)
    ).filter(
        Detection.detection_type == "vehicle"
    ).group_by(Detection.vehicle_type).all()

    distribution = {vt or "unknown": count for vt, count in rows}

    return success_response(
        message="Vehicle type distribution fetched successfully.",
        data={"distribution": distribution}
    )


@router.get("/plates")
def analytics_plates(db: Session = Depends(get_db)):

    total_plates = db.query(func.count(Detection.id)).filter(
        Detection.detection_type == "plate"
    ).scalar() or 0

    ocr_success = db.query(func.count(Detection.id)).filter(
        Detection.detection_type == "plate",
        Detection.plate_number.isnot(None),
        Detection.plate_number != "Not Recognized"
    ).scalar() or 0

    ocr_failure = total_plates - ocr_success

    return success_response(
        message="Plate analytics fetched successfully.",
        data={
            "total_plates": total_plates,
            "ocr_success": ocr_success,
            "ocr_failure": ocr_failure
        }
    )


@router.get("/timeline")
def analytics_timeline(db: Session = Depends(get_db)):
    """Detection counts per day for the last 14 days (for a trend chart)."""

    rows = db.query(
        func.date(Detection.created_at), func.count(Detection.id)
    ).group_by(
        func.date(Detection.created_at)
    ).order_by(
        func.date(Detection.created_at).desc()
    ).limit(14).all()

    timeline = [{"date": str(d), "count": c} for d, c in rows][::-1]

    return success_response(
        message="Detection timeline fetched successfully.",
        data={"timeline": timeline}
    )
