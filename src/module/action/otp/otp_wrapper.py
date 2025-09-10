from datetime import datetime, timedelta, timezone

import requests

from util.logging import log_error


class OTPWrapper:
    def __init__(self, otp_endpoint="http://paula01.sc.uni-leipzig.de:8080/otp/gtfs/v1", date=None):
        self.otp_endpoint = otp_endpoint
        self.date = date

    def query_otp(self, from_location, to_location, modes, arrival_time=None):
        query = """
        query($fromLat: Float!, $fromLon: Float!, $toLat: Float!, $toLon: Float!, $transportModes: [TransportMode!]!, $arrivalTime: String) {
          plan(from: { lat: $fromLat, lon: $fromLon }, 
               to: { lat: $toLat, lon: $toLon },
               transportModes: $transportModes,
               date: $arrivalTime) {
            itineraries {
              duration
              legs {
                mode
                distance
                from {
                  name
                }
                to {
                  name
                }
                legGeometry {
                  points
                }
              }
            }
          }
        }
        """
        # Prepare variables
        transport_modes = [{"mode": mode} for mode in modes]
        variables = {
            "fromLat": from_location[1],
            "fromLon": from_location[0],
            "toLat": to_location[1],
            "toLon": to_location[0],
            "transportModes": transport_modes,
        }

        if arrival_time:
            if self.date:
                arrival_time = datetime.combine(self.date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(
                    seconds=arrival_time)
            arrival_time = arrival_time.isoformat()
            variables["arrivalTime"] = arrival_time

        # Send the request
        response = requests.post(
            self.otp_endpoint,
            json={"query": query, "variables": variables},
        )
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            raise ValueError(f"GraphQL query error: {data['errors']}")
        return data["data"]["plan"]["itineraries"]

    def get_passenger_route(self, from_location, to_location):
        modes = ["CAR"]
        itineraries = self.query_otp(from_location, to_location, modes)
        try:
            return self.format_shortest_route_response(itineraries)
        except ValueError:
            log_error(f'Modes: {modes}, from_location: {from_location}, to_location: {to_location}')
        return {}

    def get_pedestrian_route(self, from_location, to_location):
        modes = ["WALK"]
        itineraries = self.query_otp(from_location, to_location, modes)
        try:
            return self.format_shortest_route_response(itineraries)
        except ValueError:
            log_error(f'Modes: {modes}, from_location: {from_location}, to_location: {to_location}')
        return {}

    def get_bicycle_route(self, from_location, to_location):
        modes = ["BICYCLE"]
        itineraries = self.query_otp(from_location, to_location, modes)
        try:
            return self.format_shortest_route_response(itineraries)
        except ValueError:
            log_error(f'Modes: {modes}, from_location: {from_location}, to_location: {to_location}')
        return {}

    def get_intermodal_route(self, from_location, to_location, arrival_time):
        modes = ["TRANSIT"]
        itineraries = self.query_otp(from_location, to_location, modes, arrival_time)
        try:
            return self.format_shortest_route_response(itineraries)
        except ValueError:
            log_error(f'Modes: {modes}, from_location: {from_location}, to_location: {to_location}')
        return {}

    def format_shortest_route_response(self, itineraries):
        if not itineraries:
            raise ValueError("No itineraries found. OTP did not return any valid routes.")
        formatted_route = {}
        min_duration = min([itinerary["duration"] for itinerary in itineraries])
        for itinerary in itineraries:
            duration = itinerary["duration"]
            if duration == min_duration:
                distance = sum(leg["distance"] for leg in itinerary["legs"])
                description = " -> ".join(
                    f"{leg['mode']} from {leg['from']['name']} to {leg['to']['name']}"
                    for leg in itinerary["legs"]
                )
                formatted_route = {
                    "duration": duration,
                    "distance": distance,
                    "description": description,
                }
        return formatted_route
