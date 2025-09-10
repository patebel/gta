from model.building import Building
from model.possible_route import PossibleRoute
from model.task import Task


class LocationChange:
    def __init__(self, route_id, from_task, from_building, to_task, to_building, decision=None, possible_routes=None):
        self.route_id = route_id
        self.from_task = from_task
        self.from_building = from_building
        self.to_task = to_task
        self.to_building = to_building
        self.decision = decision
        self.possible_routes = [PossibleRoute.from_dict(route) for route in
                                possible_routes] if possible_routes else None

    def to_dict(self):
        return {
            "route_id": self.route_id,
            "from": {
                "task": self.from_task.to_dict(),
                "building": self.from_building.to_dict(),
            },
            "to": {
                "task": self.to_task.to_dict(),
                "building": self.to_building.to_dict(),
            },
            "decision": self.decision,
            "possible_routes": [route.to_dict() for route in self.possible_routes] if self.possible_routes else None
        }

    @classmethod
    def from_json(cls, data):
        from_task = Task.from_json(data["from"]["task"])
        from_building = Building.from_json(data["from"]["building"])
        to_task = Task.from_json(data["to"]["task"])
        to_building = Building.from_json(data["to"]["building"])
        decision = data.get("decision")
        possible_routes = data.get("possible_routes")
        return cls(
            route_id=data["route_id"],
            from_task=from_task,
            from_building=from_building,
            to_task=to_task,
            to_building=to_building,
            decision=decision,
            possible_routes=possible_routes
        )
