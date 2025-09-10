import json

from model.agent import Agent


def map_means_of_transport_to_string(means_of_transport):
    mapping = {
        "passenger": "car",
        "pedestrian": "walk",
        "bicycle": "bicycle",
        "public transport": "public transport",
    }
    return mapping.get(means_of_transport, means_of_transport)


def map_string_to_means_of_transport(means_of_transport):
    mapping = {
        "car": "passenger",
        "walk": "pedestrian",
        "bicycle": "bicycle",
        "public transport": "public transport",
    }
    return mapping.get(means_of_transport, means_of_transport)


def get_select_means_of_transport_prompt(agent: Agent) -> str:
    few_shot = r"""
You live in Berlin and have several tasks to complete today , for which you need to plan
several trips . Berliners typically
- walk for very short trips ( <1 km ) ,
- bike for medium trips (1 -5 km ) ,
- use public transport for longer trips ( >5 km ) ,
- and drive only if they have a car immediately available .
The eight examples below are * shuffled *, but together they reflect a typical Berlin modal
split (2 walk , 1 bicycle , 3 car , 2 public transport ):
1. 0.3 km in 5 min -> ** walk ** ("300 m is fastest on foot ")
2. 4.0 km in 10 min -> ** car ** (" fastest for a 4 km morning commute ")
3. 8.0 km in 20 min -> ** public transportation ** (" subway is most reliable ")
4. 1.5 km in 7 min -> ** bicycle ** (" Berlin 's bike paths make this ideal ")
5. 0.7 km in 10 min ( with groceries ) -> ** walk ** (" easiest to carry bags ")
6. 5.0 km in 15 min -> ** public transportation ** (" smooth transfer on S - Bahn ")
7. 3.0 km in 12 min ( rainy ) -> ** car ** (" stay dry and faster than cycling ")
8. 12.0 km in 30 min -> ** car ** (" direct suburban route is best by car ")
"""

    route_choices = [
        {
            'route_id': location_change.route_id,
            'from_task': location_change.from_task.to_dict(),
            'to_task': location_change.to_task.to_dict(),
            'possible_routes': [
                {
                    'means_of_transport': map_means_of_transport_to_string(possible_route.means_of_transport),
                    'travel_time_hh_mm': possible_route.travel_time_in_hhmm(),
                    **({'distance': possible_route.distance_in_km()} if possible_route.distance is not None else {}),
                }
                for possible_route in location_change.possible_routes
            ],
        }
        for location_change in agent.location_changes
        if location_change.possible_routes
    ]
    route_choices_str = json.dumps(route_choices, indent=4)

    json_template = ",".join(
        f'{{"route_id":"{lc.route_id}","reasoning":"a one sentence reasoning for your decision","means_of_transport":"<car/walk/bicycle/public transport>"}}'
        for lc in agent.location_changes
        if lc.possible_routes
    )

    prompt = (
        f"You are:\n{agent.description}\n\n"
        f"{few_shot}\n"
        f"Your route options are:\n{route_choices_str}\n\n"
        f"For each leg, write one personal sentence explaining your choice, then pick the mode. Only switch modes if you’d logically have that vehicle with you.\n\n"
        f"Return exactly one compact JSON, no line breaks:\n"
        f"{{\"decisions\":[{json_template}]}}\n\n"
        f"Now, your JSON response:"
    )

    return prompt.strip()
