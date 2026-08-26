from fastapi import APIRouter, Query, HTTPException
from backend.database.connection import SessionLocal
from backend.models.detection import Detection
from backend.utils.responses import success_response

router = APIRouter(
    prefix="/history",
    tags=["Detection History"]
)


def _serialize(row: Detection):
    return {
        "id": row.id,
        "detection_type": row.detection_type,
        "vehicle_type": row.vehicle_type,
        "vehicle_confidence": row.vehicle_confidence,
        "plate_number": row.plate_number,
        "plate_confidence": row.plate_confidence,
        "image_path": row.image_path,
        "plate_image_path": row.plate_image_path,
        "created_at": str(row.created_at)
    }


@router.get("/")
def get_history(
    detection_type: str | None = Query(None, description="Filter: 'vehicle' or 'plate'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):

    db = SessionLocal()

    try:
        query = db.query(Detection)

        if detection_type:
            query = query.filter(Detection.detection_type == detection_type)

        total_records = query.count()

        records = (
            query.order_by(Detection.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return success_response(
            message="History fetched successfully.",
            data={
                "total_records": total_records,
                "page": page,
                "page_size": page_size,
                "history": [_serialize(r) for r in records]
            }
        )

    finally:
        db.close()


@router.get("/search")
def search_plate(plate: str = Query(...)):

    db = SessionLocal()

    try:
        records = db.query(Detection).filter(
            Detection.detection_type == "plate",
            Detection.plate_number.contains(plate.upper())
        ).order_by(Detection.id.desc()).all()

        return success_response(
            message="Search completed.",
            data={
                "total_records": len(records),
                "history": [_serialize(r) for r in records]
            }
        )

    finally:
        db.close()


@router.delete("/{id}")
def delete_history(id: int):

    db = SessionLocal()

    try:
        record = db.query(Detection).filter(Detection.id == id).first()

        if record is None:
            raise HTTPException(status_code=404, detail="Record not found")

        db.delete(record)
        db.commit()

        return success_response(message="Record deleted successfully.")

    finally:
        db.close()
