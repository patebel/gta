import json

from model.agent import Agent
from util.file import write_file, read_file, remove_files_in, create_folders


class Storage:
    def __init__(self, storage_path, load_from_storage=False):
        self.storage_path = storage_path
        if not load_from_storage:
            remove_files_in(self.storage_path)

        create_folders(self.storage_path)

        self.trips_xml_path = f'{storage_path}/trips.xml'

        self.agents_file = 'agents.json'

    def write_agents(self, agents, postfix):
        agents_str = json.dumps([agent.to_json() for agent in agents])
        agents_file_path = f'{self.storage_path}/agents_{postfix}.json'
        write_file(agents_file_path, agents_str)
        return agents_file_path

    def get_agents(self, agents_file_path):
        agents_json = read_file(agents_file_path)

        agents_data = json.loads(agents_json)

        return [Agent.from_json(agent_data) for agent_data in agents_data]

    def write_trips(self, trips_xml):
        write_file(self.trips_xml_path, trips_xml)
