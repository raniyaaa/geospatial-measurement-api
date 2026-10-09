# means one row = one uploaded geospatial file.
#file.py
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String
from app.models.database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    crs = Column(String, nullable=True)
    feature_count = Column(Integer, nullable=True)
    status = Column(String, nullable=False)
    error_message = Column(String, nullable=True)
    created_at = Column(
    DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc)
    )


