import geopandas as gpd
from shapely.geometry import Polygon
from pathlib import Path
import shutil


polygon = Polygon([
    (13.405, 52.520),
    (13.406, 52.520),
    (13.406, 52.521),
    (13.405, 52.521),
    (13.405, 52.520)
])

gdf = gpd.GeoDataFrame(
    {"name": ["Test Polygon"]},
    geometry=[polygon],
    crs="EPSG:4326"
)

output_dir = Path("test_shapefile")
output_dir.mkdir(exist_ok=True)

shapefile_path = output_dir / "test_polygon.shp"

gdf.to_file(shapefile_path)

shutil.make_archive(
    "test_shapefile",
    "zip",
    output_dir
)

print("Created test_shapefile.zip")