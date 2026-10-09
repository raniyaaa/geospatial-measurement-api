
from pathlib import Path
import json
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.utils.file_validation import validate_shapefile_zip
from app.schemas.file import FileResponse, MeasurementResponse
from app.models.database import get_db
from app.models.file import File as FileModel
from app.models.feature import Feature
from app.services.file_processor import (
    read_geospatial_file,
    process_features,
    clean_properties
)

router = APIRouter(
    prefix="/api/files",
    tags=["Files"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )

    original_filename = Path(file.filename).name
    extension = Path(original_filename).suffix.lower()

    if extension not in {".kml", ".zip"}:
        raise HTTPException(
            status_code=400,
            detail="Only .kml files and .zip Shapefiles are supported"
        )

    stored_filename = f"{uuid.uuid4()}_{original_filename}"
    file_path = UPLOAD_DIR / stored_filename

    try:
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)

        if extension == ".zip":
            try:
                validate_shapefile_zip(str(file_path))
            except ValueError as e:
                file_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail=str(e)
                )

        db_file = FileModel(
            filename=original_filename,
            file_type=extension[1:].upper(),
            status="uploaded"
        )

        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        try:
            gdf = read_geospatial_file(str(file_path))
            features = process_features(gdf)

            db_file.crs = str(gdf.crs)
            db_file.feature_count = len(features)
            db_file.status = "processed"

            for feature_data in features:
                db_feature = Feature(
                    file_id=db_file.id,
                    feature_index=feature_data["feature_index"],
                    geometry_type=feature_data["geometry_type"],
                    properties=json.dumps(
                        clean_properties(feature_data["properties"]),
                        default=str,
                        allow_nan=False
                    ),
                    area=feature_data["area"],
                    length=feature_data["length"]
                )

                db.add(db_feature)

            db.commit()

        except Exception as e:
            db.rollback()

            db_file.status = "failed"
            db_file.error_message = str(e)

            db.commit()

            file_path.unlink(missing_ok=True)

            raise HTTPException(
                status_code=400,
                detail=f"File processing failed: {e}"
            )

        return {
            "id": db_file.id,
            "filename": original_filename,
            "content_type": file.content_type,
            "saved_to": str(file_path)
        }

    except HTTPException:
        raise

    except Exception:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while uploading the file"
        )


@router.get("/{file_id}", response_model=FileResponse)
def get_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    db_file = db.query(FileModel).filter(
        FileModel.id == file_id
    ).first()

    if not db_file:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    return db_file


@router.get(
    "/{file_id}/measurements/",
    response_model=list[MeasurementResponse]
)
def get_measurements(
    file_id: int,
    db: Session = Depends(get_db)
):
    db_file = db.query(FileModel).filter(
        FileModel.id == file_id
    ).first()

    if not db_file:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    features = db.query(Feature).filter(
        Feature.file_id == file_id
    ).all()

    return features
