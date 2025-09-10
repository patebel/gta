import json
import os
from collections import Counter

import pandas as pd


class SimulationResults:
    def __init__(self, result_folder):
        self.result_folder = result_folder

        print('Loading data...')
        # Adjust file paths as needed
        self.agents_with_descriptions = self.load_json(os.path.join(self.result_folder, 'agents_1_description.json'))
        self.agents_with_no_descriptions = self.load_json(
            os.path.join(self.result_folder, 'agents_1_no_description.json'))
        self.agents_location_changes = self.load_json(
            os.path.join(self.result_folder, 'agents_3_location_changes.json'))
        self.agents_no_location_changes = self.load_json(
            os.path.join(self.result_folder, 'agents_3_no_location_changes.json'))
        self.agents_with_routes = self.load_json(os.path.join(self.result_folder, 'agents_4_route_descriptions.json'))
        print('Data loaded!')

        # Counts
        self.total_simulated_agents_count = len(self.agents_with_descriptions)
        self.total_skipped_agents_count = len(self.agents_with_no_descriptions)
        self.total_agents_count = self.total_simulated_agents_count + self.total_skipped_agents_count

        self.agents_location_changes_count = len(self.agents_location_changes)
        self.agents_no_location_changes_count = len(self.agents_no_location_changes)
        self.total_agents_until_location_changes_count = self.agents_location_changes_count + self.agents_no_location_changes_count
        self.agents_with_routes_count = len(self.agents_with_routes)

    def recursively_parse_json(self, obj):
        """Recursively parses any strings in the JSON that may be valid JSON themselves."""
        if isinstance(obj, str):
            try:
                # Attempt to parse the string as JSON
                parsed = json.loads(obj)
                return self.recursively_parse_json(parsed)
            except (json.JSONDecodeError, TypeError):
                return obj  # Return original string if it can't be parsed
        elif isinstance(obj, list):
            return [self.recursively_parse_json(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self.recursively_parse_json(value) for key, value in obj.items()}
        else:
            return obj

    def load_json(self, filepath):
        with open(filepath, 'r') as file:
            return self.recursively_parse_json(file.read())

    def calculate_modality_percent(self, person_id_list=None):
        modality_counts = self.count_modality_choices(person_id_list)
        total_trips = sum(modality_counts.values())
        modality_proportions = {modality: (count / total_trips) * 100 for modality, count in modality_counts.items()}
        return modality_proportions

    def count_modality_choices(self, person_id_list=None):
        filtered_agents = self.agents_with_routes
        if person_id_list is not None:
            filtered_agents = SimulationResults.filter_agents_by_id(filtered_agents, person_id_list)

        means_of_transport_list = self.get_means_of_transport_list(filtered_agents)
        transport_counter = Counter(means_of_transport_list)
        return transport_counter

    def get_route_lengths_by_modalities(self):
        categories = ["<0.5 km", "0.5-1 km", "1-2 km", "2-5 km", "5-10 km", "10-20 km", "20-50 km", "50-100 km",
                      ">100 km"]
        modes = ["By foot", "Bicycle", "MIT", "Public Transport"]
        modality_mapping = SimulationResults.get_standard_mapping()

        route_lengths = {}

        for agent in self.agents_with_routes:
            for route in agent['route_descriptions']:
                modality = route['means_of_transport']
                modality = modality_mapping[modality]
                length = route['distance']
                length_category = SimulationResults.map_route_length_to_category(length)
                if route_lengths.get(modality) is None:
                    route_lengths[modality] = {category: 0 for category in categories}
                route_lengths[modality][length_category] += 1

        results = {}
        for mode in modes:
            results[mode] = []
            total_sum_of_elements = sum(route_lengths[mode].values())
            for category in categories:
                percentage = route_lengths[mode][category] / total_sum_of_elements * 100
                results[mode].append(percentage)

        return results, categories, modes

    def get_route_durations(self):
        durations = []

        for agent in self.agents_with_routes:
            for route in agent['route_descriptions']:
                duration = route['travel_time']
                duration = SimulationResults.map_duration_to_category(duration)
                durations.append(duration)

        durations = Counter(durations)

        total_trips = sum(durations.values())
        duration_proportions = {duration_label: (count / total_trips) * 100 for duration_label, count in
                                durations.items()}

        return duration_proportions

    def get_route_lengths(self):
        lengths = []

        for agent in self.agents_with_routes:
            for route in agent['route_descriptions']:
                length = route['distance']
                length = SimulationResults.map_route_length_to_category(length)
                lengths.append(length)

        lengths = Counter(lengths)

        total_trips = sum(lengths.values())
        length_proportions = {length_label: (count / total_trips) * 100 for length_label, count in lengths.items()}

        return length_proportions

    def get_route_durations_by_modalities(self):
        categories = [
            "<5 min",
            "5-10 min",
            "10-15 min",
            "15-20 min",
            "20-30 min",
            "30-45 min",
            "45-60 min",
            ">60 min"
        ]

        modes = ["By foot", "Bicycle", "MIT", "Public Transport"]
        modality_mapping = SimulationResults.get_standard_mapping()

        route_lengths = {}

        for agent in self.agents_with_routes:
            for route in agent['route_descriptions']:
                modality = route['means_of_transport']
                modality = modality_mapping[modality]
                duration = route['travel_time']
                duration = SimulationResults.map_duration_to_category(duration)
                if route_lengths.get(modality) is None:
                    route_lengths[modality] = {category: 0 for category in categories}
                route_lengths[modality][duration] += 1

        results = {}
        for mode in modes:
            results[mode] = []
            total_sum_of_elements = sum(route_lengths[mode].values())
            for category in categories:
                percentage = route_lengths[mode][category] / total_sum_of_elements * 100
                results[mode].append(percentage)

        return results, categories, modes

    def print_agents(self, agents, person_id_list=None, agents_filter=None, num_agents=10):
        filtered_agents = agents
        if person_id_list is not None:
            filtered_agents = SimulationResults.filter_agents_by_id(filtered_agents, person_id_list)
        if agents_filter is not None:
            filtered_agents = list(filter(agents_filter, filtered_agents))

        for index in range(num_agents) if num_agents < len(filtered_agents) else len(filtered_agents):
            agent = filtered_agents[index]
            SimulationResults.print_agent(agent)

    def get_possible_routes_count(self):
        modalities = ['pedestrian', 'passenger', 'bicycle', 'public transport', 'total']
        possible_routes_count_dict = {modality: 0 for modality in modalities}
        for agent in self.agents_with_routes:
            for location_change in agent['location_changes']:
                if 'possible_routes' in location_change and location_change['possible_routes']:
                    possible_routes_count_dict['total'] += 1
                    for possible_route in location_change['possible_routes']:
                        possible_routes_count_dict[possible_route['means_of_transport']] += 1
        return possible_routes_count_dict

    def get_possible_routes_upset_data(self):
        """
        Creates a DataFrame suitable for an UpSet plot where each row represents
        a location change (i.e., a candidate route) and each column (one per modality)
        indicates with a boolean whether that modality is available for that route.

        Returns:
            pd.DataFrame: A DataFrame with boolean indicators for each modality.
        """
        # Define the list of modalities you want to track.
        modalities = ['pedestrian', 'passenger', 'bicycle', 'public transport']
        rows = []

        # Iterate through all agents and their location changes.
        for agent in self.agents_with_routes:
            for location_change in agent['location_changes']:
                # Initialize a dictionary for the current location change where each modality is False by default.
                row = {modality: False for modality in modalities}
                # Check that there are any possible routes in this location change.
                if 'possible_routes' in location_change and location_change['possible_routes']:
                    # For each possible route, if the mode is one of the modalities of interest, set it to True.
                    for possible_route in location_change['possible_routes']:
                        mode = possible_route.get('means_of_transport')
                        if mode in modalities:
                            row[mode] = True
                        else:
                            print(f'unknown modality: {mode}')
                rows.append(row)

        # Convert the list of dicts into a DataFrame.
        upset_df = pd.DataFrame(rows)
        return upset_df

    def get_location_change_building_attr_values_count(self):
        building_attr_values = []
        for agent in self.agents_location_changes:
            for location_change in agent['location_changes']:
                building_attr_values.extend(location_change['from']['building']['parameters'])
                building_attr_values.extend(location_change['to']['building']['parameters'])
        return Counter(building_attr_values)

    def get_routes_building_attr_values_count(self):
        building_attr_values = []
        for agent in self.agents_with_routes:
            for location_change in agent['location_changes']:
                if 'decision' in location_change and location_change['decision']:
                    building_attr_values.extend(location_change['from']['building']['parameters'])
                    building_attr_values.extend(location_change['to']['building']['parameters'])
        return Counter(building_attr_values)

    @staticmethod
    def print_agent(agent):
        print('[AGENT] ##########')
        print(json.dumps(agent['seed'], indent=4))
        print(json.dumps(agent['description'], indent=4))
        print(json.dumps(agent['day_schedule'], indent=4))
        for route in agent['route_descriptions'] or []:
            route['route'] = None
        print(json.dumps(agent['route_descriptions'], indent=4))

    @staticmethod
    def map_duration_to_category(duration_seconds):
        duration_min = duration_seconds / 60

        duration_categories = [
            (0, 5, "<5 min"),
            (5, 10, "5-10 min"),
            (10, 15, "10-15 min"),
            (15, 20, "15-20 min"),
            (20, 30, "20-30 min"),
            (30, 45, "30-45 min"),
            (45, 60, "45-60 min"),
            (60, float("inf"), ">60 min")
        ]

        for min_start, min_end, category in duration_categories:
            if min_start <= duration_min < min_end:
                return category

        return "implausible value"

    @staticmethod
    def map_route_length_to_category(length_meters):
        if length_meters < 0:
            return "unplausible value"
        elif length_meters < 500:
            return "<0.5 km"
        elif length_meters < 1000:
            return "0.5-1 km"
        elif length_meters < 2000:
            return "1-2 km"
        elif length_meters < 5000:
            return "2-5 km"
        elif length_meters < 10000:
            return "5-10 km"
        elif length_meters < 20000:
            return "10-20 km"
        elif length_meters < 50000:
            return "20-50 km"
        elif length_meters < 100000:
            return "50-100 km"
        else:
            return ">100 km"

    @staticmethod
    def get_means_of_transport_list(agents_with_routes):
        return [
            route['means_of_transport']
            for agent in agents_with_routes
            for route in agent['route_descriptions']
        ]

    @staticmethod
    def filter_agents_by_id(agents, person_id_list):
        filtered_agents = [agent for agent in agents if
                           int(agent['seed']['additional_data']['Haushalts-Personen-ID']) in person_id_list]
        return filtered_agents

    def count_possible_routes(self):
        modalities = ['pedestrian', 'passenger', 'bicycle', 'public transport', 'total']
        possible_routes_count_dict = {modality: 0 for modality in modalities}
        for agent in self.agents_with_routes:
            for location_change in agent['location_changes']:
                if 'possible_routes' in location_change and location_change['possible_routes']:
                    possible_routes_count_dict['total'] += 1
                    for possible_route in location_change['possible_routes']:
                        possible_routes_count_dict[possible_route['means_of_transport']] += 1
        return possible_routes_count_dict

    @staticmethod
    def get_standard_mapping():
        return {
            "pedestrian": "By foot",
            "passenger": "MIT",
            "bicycle": "Bicycle",
            "public transport": "Public Transport",
        }

    @staticmethod
    def standardize_keys(modality_split):
        standard_mapping = SimulationResults.get_standard_mapping()
        standard_dict = {}
        for key, value in modality_split.items():
            new_key = standard_mapping.get(key, None)
            if new_key is not None:
                standard_dict[new_key] = value
            else:
                raise KeyError(f'{key} is not a valid key')
        return standard_dict
