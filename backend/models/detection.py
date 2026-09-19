from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from backend.database.base import Base


class Detection(Base):

    __tablename__ = "detections"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # vehicle / plate
    detection_type = Column(
        String(20),
        nullable=False,
        default="vehicle"
    )

    # Vehicle
    vehicle_type = Column(
        String(50),
        nullable=True
    )

    vehicle_confidence = Column(
        Float,
        nullable=True
    )

    # Plate
    plate_number = Column(
        String(50),
        nullable=True
    )

    plate_confidence = Column(
        Float,
        nullable=True
    )

    plate_image_path = Column(
        String(255),
        nullable=True
    )

    # Shared image
    image_path = Column(
        String(255),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )