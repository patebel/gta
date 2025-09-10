from module.action.otp.sumo_otp_adapter import SumoOTPAdapter
from config.config import config_berlin_sumo as config
from module.planning.planning_module import PlanningModule
from util.logging import log_info
from util.storage import Storage
from util.time import Timer

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

storage = Storage(storage_path, load_from_storage)
otp_api_url = 'http://paula01.sc.uni-leipzig.de:8080/otp/gtfs/v1'
traffic_sim = SumoOTPAdapter(net_file, poly_file, v_types_file, pt_stops_file, pt_vehicles_file, otp_api_url)

log_info("Loading agents from storage...")
agents_path = 'results/baseline-monday-wedding-sumo/agents_3_location_changes.json'
agents = storage.get_agents(agents_path)
log_info('Loaded agents from storage...')

log_info('Adding routes...')
agents = PlanningModule.add_routes_multithreaded(agents, max_workers, traffic_sim, use_geocoord=True)
storage.write_agents(agents, '4_route_descriptions')
created_route_description_count = sum(len(agent.route_descriptions) for agent in agents)
total_route_descriptions_count = sum(sum(1 for index in range(len(agent.day_schedule.task_list) - 1) if
                                         agent.day_schedule.task_list[index].building_type !=
                                         agent.day_schedule.task_list[index + 1].building_type) for agent in agents)
log_info(f'[ROUTES] {created_route_description_count}/{total_route_descriptions_count} routes created.')
log_info(f'[ROUTES] {len(agents)} final agents.')

log_info(f'[TIME] Total runtime: {timer.stop()}.')
traffic_sim.stop_sim()
log_info('Finished traffic simulation.')
