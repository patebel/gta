from pyproj import Transformer

from module.action.sumo.traci_wrapper import get_cart_coordinates


class Building:
    def __init__(self, polygon_id, parameters, location):
        self.polygon_id = polygon_id
        self.parameters = parameters
        self.location = location

    def get_location(self, geo=False):
        transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(self.location.x, self.location.y)
        if geo:
            return lon, lat
        cart_coordinates = get_cart_coordinates(lon, lat)
        return cart_coordinates

    def to_dict(self):
        return {
            "polygon_id": str(self.polygon_id),
            "parameters": self.parameters,
            "location": {"x": int(self.location.x), "y": int(self.location.y)}  # Convert Point to a dictionary
        }

    @classmethod
    def from_json(cls, data):
        location = data["location"]
        if isinstance(location, dict) and "x" in location and "y" in location:
            from shapely.geometry import Point  # Import Point only if necessary
            location = Point(location["x"], location["y"])  # Convert dict to Point

        return cls(
            polygon_id=data["polygon_id"],
            parameters=data["parameters"],
            location=location
        )
