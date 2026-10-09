from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from app.models.database import Base


class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)

    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)

    feature_index = Column(Integer, nullable=False)

    geometry_type = Column(String, nullable=False)

    properties = Column(Text, nullable=True)

    area = Column(Float, nullable=True) #nullable cuz they aren't applicable to every geometry. ie, for polygon - length is null, for line string -area is null, for point - both are null

    length = Column(Float, nullable=True)

#dont need to create crs for every feature, cuz it belongs to one geospatial file,so let it stay in files table.