from backend.database.connection import engine
from backend.database.base import Base

from backend.models.user import User
from backend.models.detection import Detection


def init_database():
    Base.metadata.create_all(bind=engine)