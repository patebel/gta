from concurrent.futures import ProcessPoolExecutor, as_completed

from llm.huggingface_chat_api import HuggingfaceChatAPI
from model.agent import Agent
from module.profile.prompt.description import get_description_prompt
from util.json import extract_json_from
from util.list import split_list
from util.logging import log_error


class ProfileModule:
    @staticmethod
    def generate_seeded_agents(seed_generator, num_agents):
        agents = []
        seeds = seed_generator.generate_seeds(num_agents)
        for count, seed in enumerate(seeds):
            agent = Agent(count)
            agent.seed = seed
            agents.append(agent)
        return agents

    @staticmethod
    def generate_descriptions_multithreaded(agents, max_workers, exclude_too_young, exclude_too_old):
        agents_per_worker = split_list(agents, max_workers)

        result_agents = []
        agents_without_description = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for worker_id in range(max_workers):
                future = executor.submit(
                    ProfileModule.generate_descriptions,
                    agents_per_worker[worker_id],
                    worker_id,
                    exclude_too_young,
                    exclude_too_old
                )
                futures.append(future)
            for future in as_completed(futures):
                try:
                    described_agents, skipped_agents = future.result()
                    result_agents.extend(described_agents)
                    agents_without_description.extend(skipped_agents)
                except Exception as e:
                    log_error(e)
                    log_error(f'[ERROR] Failed to execute task {future}')

        return result_agents, agents_without_description

    @staticmethod
    def generate_descriptions(agents, worker_id, exclude_too_young=True, exclude_too_old=True):
        llm_api = HuggingfaceChatAPI(gpu_id=worker_id)

        agents_to_be_described = []
        skipped_agents = []
        for agent in agents:
            if exclude_too_young and agent.seed.too_young():
                skipped_agents.append(agent)
            elif exclude_too_old and agent.seed.too_old():
                skipped_agents.append(agent)
            else:
                agents_to_be_described.append(agent)

        prompts = [get_description_prompt(agent.seed) for agent in agents_to_be_described]
        responses = llm_api.get_completions(prompts)

        for agent, response in zip(agents_to_be_described, responses):
            try:
                description = extract_json_from(response)['persona_description']
                agent.description = description
            except Exception as e:
                log_error(e)
                log_error(f'[ERROR] Failed to extract description from {agent}')
                agents_to_be_described.remove(agent)
                skipped_agents.append(agent)

        return agents_to_be_described, skipped_agents
