from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from backend.database.base import Base


class Detection(Base):
    """
    Unified table for BOTH vehicle detections and plate detections.
    `detection_type` tells you which kind of row it is: "vehicle" or "plate".

    This one-table design keeps History/Analytics simple (one query
    covers everything) while still letting each row carry only the
    fields that are relevant to it — the rest stay NULL.
    """

    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)

    # "vehicle" or "plate" — tells you which columns below are meaningful
    detection_type = Column(String(20), nullable=False, default="vehicle")

    # ---- Vehicle fields ----
    vehicle_type = Column(String(50), nullable=True)          # car / motorcycle / truck / bus
    vehicle_confidence = Column(Float, nullable=True)

    # ---- Plate fields ----
    plate_number = Column(String(50), nullable=True)          # "Not Recognized" if OCR failed
    plate_confidence = Column(Float, nullable=True)
    plate_image_path = Column(String(255), nullable=True)     # cropped plate image (URL)

    # ---- Shared ----
    image_path = Column(String(255), nullable=True)           # annotated / original image (URL)

    created_at = Column(DateTime, default=datetime.utcnow)
