#automated test

import pytest
import io
import zipfile
import geopandas as gpd
from shapely.geometry import Polygon

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import files as files_route
from app.main import app
from app.models.database import Base, get_db
from app.models.file import File
from app.models.feature import Feature



@pytest.fixture
def client(tmp_path):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    Base.metadata.create_all(bind=test_engine)

    test_upload_dir = tmp_path / "uploads"
    test_upload_dir.mkdir()

    original_upload_dir = files_route.UPLOAD_DIR
    files_route.UPLOAD_DIR = test_upload_dir

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        files_route.UPLOAD_DIR = original_upload_dir
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()



def test_get_nonexistent_file_returns_404(client):
    response = client.get("/api/files/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}


def test_upload_valid_kml(client):
    kml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
      <Document>
        <Placemark>
          <name>Test Point</name>
          <Point>
            <coordinates>13.405,52.520,0</coordinates>
          </Point>
        </Placemark>
      </Document>
    </kml>
    """

    response = client.post(
        "/api/files/",
        files={
            "file": (
                "test.kml",
                kml_content,
                "application/vnd.google-earth.kml+xml"
            )
        }
    )

    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == "test.kml"
    assert "id" in data


def test_upload_unsupported_file_type_returns_400(client):
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "document.pdf",
                b"This is a test PDF",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Only .kml files and .zip Shapefiles are supported"
    }

def test_upload_invalid_zip_returns_400(client):
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr(
            "hello.txt",
            "This is not a Shapefile."
        )

    response = client.post(
        "/api/files/",
        files={
            "file": (
                "invalid.zip",
                zip_buffer.getvalue(),
                "application/zip"
            )
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "ZIP file does not contain a complete Shapefile"
    }


def test_get_measurements_for_uploaded_kml(client):
    kml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
      <Document>
        <Placemark>
          <name>Test Point</name>
          <Point>
            <coordinates>13.405,52.520,0</coordinates>
          </Point>
        </Placemark>
      </Document>
    </kml>
    """

    upload_response = client.post(
        "/api/files/",
        files={
            "file": (
                "measurements_test.kml",
                kml_content,
                "application/vnd.google-earth.kml+xml"
            )
        }
    )

    assert upload_response.status_code == 200

    file_id = upload_response.json()["id"]

    response = client.get(
        f"/api/files/{file_id}/measurements/"
    )

    assert response.status_code == 200

    measurements = response.json()

    assert len(measurements) == 1
    assert measurements[0]["feature_index"] == 0
    assert measurements[0]["geometry_type"] == "Point"
    assert measurements[0]["area"] is None
    assert measurements[0]["length"] is None



def test_polygon_area_is_calculated(client, tmp_path):
    import zipfile

    polygon = Polygon([
        (13.4050, 52.5200),
        (13.4060, 52.5200),
        (13.4060, 52.5210),
        (13.4050, 52.5210),
        (13.4050, 52.5200)
    ])

    gdf = gpd.GeoDataFrame(
        {"name": ["Test Polygon"]},
        geometry=[polygon],
        crs="EPSG:4326"
    )

    shapefile_dir = tmp_path / "shapefile"
    shapefile_dir.mkdir()

    shapefile_path = shapefile_dir / "test_polygon.shp"
    gdf.to_file(shapefile_path)

    zip_path = tmp_path / "test_polygon.zip"

    with zipfile.ZipFile(zip_path, "w") as zip_file:
        for path in shapefile_dir.iterdir():
            zip_file.write(path, arcname=path.name)

    response = client.post(
        "/api/files/",
        files={
            "file": (
                "test_polygon.zip",
                zip_path.read_bytes(),
                "application/zip"
            )
        }
    )

    assert response.status_code == 200

    file_id = response.json()["id"]

    file_response = client.get(f"/api/files/{file_id}")
    assert file_response.status_code == 200
    assert file_response.json()["crs"] == "EPSG:4326"

    measurement_response = client.get(
        f"/api/files/{file_id}/measurements/"
    )

    assert measurement_response.status_code == 200

    measurements = measurement_response.json()

    assert len(measurements) == 1
    assert measurements[0]["geometry_type"] == "Polygon"
    assert measurements[0]["area"] is not None
    assert measurements[0]["area"] > 0
    assert measurements[0]["length"] is None



def test_linestring_length_is_calculated(client, tmp_path):
    from shapely.geometry import LineString

    line = LineString([
        (13.4050, 52.5200),
        (13.4060, 52.5210)
    ])

    gdf = gpd.GeoDataFrame(
        {"name": ["Test Line"]},
        geometry=[line],
        crs="EPSG:4326"
    )

    shapefile_dir = tmp_path / "line_shapefile"
    shapefile_dir.mkdir()

    shapefile_path = shapefile_dir / "test_line.shp"
    gdf.to_file(shapefile_path)

    zip_path = tmp_path / "test_line.zip"

    with zipfile.ZipFile(zip_path, "w") as zip_file:
        for path in shapefile_dir.iterdir():
            zip_file.write(path, arcname=path.name)

    response = client.post(
        "/api/files/",
        files={
            "file": (
                "test_line.zip",
                zip_path.read_bytes(),
                "application/zip"
            )
        }
    )

    assert response.status_code == 200

    file_id = response.json()["id"]

    measurement_response = client.get(
        f"/api/files/{file_id}/measurements/"
    )

    assert measurement_response.status_code == 200

    measurements = measurement_response.json()

    assert len(measurements) == 1
    assert measurements[0]["geometry_type"] == "LineString"
    assert measurements[0]["length"] is not None
    assert measurements[0]["length"] > 0
    assert measurements[0]["area"] is None




