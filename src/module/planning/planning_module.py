from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple

from module.action.action_module import ActionModule
from llm.huggingface_chat_api import HuggingfaceChatAPI
from model.agent import Agent
from model.day_schedule import DaySchedule
from model.location_change import LocationChange
from model.task import Task
from module.planning.prompt.day_schedules import get_day_schedule_with_places_prompt
from module.planning.prompt.means_of_transport_selection import get_select_means_of_transport_prompt, map_string_to_means_of_transport
from util.json import extract_json_from
from util.list import split_list
from util.logging import log_error, log_debug
from util.time import time_to_seconds


class PlanningModule:
    @staticmethod
    def generate_day_schedules_with_places_multithreaded(agents, building_options, max_workers, day):
        agents_per_worker = split_list(agents, max_workers)

        result_agents = []
        skipped_agents = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for worker_id in range(max_workers):
                future = executor.submit(
                    PlanningModule.generate_day_schedules_with_places,
                    agents_per_worker[worker_id],
                    building_options,
                    worker_id,
                    day
                )
                futures.append(future)
            for future in as_completed(futures):
                try:
                    agents_with_day_schedule, agents_without_day_schedule = future.result()
                    result_agents.extend(agents_with_day_schedule)
                    skipped_agents.extend(agents_without_day_schedule)
                except Exception as e:
                    log_error(e)
                    log_error(f'[ERROR] Failed to execute task {future}')

        return result_agents, skipped_agents

    @staticmethod
    def generate_day_schedules_with_places(agents, building_options, worker_id, day):
        llm_api = HuggingfaceChatAPI(gpu_id=worker_id)

        prompts = [get_day_schedule_with_places_prompt(building_options, agent.description, day)
                   for agent in agents]
        responses = llm_api.get_completions(prompts)

        agents_with_day_schedule = []
        agents_without_day_schedule = []
        for agent, response in zip(agents, responses):
            try:
                day_schedule_data = extract_json_from(response)['description_of_today']
                agent.day_schedule = DaySchedule.from_json({
                    'day': day,
                    'task_list': day_schedule_data
                })
                agents_with_day_schedule.append(agent)
            except Exception as e:
                log_error(e)
                log_error(f'[ERROR] Failed to generate day schedule for {agent.to_json()}')
                log_error(f'[ERROR] Response:\n{response}')
                agents_without_day_schedule.append(agent)

        return agents_with_day_schedule, agents_without_day_schedule

    @staticmethod
    def extend_with_location_changes_multithreaded(agents: List[Agent],
                                                   max_workers,
                                                   traffic_sim) -> (List[Agent], List[Agent]):
        agents_per_worker = split_list(agents, max_workers)

        agents = []
        skipped_agents = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for worker_id in range(max_workers):
                future = executor.submit(PlanningModule.extend_with_location_changes,
                                         agents_per_worker[worker_id],
                                         traffic_sim)
                futures.append(future)
            for future in as_completed(futures):
                try:
                    agents_with_location_changes, agents_without_location_changes = future.result()
                    agents.extend(agents_with_location_changes)
                    skipped_agents.extend(agents_without_location_changes)
                except Exception as e:
                    log_error(e)

        return agents, skipped_agents

    @staticmethod
    def extend_with_location_changes(agents: List[Agent], traffic_sim) -> (List[Agent], List[Agent]):
        agents_with_location_changes = []
        agents_without_location_changes = []

        for agent in agents:
            location_changes = PlanningModule.get_planned_location_changes(agent, traffic_sim)
            agent.location_changes = location_changes
            if agent.location_changes:
                agents_with_location_changes.append(agent)
            else:
                agents_without_location_changes.append(agent)

        return agents_with_location_changes, agents_without_location_changes

    @staticmethod
    def get_planned_location_changes(agent: Agent, traffic_sim) -> List[LocationChange]:
        agent.home = traffic_sim.get_random_apartment()
        reference_location = agent.home.location
        tasks = agent.day_schedule.task_list

        building_types = set(task.building_type for task in tasks)
        buildings = {}
        for building_type in building_types:
            try:
                building = ActionModule.get_building_with(agent, building_type, traffic_sim,
                                                          reference_location=reference_location)
                buildings[building_type] = building
                reference_location = building.location
            except Exception as e:
                log_error(e)

        location_change_task_tuples = PlanningModule.get_tasks_with_location_change(tasks)
        location_changes = []
        for index, task_tuple in enumerate(location_change_task_tuples):
            try:
                route_id = ActionModule.generate_route_id(agent.id, index)
                from_task = task_tuple[0]
                from_building = buildings[from_task.building_type]
                to_task = task_tuple[1]
                to_building = buildings[to_task.building_type]

                if from_building.location == to_building.location:
                    raise Exception('Locations of both from and to building are the same!')

                location_change = LocationChange(
                    route_id=route_id,
                    from_task=from_task,
                    from_building=from_building,
                    to_task=to_task,
                    to_building=to_building
                )
                location_changes.append(location_change)
            except Exception as e:
                log_error(e)
        return location_changes

    @staticmethod
    def get_tasks_with_location_change(tasks: List[Task]) -> List[Tuple[Task, Task]]:
        location_change_tasks = []
        for i in range(len(tasks) - 1):
            if tasks[i].building_type != tasks[i + 1].building_type:
                location_change_tasks.append((tasks[i], tasks[i + 1]))
        return location_change_tasks

    @staticmethod
    def add_routes_multithreaded(agents: List[Agent], max_workers, traffic_sim, actually_add_route_to_sim=False,
                                 use_geocoord=False) -> List[Agent]:
        agents_per_worker = split_list(agents, max_workers)

        agents = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for worker_id in range(max_workers):
                future = executor.submit(PlanningModule.add_routes,
                                         agents_per_worker[worker_id],
                                         worker_id,
                                         traffic_sim,
                                         actually_add_route_to_sim,
                                         use_geocoord)
                futures.append(future)
            for future in as_completed(futures):
                try:
                    agents_with_routes = future.result()
                    agents.extend(agents_with_routes)
                except Exception as e:
                    log_error(e)

        return agents

    @staticmethod
    def add_routes(agents: List[Agent], worker_id, traffic_sim, actually_add_route_to_sim=False, use_geocoord=False) -> \
            List[Agent]:
        try:
            llm_api = HuggingfaceChatAPI(gpu_id=worker_id)
            agents = ActionModule.get_possible_routes_for_agents(agents, traffic_sim, use_geocoord=use_geocoord)
            agents = PlanningModule.get_route_decisions(agents, llm_api)
            agents = PlanningModule.set_sim_routes(agents, traffic_sim, actually_add_route_to_sim)
            return agents
        except Exception as e:
            log_error(e)

    @staticmethod
    def get_route_decisions(agents: List[Agent], llm_api) -> List[Agent]:
        prompts = [get_select_means_of_transport_prompt(agent) for agent in agents]
        if not prompts:
            raise Exception('No routes available')
        results = llm_api.get_completions(prompts)

        for agent, result, prompt in zip(agents, results, prompts):
            log_debug(f'[ROUTE_DECISIONS][PROMPT]{prompt}')
            log_debug(f'[ROUTE_DECISIONS][RESPONSE]{result}')
            try:
                decisions = extract_json_from(result)['decisions']
                decision_map = {decision['route_id']: decision for decision in decisions if 'route_id' in decision}
                for location_change in agent.location_changes:
                    if location_change.possible_routes:
                        route_id = str(location_change.route_id)
                        if route_id not in decision_map:
                            raise Exception(f'No decision found for route_id: {route_id}')
                        location_change.decision = decision_map[route_id]
                        location_change.decision['means_of_transport'] = map_string_to_means_of_transport(
                            location_change.decision['means_of_transport'])
            except Exception as e:
                log_error(f'Error: {e}\n\nNo decision found found for result:\n{result}')
        return agents

    @staticmethod
    def set_sim_routes(agents: List[Agent], traffic_sim, actually_add_route_to_sim=False) -> List[Agent]:
        for agent in agents:
            routes = []
            for location_change in agent.location_changes:
                if location_change.decision:
                    try:
                        decision = location_change.decision
                        possible_routes = location_change.possible_routes
                        means_of_transport = decision['means_of_transport']
                        possible_route = next((route for route in possible_routes
                                               if route.means_of_transport == means_of_transport), None)
                        if possible_route:
                            route = possible_route.to_dict()
                            route['route_id'] = decision['route_id']
                            route['departure_time'] = time_to_seconds(location_change.to_task.time) - route[
                                'travel_time']
                            if route['departure_time'] < 0:
                                route['departure_time'] = 0
                            if actually_add_route_to_sim:
                                route = traffic_sim.add_traffic_participant(route)
                            routes.append(route)
                    except Exception as e:
                        log_error(f'{e}\n\n{route if route else None}')
            agent.route_descriptions = routes
        return agents
