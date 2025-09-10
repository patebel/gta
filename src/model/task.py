class Task:
    def __init__(self, time, action, building_type):
        self.time = time
        self.action = action
        self.building_type = building_type

    def to_dict(self):
        return {
            "time": self.time,
            "action": self.action,
            "building_type": self.building_type,
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            time=data["time"],
            action=data["action"],
            building_type=data.get("building_type", None)
        )
