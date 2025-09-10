from module.action.sumo.traci_wrapper import start_sim, get_num_expected_vehicles, \
    simulation_step, stop_sim, find_route, add_pedestrian, \
    add_car, add_bicycle, find_intermodal_route, add_intermodal
from model.building import Building
from model.possible_route import PossibleRoute


class SumoAdapter:
    def __init__(self, urban_sampler, net_file, poly_file, v_types_file, pt_stops_file, pt_vehicles_file):
        self.urban_sampler = urban_sampler
        self.building_categories = urban_sampler.get_attribute_values()

        self.start_sim(net_file, poly_file, v_types_file, pt_stops_file, pt_vehicles_file)

    def start_sim(self, net_file, poly_file, v_types_file, pt_stops_file, pt_vehicles_file):
        start_sim(net_file, poly_file, v_types_file, pt_stops_file, pt_vehicles_file)

    def should_continue_sim(self):
        num_vehicles = get_num_expected_vehicles()
        return True if num_vehicles > 0 else False

    def simulation_step(self):
        simulation_step()

    def stop_sim(self):
        stop_sim()

    def row_to_building(self, row, parameters):
        polygon_id = row['id']

        location = row['geometry'].centroid

        building = Building(polygon_id=polygon_id, parameters=parameters, location=location)
        return building

    def get_random_apartment(self):
        apartment = self.urban_sampler.sample_residential_apartment_location()
        apartment = self.row_to_building(apartment.iloc[0], ['apartment'])
        return apartment

    def get_building_with(self, reference_point, attribute_value):
        building = self.urban_sampler.sample_building_near_reference(reference_point, attribute_value=attribute_value)
        building = self.row_to_building(building.iloc[0], [attribute_value])
        return building

    def get_passenger_route(self, from_location, to_location):
        route = self.get_route(from_location, to_location, v_class='passenger', v_type='DEFAULT_VEHTYPE')
        return PossibleRoute('passenger', route.edges, route.travelTime, route.length)

    def get_pedestrian_route(self, from_location, to_location):
        route = self.get_route(from_location, to_location, v_class='pedestrian', v_type='DEFAULT_PEDTYPE')
        return PossibleRoute('pedestrian', route.edges, route.travelTime, route.length)

    def get_bicycle_route(self, from_location, to_location):
        route = self.get_route(from_location, to_location, v_class='bicycle', v_type='DEFAULT_BIKETYPE')
        return PossibleRoute('bicycle', route.edges, route.travelTime, route.length)

    def get_intermodal_route(self, from_location, to_location, arrival_time):
        route = find_intermodal_route(from_location, to_location, arrival_time)
        if not route:
            return PossibleRoute('public transport', None, None, None)
        travel_time = sum(stage.travelTime for stage in route)
        length = sum(stage.length for stage in route)
        from_edge = route[0].edges[0]
        to_edge = route[-1].edges[-1]
        return PossibleRoute('public transport', [from_edge, to_edge], travel_time, length)

    def get_route(self, start_pos, end_pos, v_class='passenger', v_type='DEFAULT_VEHTYPE'):
        return find_route(start_pos, end_pos, v_class=v_class, v_type=v_type)

    def add_traffic_participant(self, route):
        means_of_transport = route['means_of_transport']
        if means_of_transport == 'pedestrian':
            return add_pedestrian(route)
        elif means_of_transport == 'bicycle':
            return add_bicycle(route)
        elif means_of_transport == 'public transport':
            return add_intermodal(route)
        elif means_of_transport == 'passenger':
            return add_car(route)
        else:
            raise Exception(f'Not implemented means of transport was chosen: {means_of_transport}')

    def get_building_categories(self):
        return self.building_categories

    def get_building_categories_string(self):
        return ', '.join(self.get_building_categories())
