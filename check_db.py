from app.models.database import SessionLocal
from app.models.file import File
from app.models.feature import Feature

db = SessionLocal()

files = db.query(File).all()
features = db.query(Feature).all()

print("FILES:")
for file in files:
    print(
        file.id,
        file.filename,
        file.file_type,
        file.crs,
        file.feature_count,
        file.status
    )

print("\nFEATURES:")
for feature in features:
    print(
        feature.id,
        feature.file_id,
        feature.feature_index,
        feature.geometry_type,
        feature.area,
        feature.length,
        feature.properties
    )

db.close()