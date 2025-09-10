import libsumo as traci


def start_sim(net_file, poly_file, v_types_file, pt_stops_file, pt_vehicles_file):
    additional_files = [poly_file, v_types_file, pt_stops_file]
    additional_files = ','.join(filter(None, additional_files))
    traci.start(
        [
            'sumo',
            '--net-file', net_file,
            '--additional-files', additional_files,
            '--route-files', pt_vehicles_file,
            '--ignore-route-errors', "true",
            '--time-to-teleport', '20'
        ])


def get_num_expected_vehicles():
    return traci.simulation.getMinExpectedNumber()


def simulation_step():
    traci.simulationStep()


def stop_sim():
    traci.close()


def get_polygons_with_parameters(parameters):
    polygon_ids = get_polygon_ids()
    polygon_parameters_list = []
    for polygon_id in polygon_ids:
        polygon_parameters = {'polygon_id': polygon_id, 'parameters': []}
        has_at_least_one_parameter = False
        for parameter in parameters:
            key, value = traci.polygon.getParameterWithKey(polygon_id, parameter)
            if value != '':
                has_at_least_one_parameter = True
            polygon_parameters['parameters'].append({key: value})
        if has_at_least_one_parameter:
            polygon_parameters_list.append(polygon_parameters)
    return polygon_parameters_list


def get_polygons_with_parameter(parameter):
    polygon_ids = get_polygon_ids()
    polygons_with_parameter = []
    for polygon_id in polygon_ids:
        key, value = traci.polygon.getParameterWithKey(polygon_id, parameter)
        if value != '':
            polygon_with_parameter = {'polygon_id': polygon_id, key: value}
            polygons_with_parameter.append(polygon_with_parameter)
    return polygons_with_parameter


def get_polygon_ids():
    return traci.polygon.getIDList()


def get_polygon_position(polygon_id):
    return get_polygon_shape(polygon_id)[0]


def get_geo_coordinates(cart_coordinates):
    lon_lat = traci.simulation.convertGeo(cart_coordinates[0], cart_coordinates[1])
    # We want lat and then lon and not the other way round
    return [lon_lat[1], lon_lat[0]]


def get_cart_coordinates(lon, lat):
    lon_lat = traci.simulation.convertGeo(lon, lat, fromGeo=True)
    return [lon_lat[0], lon_lat[1]]


def get_polygon_shape(polygon_id):
    return traci.polygon.getShape(polygon_id)


def find_route(start_position, end_position, v_class='passenger', v_type='DEFAULT_VEHTYPE'):
    from_edge = get_road_edge(start_position, v_class)
    to_edge = get_road_edge(end_position, v_class)
    return traci.simulation.findRoute(from_edge, to_edge, vType=v_type)


def get_road_edge(start_position, v_class):
    from_edge, _, _ = traci.simulation.convertRoad(start_position[0], start_position[1], vClass=v_class)
    return from_edge


def find_intermodal_route(start_position, end_position, arrival_time):
    from_edge = get_road_edge(start_position, 'pedestrian')
    to_edge = get_road_edge(end_position, 'pedestrian')
    route_estimation = find_intermodal_route_from_edges(from_edge, to_edge, arrival_time)
    estimated_travel_time = sum(stage.travelTime for stage in route_estimation)
    departure_time = arrival_time - estimated_travel_time
    return find_intermodal_route_from_edges(from_edge, to_edge, departure_time)


def find_intermodal_route_from_edges(from_edge, to_edge, departure_time):
    modes = 'public'
    return traci.simulation.findIntermodalRoute(from_edge, to_edge, modes, depart=departure_time)


def add_car(route):
    route_id = route['route_id']
    edges = route['route']
    departure_time = route['departure_time']
    if edges:
        add_route(route_id, edges)
        add_vehicle(route_id, route_id, departure_time, 'DEFAULT_VEHTYPE')
        return route
    else:
        raise Exception('No vehicle route found')


def add_bicycle(route):
    route_id = route['route_id']
    edges = route['route']
    departure_time = route['departure_time']
    if edges:
        add_route(route_id, edges)
        add_vehicle(route_id, route_id, departure_time, 'DEFAULT_BIKETYPE')
        return route
    else:
        raise Exception('No vehicle route found')


def add_vehicle(veh_id, route_id, departure_time, vehicle_type):
    traci.vehicle.add(str(veh_id), str(route_id), depart=departure_time, typeID=vehicle_type)


def add_route(route_id, edges, v_class='passenger'):
    traci.route.add(str(route_id), edges)


def add_pedestrian(route, type_id="DEFAULT_PEDTYPE"):
    route_id = route['route_id']
    edges = route['route']
    departure_time = route['departure_time']
    from_edge = edges[0]

    traci.person.add(route_id, from_edge, 0, departure_time, typeID=type_id)
    traci.person.appendWalkingStage(route_id, edges, arrivalPos=1.0)
    return route


def add_intermodal(route):
    route_id = route['route_id']
    stages = route['route']
    from_edge = stages[0]
    to_edge = stages[1]
    departure_time = route['departure_time']

    stages = find_intermodal_route_from_edges(from_edge, to_edge, departure_time)

    type_id = "DEFAULT_PEDTYPE"
    traci.person.add(route_id, from_edge, 0, departure_time, typeID=type_id)
    for stage in stages:
        traci.person.appendStage(route_id, stage)
    return route


def edge_near(position, v_class):
    from_edge, _, _ = traci.simulation.convertRoad(position[0], position[1], vClass=v_class)
    return from_edge
