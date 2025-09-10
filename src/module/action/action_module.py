import json
from typing import List

from model.agent import Agent
from model.building import Building
from model.possible_route import PossibleRoute
from util.logging import log_error
from util.time import time_to_seconds


class ActionModule:
    @staticmethod
    def get_possible_routes_for_agents(agents: List[Agent], traffic_sim, use_geocoord=False) -> List[Agent]:
        for agent in agents:
            for index, location_change in enumerate(agent.location_changes):
                try:
                    from_location = location_change.from_building.get_location(geo=use_geocoord)
                    to_location = location_change.to_building.get_location(geo=use_geocoord)
                    arrival_time = time_to_seconds(location_change.to_task.time)
                    possible_routes = ActionModule.get_possible_routes(from_location,
                                                                       to_location,
                                                                       arrival_time,
                                                                       traffic_sim)
                    agent.location_changes[index].possible_routes = possible_routes
                except Exception as e:
                    log_error(f'{e}\n\n'
                              f'from_location:{from_location}\n'
                              f'to_location:{to_location}\n\n'
                              f'location change:{json.dumps(agent.location_changes[index].to_dict(), indent=4)}\n\n'
                              f'agent{json.dumps(agent.to_json(), indent=4)}\n\n')
        return agents

    @staticmethod
    def get_possible_routes(from_location, to_location, arrival_time, traffic_sim) -> List[PossibleRoute]:
        passenger_route = traffic_sim.get_passenger_route(from_location, to_location)
        pedestrian_route = traffic_sim.get_pedestrian_route(from_location, to_location)
        bicycle_route = traffic_sim.get_bicycle_route(from_location, to_location)
        intermodal_route = traffic_sim.get_intermodal_route(from_location, to_location, arrival_time)

        if not passenger_route.route and not pedestrian_route.route and not bicycle_route.route and not intermodal_route.route:
            raise Exception(f'No route found!')

        possible_routes = []
        if passenger_route.route:
            possible_routes.append(passenger_route)
        if pedestrian_route.route:
            possible_routes.append(pedestrian_route)
        if bicycle_route.route:
            possible_routes.append(bicycle_route)
        if intermodal_route.route:
            possible_routes.append(intermodal_route)

        return possible_routes

    @staticmethod
    def get_building_with(agent: Agent, building_type, traffic_sim, reference_location=None) -> Building:
        if reference_location is None:
            reference_location = agent.home.location
        building = agent.home if building_type == 'home' else traffic_sim.get_building_with(reference_location,
                                                                                            building_type)
        return building

    @staticmethod
    def generate_route_id(agent_id, index):
        return int(f"{agent_id}{index:02d}{index + 1:02d}")
