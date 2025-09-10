import json


def map_list_of_lists_to_string(my_list):
    return ','.join(map(str, [item for sublist in my_list for item in sublist]))


def get_bounding_rectangle(coordinates):
    min_lon = min(coordinate[0] for coordinate in coordinates)
    max_lon = max(coordinate[0] for coordinate in coordinates)
    min_lat = min(coordinate[1] for coordinate in coordinates)
    max_lat = max(coordinate[1] for coordinate in coordinates)

    return min_lon, min_lat, max_lon, max_lat


geojson_path = '../../data/open_street_map/wedding/wedding.geojson'
with open(geojson_path) as f:
    wedding = json.load(f)

wedding_boundaries = wedding['features'][0]['geometry']['coordinates'][0]

xmin, ymin, xmax, ymax = get_bounding_rectangle(wedding_boundaries)

print(f"{xmin},{ymin},{xmax},{ymax}")
