#!/usr/bin/env python3
"""
This script generates Traffic Analysis Zones (TAZ) for a specified area of Berlin and
classifies building footprints based on certain attributes. It:
- Fetches building footprints from OpenStreetMap using OSMnx
- Performs clustering to create TAZ polygons
- Optionally classifies buildings (e.g., residential)
- Saves the results in a GeoPackage format to avoid shapefile limitations
- Displays and saves a plot of the resulting TAZ polygons and buildings
"""

import osmnx as ox
import geopandas as gpd
from shapely.geometry import Polygon
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt

# ------------------------- Configuration -------------------------
city_name = "Berlin, Germany"
EPSG_CODE = 25833          # Projected CRS for accurate spatial operations
NUM_TAZ = 50               # Adjust as needed
output_taz_file = "wedding_taz_zones.gpkg"
output_buildings_file = "wedding_buildings.gpkg"
output_plot_file = "wedding_taz_plot.png"

# Attributes to fetch and classify.
ATTRIBUTES = {
    "building": {
        "fetch": True,
        "categories": {
            "residential": ["residential", "apartments", "house", "terrace"]
        }
    },
    "amenity": {
        "fetch": True,
        "categories": None
    },
    "office": {
        "fetch": True,
        "categories": None
    },
    "shop": {
        "fetch": True,
        "categories": None
    },
    "craft": {
        "fetch": True,
        "categories": None
    }
}

# ----------------------- Data Retrieval ---------------------------
print("Fetching Berlin boundary from OSM...")
berlin_polygon = ox.geocode_to_gdf(city_name)

# ---------- Crop Berlin Boundary to Wedding Area Immediately ----------
# Provided geo coordinates for Wedding (lon_min, lat_min, lon_max, lat_max)
prune_boundary_geo = (13.3015376, 52.5356604, 13.3749244, 52.5644452)
xmin, ymin, xmax, ymax = prune_boundary_geo
# Create a polygon in WGS84 (EPSG:4326) representing the Wedding area
wedding_poly = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)])
wedding_gdf = gpd.GeoDataFrame({'geometry': [wedding_poly]}, crs="EPSG:4326")

# Clip the Berlin boundary to the Wedding area to reduce the spatial extent
wedding_boundary = gpd.clip(berlin_polygon, wedding_gdf)
print("Cropped Berlin boundary to the Wedding area.")

# Fetch building features using the cropped polygon instead of the entire city
print("Fetching building data from OSM for the Wedding area...")
tags = {attr: True for attr, conf in ATTRIBUTES.items() if conf["fetch"]}
# Use the wedding_boundary polygon (geometry) for the query:
buildings = ox.features_from_polygon(wedding_boundary.geometry.iloc[0], tags=tags)
buildings = buildings[buildings.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

print(f"Number of buildings fetched: {len(buildings)}")

# ---------------- Reproject to a Projected CRS ---------------------
print(f"Reprojecting data to EPSG:{EPSG_CODE}...")
buildings = buildings.to_crs(epsg=EPSG_CODE)
wedding_boundary = wedding_boundary.to_crs(epsg=EPSG_CODE)

# --------------------- Generate TAZ -------------------------------
print("Generating TAZ by clustering building centroids...")
# Use centroids of buildings for clustering
building_centroids = buildings.geometry.centroid
X = np.column_stack((building_centroids.x, building_centroids.y))

# Ensure we don't have more clusters than buildings
num_buildings = len(buildings)
if num_buildings < NUM_TAZ:
    print(f"Warning: Only {num_buildings} buildings found. Reducing NUM_TAZ from {NUM_TAZ} to {num_buildings}.")
    NUM_TAZ = max(1, num_buildings)

kmeans = KMeans(n_clusters=NUM_TAZ, random_state=0, n_init="auto").fit(X)
buildings["TAZ_id"] = kmeans.labels_

taz_polygons = []
print("Forming TAZ polygons...")
for cluster_id in range(NUM_TAZ):
    cluster_geoms = buildings.loc[buildings["TAZ_id"] == cluster_id, "geometry"]
    # Create a union of all geometries in the cluster
    combined = cluster_geoms.unary_union  # Using unary_union for a combined geometry
    if not combined.is_empty:
        taz_polygons.append({"TAZ_id": cluster_id, "geometry": combined.convex_hull})

taz_gdf = gpd.GeoDataFrame(taz_polygons, crs=buildings.crs)
# Intersect with the Wedding boundary to limit TAZ extent
taz_gdf = gpd.overlay(taz_gdf, wedding_boundary, how="intersection")

print(f"Number of TAZ generated: {len(taz_gdf)}")

# -------------------- Classification (Optional) --------------------
print("Classifying buildings based on defined categories...")
for attr in ATTRIBUTES.keys():
    if attr not in buildings.columns:
        buildings[attr] = None

for attr, config in ATTRIBUTES.items():
    if config["categories"] and attr in buildings.columns:
        for cat_name, values in config["categories"].items():
            cat_mask = buildings[attr].isin(values)
            buildings.loc[cat_mask, "category"] = cat_name
print("Classification complete.")

# --------------------- Spatial Indexing ----------------------------
print("Building spatial indexes as example...")
_ = taz_gdf.sindex
if "category" in buildings.columns:
    residential_buildings = buildings[buildings["category"] == "residential"]
    _ = residential_buildings.sindex

print("Spatial indexing complete.")

# ----------------------- Save Results ------------------------------
print(f"Saving TAZ to {output_taz_file} and buildings to {output_buildings_file}...")
taz_gdf.to_file(output_taz_file, driver="GPKG")

# Keep only essential columns
essential_cols = ["geometry", "building", "category", "TAZ_id"]
for attr in ["amenity", "office", "shop", "craft"]:
    if attr in buildings.columns:
        essential_cols.append(attr)

buildings = buildings[essential_cols]

# Ensure uniqueness again
buildings = buildings.loc[:, ~buildings.columns.duplicated()]

# Replace colons in column names, if any
buildings.columns = [c.replace(":", "_") for c in buildings.columns]

# Now save to GeoPackage
buildings.to_file(output_buildings_file, driver="GPKG")

print("Data saved successfully.")

# ---------------------- Visualization ------------------------------
print("Creating plot for visualization...")
fig, ax = plt.subplots(figsize=(10, 10))

# Plot TAZ polygons
taz_gdf.plot(ax=ax, color="lightblue", edgecolor="black", alpha=0.5)

if "category" in buildings.columns:
    # If categories exist, highlight residential buildings
    buildings_no_cat = buildings[buildings["category"].isnull()]
    buildings_no_cat.plot(ax=ax, color="grey", markersize=2, alpha=0.5, label="Other Buildings")
    if not residential_buildings.empty:
        residential_buildings.plot(ax=ax, color="red", markersize=2, alpha=0.7, label="Residential")
else:
    # Otherwise, show all buildings in one color
    buildings.plot(ax=ax, color="grey", markersize=2, alpha=0.5, label="Buildings")

ax.set_title("TAZ Polygons and Buildings in Wedding (Berlin)", fontsize=14)
ax.set_axis_off()
ax.legend()

plt.tight_layout()
plt.savefig(output_plot_file, dpi=300)
print(f"Plot saved as {output_plot_file}")
plt.show()

print("Script execution completed.")
