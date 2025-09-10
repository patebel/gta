from module.action.closest_location_choice import ClosestLocationChoice
from module.action.sumo.sumo_adapter import SumoAdapter
from config.config import config_berlin_sumo as config
from module.planning.planning_module import PlanningModule
from module.profile.profile_module import ProfileModule
from module.profile.seed.mid_b1_seed_generator import SeedGeneratorMiD
from util.logging import log_info
from util.storage import Storage
from util.time import Timer
from util.trips import generate_trips_xml

log_info("Starting traffic simulacra")
timer = Timer()
timer.start()

log_info('Initialising parameter, necessary objects...')
log_info(f'Config used:\n{config}')
day = config['day']

max_workers = config['workers']
num_agents = config['num_agents']

load_from_storage = config['load_from_storage']
storage_path = config['storage_path']

census_file = config['census_file']
net_file = config['net_file']
poly_file = config['poly_file']
v_types_file = config['v_types_file']
pt_stops_file = config['pt_stops_file']
pt_vehicles_file = config['pt_vehicles_file']

exclude_too_young = config['exclude_too_young']
exclude_too_old = config['exclude_too_old']

buildings_file = config['buildings_file']
taz_file = config['taz_file']

storage = Storage(storage_path, load_from_storage)
urban_sampler = ClosestLocationChoice(buildings_file, taz_file)
traffic_sim = SumoAdapter(urban_sampler, net_file, poly_file, v_types_file, pt_stops_file, pt_vehicles_file)
seed_generator = SeedGeneratorMiD(census_file)

log_info('Initialising agents and enriching them with descriptions...')
final_agents = ProfileModule.generate_seeded_agents(seed_generator, num_agents)
final_agents, agents_without_description = ProfileModule.generate_descriptions_multithreaded(final_agents,
                                                                                             max_workers,
                                                                                             exclude_too_young,
                                                                                             exclude_too_old)

storage.write_agents(final_agents, '1_description')
storage.write_agents(agents_without_description, '1_no_description')
log_info(f'[DESCRIPTION] {len(final_agents)} described agents.')
log_info(f'[DESCRIPTION] {len(agents_without_description)} agents without description.')
agents_without_description = None

log_info('Adding day schedules with the respective places to the agents...')
building_options = traffic_sim.get_building_categories_string()
final_agents, agents_without_day_schedule = PlanningModule.generate_day_schedules_with_places_multithreaded(
    final_agents,
    building_options,
    max_workers,
    day)

storage.write_agents(final_agents, '2_day_schedule')
storage.write_agents(agents_without_day_schedule, '2_no_day_schedule')
log_info(f'[DAY_SCHEDULE] {len(final_agents)} agents with day schedule.')
log_info(f'[DAY_SCHEDULE] {len(agents_without_day_schedule)} agents without day schedule.')
agents_without_day_schedule = None

log_info('Extracting location changes of agents...')
final_agents, agents_without_location_changes = PlanningModule.extend_with_location_changes_multithreaded(
    final_agents, max_workers, traffic_sim)

storage.write_agents(final_agents, '3_location_changes')
storage.write_agents(agents_without_location_changes, '3_no_location_changes')
log_info(f'[LOCATION_CHANGES] {len(final_agents)} agents with location changes.')
log_info(f'[LOCATION_CHANGES] {len(agents_without_location_changes)} agents without location changes.')
agents_without_location_changes = None

log_info('Adding routes...')
final_agents = PlanningModule.add_routes_multithreaded(final_agents, max_workers, traffic_sim)

storage.write_agents(final_agents, '4_route_descriptions')
created_route_description_count = sum(len(agent.route_descriptions) for agent in final_agents)
total_route_descriptions_count = sum(sum(1 for index in range(len(agent.day_schedule.task_list) - 1) if
                                         agent.day_schedule.task_list[index].building_type !=
                                         agent.day_schedule.task_list[index + 1].building_type) for agent in
                                     final_agents)
log_info(f'[ROUTES] {created_route_description_count}/{total_route_descriptions_count} routes created.')
log_info(f'[ROUTES] {len(final_agents)} final agents.')

log_info('Extracting trips.xml...')
route_descriptions = [route_description for agent in final_agents for route_description in agent.route_descriptions]
trips_xml = generate_trips_xml(route_descriptions)
storage.write_trips(trips_xml)

log_info(f'[TIME] Total runtime: {timer.stop()}.')

traffic_sim.stop_sim()
log_info('Finished traffic simulation.')
