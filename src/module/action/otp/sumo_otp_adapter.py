import random
from datetime import datetime, timedelta, timezone

from module.action.otp.otp_wrapper import OTPWrapper
from module.action.sumo.traci_wrapper import start_sim, stop_sim, get_polygon_position, get_polygons_with_parameters, \
    get_geo_coordinates
from model.possible_route import PossibleRoute


class SumoOTPAdapter:
    def __init__(self, net_file, poly_file, v_types_file, pt_stops_file, pt_vehicles_file, otp_api_url):
        self.start_sim(net_file, poly_file, v_types_file, pt_stops_file, pt_vehicles_file)

        self.building_category_keys = ['building', 'amenity', 'office', 'shop', 'craft']
        self.buildings = get_polygons_with_parameters(self.building_category_keys)

        self.building_categories = self.merge_building_category_values()
        self.building_categories.insert(0, 'home')

        self.building_by_categories = self.create_building_by_categories()

        today = datetime.now(tz=timezone.utc).date()
        days_since_monday = (today.weekday() + 1) % 7
        date = today - timedelta(days=days_since_monday)

        self.route_planner = OTPWrapper(otp_api_url, date)

    def merge_building_category_values(self):
        building_categories = set()
        for building in self.buildings:
            for building_category_dict in building['parameters']:
                for value in building_category_dict.values():
                    if value != '':
                        building_categories.add(value)
        return list(building_categories)

    def create_building_by_categories(self):
        buildings_by_categories = {}

        for building in self.buildings:
            for building_category_dict in building['parameters']:
                for value in building_category_dict.values():
                    if value != '':
                        if value not in buildings_by_categories:
                            buildings_by_categories[value] = []
                        buildings_by_categories[value].append(building)

        return buildings_by_categories

    def start_sim(self, net_file, poly_file, v_types_file, pt_stops_file, pt_vehicles_file):
        start_sim(net_file, poly_file, v_types_file, pt_stops_file, pt_vehicles_file)

    def should_continue_sim(self):
        raise NotImplementedError()

    def simulation_step(self):
        raise NotImplementedError()

    def stop_sim(self):
        stop_sim()

    def get_new_apartment_for(self, generative_agent):
        return self.get_random_apartment()

    def get_new_workplace_for(self, generative_agent):
        return self.get_random_workplace()

    def get_random_apartment(self):
        return self.get_building_with('apartments')

    def get_random_workplace(self):
        return self.get_building_not_with('apartments')

    def get_polygon_position(self, polygon_id):
        cart_coordinates = get_polygon_position(polygon_id)
        geo_coordinates = get_geo_coordinates(cart_coordinates)
        return geo_coordinates

    def get_passenger_route(self, from_location, to_location):
        route = self.route_planner.get_passenger_route(from_location, to_location)
        return PossibleRoute('passenger', route.get('description'), route.get('duration'), route.get('distance'))

    def get_pedestrian_route(self, from_location, to_location):
        route = self.route_planner.get_pedestrian_route(from_location, to_location)
        return PossibleRoute('pedestrian', route.get('description'), route.get('duration'), route.get('distance'))

    def get_bicycle_route(self, from_location, to_location):
        route = self.route_planner.get_bicycle_route(from_location, to_location)
        return PossibleRoute('bicycle', route.get('description'), route.get('duration'), route.get('distance'))

    def get_intermodal_route(self, from_location, to_location, arrival_time):
        route = self.route_planner.get_intermodal_route(from_location, to_location, arrival_time)
        return PossibleRoute('public transport', route.get('description'), route.get('duration'), route.get('distance'))

    def get_route(self, start_pos, end_pos, v_class='passenger', v_type='DEFAULT_VEHTYPE'):
        raise NotImplementedError()

    def add_traffic_participant(self, route):
        means_of_transport = route['means_of_transport']
        if means_of_transport == 'pedestrian':
            pass
        elif means_of_transport == 'bicycle':
            pass
        elif means_of_transport == 'public transport':
            pass
        elif means_of_transport == 'passenger':
            pass
        else:
            raise Exception(f'Not implemented means of transport was chosen: {means_of_transport}')

    def get_polygons_with_parameters(self, parameters):
        return get_polygons_with_parameters(parameters)

    def get_building_with(self, category):
        candidates = self.building_by_categories[category]
        return random.choice(candidates)

    def get_building_not_with(self, category):
        candidates = [value for key, values in self.building_by_categories.items() for value in values if
                      key != category]
        return random.choice(candidates)

    def get_building_categories(self):
        return self.building_categories

    def get_building_categories_string(self):
        return ', '.join(self.get_building_categories())
