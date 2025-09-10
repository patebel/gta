import argparse
import copy
import json
import random

import libsumo as traci

from model.agent import Agent
from util.file import write_file
from util.trips import generate_trips_xml


def start_sim(net_file, pt_stops_file, pt_vehicles_file):
    traci.start(
        [
            'sumo',
            '--net-file', net_file,
            '--additional-files', pt_stops_file,
            '--route-files', pt_vehicles_file,
        ])


def get_v_class(means_of_transport):
    if means_of_transport == 'public transport':
        return 'pedestrian'
    else:
        return means_of_transport


def get_new_random_edge(edge_id, meter_interval, means_of_transport):
    x, y = traci.simulation.convert2D(edge_id, 0, laneIndex=0, toGeo=False)
    new_x = x + random.uniform(*meter_interval)
    new_y = y + random.uniform(*meter_interval)
    v_class = get_v_class(means_of_transport)
    new_edge_id, _, _ = traci.simulation.convertRoad(new_x, new_y, vClass=v_class)
    return new_edge_id


def has_route(from_edge_id, to_edge_id, means_of_transport, departure_time):
    if means_of_transport == 'public transport':
        modes = 'public'
        route = traci.simulation.findIntermodalRoute(from_edge_id, to_edge_id, modes, depart=departure_time)
    else:
        v_type = None
        if means_of_transport == 'pedestrian':
            v_type = 'DEFAULT_PEDTYPE'
        elif means_of_transport == 'bicycle':
            v_type = 'DEFAULT_BIKETYPE'
        elif means_of_transport == 'passenger':
            v_type = 'DEFAULT_VEHTYPE'
        route = traci.simulation.findRoute(from_edge_id, to_edge_id, vType=v_type)
    if route:
        return True
    else:
        return False


class AgentsReplicator:
    def __init__(self, net_file, pt_stops_file, pt_vehicles_file, agents_file, output_file):
        self.net_file = net_file
        self.pt_stops_file = pt_stops_file
        self.pt_vehicles_file = pt_vehicles_file

        self.agents_file = agents_file
        self.output_file = output_file

        self.json_agents = None
        self.agents = None

    def load_file(self):
        with open(self.agents_file, 'r') as file:
            self.json_agents = json.load(file)

    def save_file(self):
        route_descriptions = [route_description for agent in self.agents for route_description in
                              agent.route_descriptions]
        trips_xml = generate_trips_xml(route_descriptions)
        write_file(self.output_file, trips_xml)

    def start_sim(self):
        start_sim(self.net_file, self.pt_stops_file, self.pt_vehicles_file)

    def replicate_agents(self, count, time_interval, meter_interval, retries=5):
        self.agents = []
        routes_changed_count = 0
        routes_failed_changing_count = 0
        for json_agent in self.json_agents:
            for index in range(count):
                agent = copy.deepcopy(Agent.from_json(json_agent))
                agent.id = f'{agent.id}{(index + 1):03d}'
                if index != 0:
                    for route_index in range(len(agent.route_descriptions)):
                        are_valid_edges = False
                        for try_count in range(retries):
                            means_of_transport = agent.route_descriptions[route_index]['means_of_transport']
                            agent.route_descriptions[route_index][
                                'route_id'] = f"{agent.route_descriptions[route_index]['route_id']}{index:03d}"
                            departure_time = max(0.0,
                                                 (float(agent.route_descriptions[route_index]['departure_time']) +
                                                  random.uniform(*time_interval)))
                            agent.route_descriptions[route_index]['departure_time'] = departure_time

                            from_edge_id = agent.route_descriptions[route_index]['route'][0]
                            new_from_edge_id = get_new_random_edge(from_edge_id, meter_interval, means_of_transport)

                            to_edge_id = agent.route_descriptions[route_index]['route'][
                                -1]
                            new_to_edge_id = get_new_random_edge(to_edge_id, meter_interval, means_of_transport)

                            are_valid_edges = has_route(new_from_edge_id, new_to_edge_id, means_of_transport,
                                                        departure_time)
                            if are_valid_edges:
                                agent.route_descriptions[route_index]['route'] = [new_from_edge_id, new_to_edge_id]
                                break
                        if are_valid_edges:
                            routes_changed_count += 1
                        else:
                            routes_failed_changing_count += 1
                self.agents.append(agent)
        return routes_changed_count, routes_failed_changing_count

    def process(self, count, time_interval=(-120, 120), meter_interval=(-1000, 1000), retries=5):
        self.load_file()
        self.start_sim()
        routes_changed_count, routes_failed_changing_count = self.replicate_agents(count, time_interval, meter_interval,
                                                                                   retries)
        print(f'{routes_changed_count} routes were successfully changed, '
              f'{routes_failed_changing_count} routes failed to find valid edges ({retries} times)')
        self.save_file()
        print(f'Finished creating {len(self.agents)} from {len(self.json_agents)} agents')
        print(f"Expanded XML content has been saved to {self.output_file}.")


def main():
    parser = argparse.ArgumentParser(
        description="Run the AgentsReplicator with customizable file paths and parameters."
    )
    parser.add_argument(
        '--net-file',
        default='../../data/open_street_map/berlin/berlin.net.xml',
        help='Path to the SUMO network file'
    )
    parser.add_argument(
        '--pt-stops-file',
        default='../../data/open_street_map/berlin/gtfs_pt_stops.add.xml',
        help='Path to the public transport stops XML file'
    )
    parser.add_argument(
        '--pt-vehicles-file',
        default='../../data/open_street_map/berlin/validated.gtfs_pt_vehicles.add.xml',
        help='Path to the public transport vehicles XML file'
    )
    parser.add_argument(
        '--input-file',
        default='../../results/test/agents_4_route_descriptions.json',
        help='Path to the JSON file with agent route descriptions'
    )
    parser.add_argument(
        '--output-file',
        default='test.xml',
        help='Path where the expanded XML will be saved'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of times to replicate agents'
    )
    parser.add_argument(
        '--time-interval',
        nargs=2,
        type=int,
        metavar=('START', 'END'),
        default=[-300, 300],
        help='Time interval for agent injection (start, end)'
    )
    parser.add_argument(
        '--meter-interval',
        nargs=2,
        type=int,
        metavar=('START', 'END'),
        default=[-1000, 1000],
        help='Distance interval for agent injection (start, end)'
    )

    args = parser.parse_args()

    replicator = AgentsReplicator(
        args.net_file,
        args.pt_stops_file,
        args.pt_vehicles_file,
        args.input_file,
        args.output_file
    )
    replicator.process(
        count=args.count,
        time_interval=(args.time_interval[0], args.time_interval[1]),
        meter_interval=(args.meter_interval[0], args.meter_interval[1])
    )


if __name__ == '__main__':
    main()
