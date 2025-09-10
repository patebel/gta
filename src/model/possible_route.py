from util.time import seconds_to_hhmm


class PossibleRoute:
    def __init__(self, means_of_transport, route, travel_time, distance=None):
        self.means_of_transport = means_of_transport
        self.route = route
        self.travel_time = travel_time
        self.distance = distance

    def to_dict(self):
        return {
            "means_of_transport": self.means_of_transport,
            "route": self.route,
            "travel_time": self.travel_time,
            "distance": self.distance
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            means_of_transport=data["means_of_transport"],
            route=data["route"],
            travel_time=data["travel_time"],
            distance=data.get("distance")
        )

    def travel_time_in_hhmm(self):
        return seconds_to_hhmm(self.travel_time)

    def distance_in_km(self):
        if self.distance is None:
            return None
        distance = round(int(self.distance) / 1000, 2)
        return f'{distance}km'
