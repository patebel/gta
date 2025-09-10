def generate_trips_xml(route_descriptions):
    route_descriptions.sort(key=lambda x: x['departure_time'])
    trips_xml = ('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
    for route_description in route_descriptions:
        route_xml = convert_to_trip_xml(route_description)
        if route_xml is not None:
            trips_xml += route_xml
    trips_xml += '</routes>\n'
    return trips_xml


def convert_to_trip_xml(route_description):
    trip_id = route_description['route_id']
    departure_time = route_description['departure_time']
    transportation = route_description['means_of_transport']
    from_edge = route_description['route'][0]
    to_edge = route_description['route'][-1]

    if from_edge != to_edge:
        if transportation == 'passenger':
            trip = f'\t<trip id="{trip_id}" depart="{departure_time}" from="{from_edge}" to="{to_edge}" />\n'
            return trip
        elif transportation == 'pedestrian':
            trip = (f'\t<person id="{trip_id}" depart="{departure_time}" departPos="random">\n'
                    f'\t\t<walk from="{from_edge}" to="{to_edge}" arrivalPos="random"/>\n'
                    f'\t</person>\n')
            return trip
        elif transportation == 'bicycle':
            trip = f'\t<trip id="{trip_id}" type="DEFAULT_BIKETYPE" depart="{departure_time}" from="{from_edge}" to="{to_edge}" />\n'
            return trip
        elif transportation == 'public transport':
            modes = 'public'
            trip = (f'\t<person id="{trip_id}" depart="{departure_time}">\n'
                    f'\t\t<personTrip from="{from_edge}" to="{to_edge}" modes="{modes}"/>\n'
                    f'\t</person>\n')
            return trip
        else:
            raise NotImplementedError(f'Transportation type "{transportation}" not implemented')
