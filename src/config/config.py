config_minimal = {
    'workers': 1,
    'num_agents': 8,
    'load_from_storage': False,
    'storage_path': 'results/minimal',
    'buildings_file': 'data/taz/berlin_buildings.gpkg',
    'taz_file': 'data/taz/berlin_taz_zones.gpkg',
    'net_file': 'data/open_street_map/berlin/berlin.net.xml',
    'poly_file': 'data/open_street_map/berlin/berlin.poly.xml',
    'v_types_file': '',
    'pt_stops_file': 'data/open_street_map/berlin/gtfs_pt_stops.add.xml',
    'pt_vehicles_file': 'data/open_street_map/berlin/validated.gtfs_pt_vehicles.add.xml',
    'census_file': 'data/census/B1_Standard-Datensatzpaket/CSV/MiD2017_Personen.csv',
    'day': 'Monday',
    'exclude_too_young': True,
    'exclude_too_old': False
}

config_berlin_sumo = {
    'workers': 8,
    'num_agents': 35769,
    # 3,576,870 * (1/100) = 35769 -> https://esa.un.org/unpd/wup/  / https://worldpopulationreview.com/cities/germany/berlin
    'load_from_storage': False,
    'storage_path': 'results/baseline-monday-berlin-sumo',
    'buildings_file': 'data/taz/berlin_buildings.gpkg',
    'taz_file': 'data/taz/berlin_taz_zones.gpkg',
    'net_file': 'data/open_street_map/berlin/berlin.net.xml',
    'poly_file': 'data/open_street_map/berlin/berlin.poly.xml',
    'v_types_file': '',
    'pt_stops_file': 'data/open_street_map/berlin/gtfs_pt_stops.add.xml',
    'pt_vehicles_file': 'data/open_street_map/berlin/validated.gtfs_pt_vehicles.add.xml',
    'census_file': 'data/census/B1_Standard-Datensatzpaket/CSV/MiD2017_Personen.csv',
    'day': 'Monday',
    'exclude_too_young': True,
    'exclude_too_old': False
}

config_berlin_otp = {
    'workers': 8,
    'num_agents': 35769,
    'load_from_storage': True,
    'storage_path': 'results/baseline-monday-berlin-otp',
    'buildings_file': 'data/taz/berlin_buildings.gpkg',
    'taz_file': 'data/taz/berlin_taz_zones.gpkg',
    'net_file': 'data/open_street_map/berlin/berlin.net.xml',
    'poly_file': 'data/open_street_map/berlin/berlin.poly.xml',
    'v_types_file': 'data/open_street_map/berlin/vtypes.xml',
    'pt_stops_file': 'data/open_street_map/berlin/gtfs_pt_stops.add.xml',
    'pt_vehicles_file': 'data/open_street_map/berlin/gtfs_pt_vehicles.add.xml',
    'census_file': 'data/census/B1_Standard-Datensatzpaket/CSV/MiD2017_Personen.csv',
    'day': 'Monday',
    'exclude_too_young': True,
    'exclude_too_old': False
}

config_wedding_sumo = {
    'workers': 8,
    'num_agents': 8680,
    'load_from_storage': False,
    'storage_path': 'results/baseline-monday-wedding-sumo',
    'buildings_file': 'data/taz/wedding_buildings.gpkg',
    'taz_file': 'data/taz/wedding_taz_zones.gpkg',
    'net_file': 'data/open_street_map/wedding/wedding.net.xml',
    'poly_file': 'data/open_street_map/wedding/wedding.poly.xml',
    'v_types_file': 'data/open_street_map/wedding/vtypes.xml',
    'pt_stops_file': 'data/open_street_map/wedding/gtfs_pt_stops.add.xml',
    'pt_vehicles_file': 'data/open_street_map/wedding/gtfs_pt_vehicles.add.xml',
    'census_file': 'data/census/B1_Standard-Datensatzpaket/CSV/MiD2017_Personen.csv',
    'day': 'Monday',
    'exclude_too_young': True,
    'exclude_too_old': False
}

config_wedding_otp = {
    'workers': 8,
    'num_agents': 8680,
    'load_from_storage': True,
    'storage_path': 'results/baseline-monday-wedding-otp',
    'buildings_file': 'data/taz/wedding_buildings.gpkg',
    'taz_file': 'data/taz/wedding_taz_zones.gpkg',
    'net_file': 'data/open_street_map/wedding/wedding.net.xml',
    'poly_file': 'data/open_street_map/wedding/wedding.poly.xml',
    'v_types_file': 'data/open_street_map/wedding/vtypes.xml',
    'pt_stops_file': 'data/open_street_map/wedding/gtfs_pt_stops.add.xml',
    'pt_vehicles_file': 'data/open_street_map/wedding/gtfs_pt_vehicles.add.xml',
    'census_file': 'data/census/B1_Standard-Datensatzpaket/CSV/MiD2017_Personen.csv',
    'day': 'Monday',
    'exclude_too_young': True,
    'exclude_too_old': False
}
