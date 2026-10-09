import geopandas as gpd
import json
import pandas as pd

def clean_properties(properties):
    cleaned = {}

    for key, value in properties.items():
        if pd.isna(value):
            cleaned[key] = None
        else:
            cleaned[key] = value

    return cleaned

def read_geospatial_file(file_path: str) -> gpd.GeoDataFrame:
    if file_path.lower().endswith(".kml"):
        return gpd.read_file(file_path, driver="KML")

    if file_path.lower().endswith(".zip"):
        return gpd.read_file(file_path)

    raise ValueError("Unsupported file type")


def extract_features(gdf):
    features = []

    for index, row in gdf.iterrows():
        feature = {
            "feature_index": index,
            "geometry_type": row.geometry.geom_type,
            "properties": row.drop("geometry").to_dict()
        }

        features.append(feature)

    return features

def calculate_measurements(gdf):
    measurements = []

    projected_gdf = gdf

    if gdf.crs is None:
        raise ValueError("CRS is required for measurement calculation")

    # print("Original CRS:", gdf.crs)

    if gdf.crs.is_geographic:
        projected_crs = gdf.estimate_utm_crs()
        # print("Projected CRS:", projected_crs)

        projected_gdf = gdf.to_crs(projected_crs)

    for geometry in projected_gdf.geometry:
        geometry_type = geometry.geom_type

        if geometry_type == "Point":
            measurements.append({
                "area": None,
                "length": None
            })

        elif geometry_type == "LineString":
            measurements.append({
                "area": None,
                "length": geometry.length
            })

        elif geometry_type == "Polygon":
            measurements.append({
                "area": geometry.area,
                "length": None
            })

        else:
            measurements.append({
                "area": None,
                "length": None
            })

    return measurements

#combiining all the 3 above functions

def process_features(gdf):
    features = extract_features(gdf)
    measurements = calculate_measurements(gdf)

    for feature, measurement in zip(features, measurements):
        feature["area"] = measurement["area"]
        feature["length"] = measurement["length"]

    return features