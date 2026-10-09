# Geospatial File Measurement API

A geospatial file processing application built with FastAPI and Streamlit, **dockerized using Docker Compose**. It accepts KML files and Shapefile ZIP archives, extracts their features, calculates geometric measurements, and displays the results through a web interface.

## Features

- Upload KML files and Shapefile ZIP archives.
- Validate file extensions and Shapefile ZIP contents.
- Extract geometry types and feature properties.
- Calculate Polygon area and LineString length.
- Handle Point geometries without calculating area or length.
- Transform geographic coordinates into a suitable projected coordinate reference system (CRS) before calculating measurements.
- Store file metadata and feature measurements using SQLite and SQLAlchemy.
- Retrieve file details and measurement results through API endpoints.
- View file metadata and measurement results through a Streamlit interface.
- Handle invalid uploads, processing failures, and nonexistent file IDs.
- Run automated tests using pytest.
- Run the backend and frontend in separate Docker containers using Docker Compose.
- Preserve the SQLite database and uploaded files using Docker named volumes.

## Tech Stack

- **Backend API:** FastAPI
- **Frontend:** Streamlit
- **HTTP requests:** Requests
- **Geospatial processing:** GeoPandas, Shapely, PyProj
- **Database:** SQLite, SQLAlchemy
- **Validation:** Pydantic
- **Testing:** Pytest, FastAPI TestClient, HTTPX
- **Containerization:** Docker, Docker Compose

## Project Structure

```text
geospatial-measurement-api/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── files.py
│   ├── models/
│   │   ├── database.py
│   │   ├── file.py
│   │   └── feature.py
│   ├── schemas/
│   │   └── file.py
│   ├── services/
│   │   └── file_processor.py
│   ├── utils/
│   │   └── file_validation.py
│   └── main.py
├── frontend/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── tests/
│   └── test_files.py
├── uploads/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── requirements.txt
└── README.md
```

### Application Structure

- **API routes (`app/api/routes/`):** Define the file upload, file details, and measurements endpoints.
- **Services (`app/services/`):** Handle geospatial file reading, feature extraction, CRS transformation, and measurement calculation.
- **Models (`app/models/`):** Define the database connection and SQLAlchemy models for files and features.
- **Schemas (`app/schemas/`):** Define Pydantic response schemas.
- **Utilities (`app/utils/`):** Validate uploaded Shapefile ZIP archives.
- **Frontend (`frontend/`):** Provides a Streamlit interface for uploading files and viewing metadata and measurements.
- **Tests (`tests/`):** Verify API behavior and geometry measurement calculations.
- **Docker configuration:** Defines the backend and frontend images, container networking, and persistent storage.

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/raniyaaa/geospatial-measurement-api.git
cd geospatial-measurement-api
```

### 2. Create and activate a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS or Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the backend API

Run the following command from the project root:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

`http://127.0.0.1:8000`

Interactive API documentation is available at:

`http://127.0.0.1:8000/docs`

## Running the Frontend Locally

The application includes a Streamlit interface for uploading geospatial files and viewing file details and measurement results.

Keep the FastAPI backend running in the first terminal. Open a second terminal, navigate to the project root, and activate the virtual environment if necessary.

Run:

```bash
streamlit run frontend/app.py
```

Streamlit will display a local URL, usually:

`http://localhost:8501`

Open that URL in your browser.

By default, the frontend communicates with the FastAPI backend at `http://127.0.0.1:8000`. The backend URL can be configured using the `API_BASE_URL` environment variable.

For example, in PowerShell:

```powershell
$env:API_BASE_URL = "http://127.0.0.1:8000"
streamlit run frontend/app.py
```

Ensure the backend is running before uploading files.

## Running with Docker

### Prerequisites

- Docker Desktop installed and running
- Docker Compose available through the Docker CLI

### Build the images

From the project root, run:

```bash
docker compose build
```

This builds separate Docker images for the FastAPI backend and Streamlit frontend.

### Start the application

```bash
docker compose up
```

Docker Compose starts both services and connects them through an internal Docker network.

To run the containers in the background instead, use:

```bash
docker compose up -d
```

### Access the application

- **Streamlit frontend:** http://localhost:8501
- **FastAPI Swagger documentation:** http://localhost:8000/docs

### Container networking

The frontend uses the `API_BASE_URL` environment variable to determine the backend address.

- **Local development:** `http://127.0.0.1:8000`
- **Docker Compose:** `http://backend:8000`

Inside Docker Compose, `backend` is the service name of the FastAPI container. Docker's internal network allows the frontend to communicate with the backend using this service name.

The frontend container exposes port `8501`, and the backend container exposes port `8000`. The port mappings make both services accessible from the host machine.

### Stop the application

If running in the foreground, press `Ctrl + C` in the terminal running Docker Compose.

To stop and remove the containers and Compose network, use:

```bash
docker compose down
```

### Persistent storage

Docker Compose uses named volumes to preserve the SQLite database and uploaded files:

- `db_data`: stores the SQLite database at `/app/data/geospatial.db`.
- `uploads_data`: stores uploaded geospatial files at `/app/uploads`.

Stopping or recreating the containers does not normally delete these named volumes. Avoid using `docker compose down -v` unless you intentionally want to remove the volumes and their data.

### Frontend Features

- Upload KML files and Shapefile ZIP archives.
- View file ID, filename, feature count, processing status, and source CRS.
- View geometry types and measurements in a table.
- Display Polygon area in square metres (m²) and LineString length in metres (m).
- Show error messages when uploads or API requests fail.

## API Endpoints

### 1. Upload a geospatial file

**Endpoint:** `POST /api/files/`

Accepts a `.kml` file or a `.zip` archive containing a Shapefile.

**Example request:**

```bash
curl -X POST "http://127.0.0.1:8000/api/files/" \
  -F "file=@sample.kml"
```

**Example response:**

```json
{
  "id": 1,
  "filename": "sample.kml",
  "content_type": "application/vnd.google-earth.kml+xml",
  "saved_to": "uploads/<unique_filename>"
}
```

The actual ID, content type, and stored filename depend on the uploaded file and request. The returned `saved_to` value identifies the server-side storage path; it is not a public download URL.

Use the returned ID to retrieve the file metadata and measurements.

If file validation or processing fails, the API returns an HTTP error response. Processing failures may leave a file metadata record with a `failed` status and an associated error message.

### 2. Retrieve file details

**Endpoint:** `GET /api/files/{file_id}`

**Example request:**

```bash
curl "http://127.0.0.1:8000/api/files/1"
```

**Example response:**

```json
{
  "id": 1,
  "filename": "sample.kml",
  "file_type": "KML",
  "crs": "EPSG:4326",
  "feature_count": 1,
  "status": "processed",
  "error_message": null,
  "created_at": "2026-10-08T14:02:00"
}
```

Returns file metadata, including the original filename, file type, source CRS, feature count, processing status, error message, and creation timestamp.

### 3. Retrieve measurements

**Endpoint:** `GET /api/files/{file_id}/measurements/`

**Example request:**

```bash
curl "http://127.0.0.1:8000/api/files/1/measurements/"
```

**Example response:**

```json
[
  {
    "feature_index": 0,
    "geometry_type": "Polygon",
    "area": 7549.47,
    "length": null
  }
]
```

The numerical values depend on the uploaded geometry. Point features have `null` area and length; Polygon features have an area; LineString features have a length.

The example file ID `1` is illustrative. Replace it with the ID returned by the upload endpoint.

### Error Handling

The API returns appropriate HTTP errors for:

- Unsupported file extensions.
- Invalid Shapefile ZIP archives.
- File processing failures.
- Requests for nonexistent file IDs.

## Architecture and Processing Flow

### File Upload and Processing

1. Receive the uploaded file.
2. Validate the filename and supported extension.
3. Save the file using a unique stored filename.
4. Validate ZIP archives for required Shapefile components.
5. Read the geospatial data using GeoPandas.
6. Extract feature indexes, geometry types, and properties.
7. Calculate measurements using the appropriate CRS.
8. Store file metadata and feature results in SQLite.
9. Return the file identifier and upload information.

Successful uploads return the upload information. If processing fails, the API returns an error response and records the failure status and error message when possible.

### Measurement Calculation

- **Point:** No area or length is calculated.
- **LineString:** Calculate length after projecting geographic coordinates when necessary.
- **Polygon:** Calculate area after projecting geographic coordinates when necessary.
- **Other geometry types:** Return no area or length measurement.

### Frontend and Backend Communication

The Streamlit frontend sends HTTP requests to the FastAPI backend.

1. The user selects a geospatial file in the frontend.
2. Streamlit sends the file to `POST /api/files/`.
3. FastAPI validates and processes the file, calculates measurements, and stores the results.
4. Streamlit uses the returned file ID to request file details and measurements.
5. The frontend displays the metadata and formatted measurement results.

Measurement calculations remain in the backend, so the frontend does not duplicate the geospatial processing logic.

## Coordinate Reference System (CRS) Handling

Geographic CRS values such as EPSG:4326 represent coordinates in degrees. Calculating area or distance directly from these coordinates would produce unsuitable measurement units.

The service checks the input CRS before measurement calculations:

1. If the CRS is missing, measurement processing fails with an error.
2. If the CRS is geographic, GeoPandas estimates a suitable UTM CRS using `estimate_utm_crs()`.
3. The geometries are transformed using `to_crs()`.
4. Area and length are calculated using the projected geometries.

For suitable projected coordinate systems such as UTM, Polygon area is expressed in square metres and LineString length in metres.

The source CRS is retained as file metadata, while the transformed geometries are used for measurement calculations.

UTM estimation is appropriate for many datasets within a suitable projection zone. Very large geometries or geometries spanning multiple projection zones may require a different projection strategy.

## Database Design

The application uses two tables.

### `files`

Stores file-level metadata, including filename, file type, source CRS, feature count, processing status, error information, and creation time.

### `features`

Stores extracted feature information, including its parent file ID, feature index, geometry type, properties, area, and length.

Uploaded file contents are stored on the filesystem. SQLite stores the associated metadata and calculated results.

When running with Docker Compose, the database and uploaded files are stored in separate named volumes to preserve data across container recreation.

## Design Decisions

- **FastAPI:** Chosen to provide a lightweight REST API with automatic OpenAPI documentation and straightforward endpoint development.
- **Streamlit instead of a JavaScript frontend:** Provides a simple Python-based interface without requiring a separate JavaScript framework. The frontend communicates with the backend through HTTP requests.
- **SQLite instead of PostGIS:** SQLite keeps setup simple and avoids requiring a separate database server. PostGIS would be more suitable if the application needed advanced spatial queries or larger-scale spatial data management.
- **SQLAlchemy:** Provides database models and query operations without requiring raw SQL for every database interaction.
- **GeoPandas, Shapely, and PyProj:** Handle geospatial file reading, geometry operations, CRS transformations, and measurements.
- **Filesystem storage instead of database binary storage:** Uploaded files are stored separately from their metadata and measurement results, avoiding the need to store file contents in SQLite.
- **Synchronous processing instead of background jobs:** Files are processed during the upload request, keeping the architecture straightforward for this assignment. Background workers would be more appropriate for large files or long-running workloads.
- **Docker Compose:** Runs the backend and frontend in separate containers, provides internal service networking, and manages persistent storage volumes.

## Running Tests

Run the automated test suite from the project root:

```bash
python -m pytest tests/test_files.py -v
```

The tests cover:

- Requests for nonexistent file IDs.
- Valid KML uploads.
- Unsupported file extensions.
- Invalid ZIP archives.
- Measurement retrieval.
- Polygon area calculation.
- LineString length calculation.

## Limitations and Future Improvements

- Add support for more geometry types, such as MultiPolygon and MultiLineString measurements.
- Improve CRS selection for large datasets or geometries spanning multiple projection zones.
- Add file-size limits and stronger protections against malicious or oversized archives.
- Introduce background processing for large uploads.
- Add pagination for files containing many features.
- Expand automated tests for missing CRS, empty files, malformed archives, and additional geometry types.
- Consider a spatial database such as PostGIS if advanced spatial queries become necessary.

## Learning Outcomes

This project provided practical experience with REST API development, file validation, geospatial data processing, CRS transformations, database persistence, frontend-backend communication, error handling, automated testing, containerization, and persistent storage using Docker Compose.