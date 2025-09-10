import geopandas as gpd
import numpy as np
from shapely.geometry import Point


class ClosestLocationChoice:
    def __init__(self,
                 buildings_file="data/taz/berlin_buildings.gpkg",
                 taz_file="data/taz/berlin_taz_zones.gpkg",
                 candidate_attributes=None):
        # Load buildings and TAZ polygons
        self.buildings = gpd.read_file(buildings_file)
        self.taz = gpd.read_file(taz_file)
        if self.buildings.crs != self.taz.crs:
            self.taz = self.taz.to_crs(self.buildings.crs)

        # Calculate area (or default to 1.0) and ensure a “category” column
        if not self.buildings.empty and self.buildings.geometry.iloc[0].geom_type in ["Polygon", "MultiPolygon"]:
            self.buildings["area"] = self.buildings.geometry.area
        else:
            self.buildings["area"] = 1.0
        if "category" not in self.buildings.columns:
            self.buildings["category"] = None

        # Set candidate attributes (only keep those that exist in the buildings data)
        if candidate_attributes is None:
            self.candidate_attributes = ["building", "amenity", "office", "shop", "craft"]
        else:
            self.candidate_attributes = candidate_attributes
        self.candidate_attributes = [attr for attr in self.candidate_attributes if attr in self.buildings.columns]

        # Precompute residential buildings
        self.residential_buildings = self.buildings[self.buildings["category"] == "residential"]

        # Precompute a spatial index on the full buildings dataset (for other uses)
        self.buildings_sindex = self.buildings.sindex

        # Cache for filtered candidate sets (so that repeated calls with the same filter do not recompute)
        self.candidates_cache = {}

    def get_attribute_values(self, attribute=None):
        if attribute is None:
            all_values = []
            for attr in self.candidate_attributes:
                all_values.extend(self.buildings[attr].dropna().unique().tolist())
            return list(set(all_values))
        elif attribute in self.buildings.columns:
            return self.buildings[attribute].dropna().unique().tolist()
        return []

    def sample_residential_apartment_location(self):
        """Sample a residential building (weighted by area)."""
        if self.residential_buildings.empty:
            raise ValueError("No residential buildings found.")
        areas = self.residential_buildings["area"].values
        p = areas / areas.sum()
        selected_index = np.random.choice(self.residential_buildings.index, size=1, p=p)
        return self.residential_buildings.loc[selected_index]

    def _find_attribute_for_value(self, attribute_value):
        for attr in self.candidate_attributes:
            if attribute_value in self.buildings[attr].dropna().unique():
                return attr
        return None

    def _get_candidates(self, attribute=None, attribute_value=None):
        """
        Retrieve or compute the candidate GeoDataFrame based on attribute filters.
        The result is cached based on the (attribute, attribute_value) tuple.
        """
        cache_key = (attribute, attribute_value)
        if cache_key in self.candidates_cache:
            return self.candidates_cache[cache_key]

        if attribute is not None:
            if attribute_value is not None:
                candidates = self.buildings[self.buildings[attribute] == attribute_value]
            else:
                candidates = self.buildings[~self.buildings[attribute].isnull()]
        else:
            candidates = self.buildings

        # Cache the result for future calls.
        self.candidates_cache[cache_key] = candidates
        return candidates

    def sample_building_near_reference(self, reference_point, attribute=None, attribute_value=None):
        if not isinstance(reference_point, Point):
            reference_point = Point(reference_point)

        if attribute is None and attribute_value is not None:
            attribute = self._find_attribute_for_value(attribute_value)

        candidates = self._get_candidates(attribute, attribute_value)
        if candidates.empty:
            return gpd.GeoDataFrame(geometry=[], crs=self.buildings.crs)

        nearest_idx = candidates.sindex.nearest(reference_point, return_all=False)
        candidate_idx = nearest_idx[1, 0]

        nearest_building = candidates.iloc[[candidate_idx]]
        return nearest_building
