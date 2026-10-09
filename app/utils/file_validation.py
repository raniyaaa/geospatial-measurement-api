from pathlib import Path
import zipfile


def validate_shapefile_zip(file_path: str) -> None:
    path = Path(file_path)

    if not zipfile.is_zipfile(path):
        raise ValueError("Uploaded file is not a valid ZIP archive")

    with zipfile.ZipFile(path, "r") as zip_file:
        files = zip_file.namelist()

    extensions = {
        Path(name).suffix.lower()
        for name in files
        if not name.endswith("/")
    }

    required_extensions = {".shp", ".shx", ".dbf"}

    if not required_extensions.issubset(extensions):
        raise ValueError(
            "ZIP file does not contain a complete Shapefile"
        )