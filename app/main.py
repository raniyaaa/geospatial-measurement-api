from fastapi import FastAPI

from app.models.database import Base, engine
from app.models.file import File
from app.models.feature import Feature
from app.api.routes.files import router as file_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Geospatial Measurement API")

app.include_router(file_router)


@app.get("/")
def root():
    return {"message": "Geospatial Measurement API is running"}