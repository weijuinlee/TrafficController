import requests
import time
import json
import math
import random
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans

broker_address="18.140.162.221"
client = mqtt.Client("TrafficController") 
client.connect(broker_address)
all_robots_current_coordinates = {}
all_robots_current_vertice = {}
robots_planned_route = {}
current_node_used = []
complete_from_robot_id = None

def get_list_of_vertices(input_data, patrol_route):

    graph_ID = input_data['graphID']
    URL = "https://go-pq.herokuapp.com/editor/graph/detailed/%s"%graph_ID
    r = requests.get(url = URL)
    graph_data = r.json()
    list_of_verticies = []
    vertices = graph_data['vertices']

    for waypoint in patrol_route:

        vertice = vertices.get(waypoint)
        x_coordinate = vertice.get('x')
        y_coordinate = vertice.get('y')
        list_of_verticies.append([x_coordinate,y_coordinate])

    return list_of_verticies

def create_list_of_robots(input_data):

    list_of_robots = []

    for robot in input_data['robots']:

        list_of_robots.append(robot['robotID'])

    return list_of_robots

def get_patrol_route(input_data):

    patrol_ID = input_data['patrolID']
    graph_ID = input_data['graphID']
    URL = "https://go-patrol.herokuapp.com/editor/patrol"
    r = requests.get(url = URL)
    graph_data = r.json()
    searched_patrol = next((item for item in graph_data if item.get("id") == patrol_ID and item["graphID"] == graph_ID), None)
    patrol_route = searched_patrol['points']
    return patrol_route

def initialisation(input_data):

    graph_ID = input_data['graphID']
    URL = "https://go-pq.herokuapp.com/editor/graph/detailed/%s"%graph_ID
    r = requests.get(url = URL)
    graph_data = r.json()
    vertices = graph_data['vertices']
    list_of_vertices = list(vertices.keys())
    coordinates_of_verticies = []

    for vertice in list_of_vertices:

        x_coordinate = vertices[vertice].get('x')
        y_coordinate = vertices[vertice].get('y')
        coordinates_of_verticies.append([x_coordinate,y_coordinate])

    all_vertices_and_coordinates = dict(zip(list_of_vertices, coordinates_of_verticies))

    return all_vertices_and_coordinates

def starting_optimizer(all_vertices_and_coordinates, number_of_robots, patrol_route):

    # print(all_vertices_and_coordinates)
    list_of_vertices = list(all_vertices_and_coordinates.values())
    # print(list_of_vertices)
    X = np.array(list_of_vertices)
    plt.scatter(X[:,0],X[:,1], label='True Position')
    # plt.show()
    kmeans = KMeans(n_clusters=number_of_robots)
    kmeans.fit(X)
    # print(kmeans.cluster_centers_)
    # print(list_of_vertices)
    # all_shortest_vertice_and_coordinate = {}
    list_of_starting_vertices = []

    for center in kmeans.cluster_centers_:

        shortest_distance = 99999
        # current_list = list_of_vertices

        for vertice in all_vertices_and_coordinates:

            # print(vertice)
            vertice_coordinates = all_vertices_and_coordinates[vertice]
            # print(vertice_coordinates)
            distance = int(math.hypot(center[0] - vertice_coordinates[0], center[1] - vertice_coordinates[1]))

            # print(distance)
            # print(shortest_distance)

            if distance < shortest_distance:

                shortest_distance = distance
                shortest_distance_vertice = vertice
                # del all_vertices_and_coordinates[vertice]

        # print(shortest_distance_vertice)
        # print(all_vertices_and_coordinates.items())
        # del all_vertices_and_coordinates[shortest_distance_vertice]
        # print(shortest_distance_vertice)
        # print(all_vertices_and_coordinates)

        list_of_starting_vertices.append(shortest_distance_vertice)
        # print(list_of_starting_vertices)
        # vertice_coordinates = all_vertices_and_coordinates
        # all_shortest_vertice_and_coordinate.update( shortest_distance_vertice = all_vertices_and_coordinates[vertice])
    
    all_shortest_vertice_and_coordinate = {x: all_vertices_and_coordinates[x] for x in list_of_starting_vertices}
    # print(all_shortest_vertice_and_coordinate)
    # print(all_shortest_vertice_and_coordinate)
    # vertice_and_coordinates = dict(zip(patrol_route, list_of_shortest_distance_coordinates))

    print(all_shortest_vertice_and_coordinate)

    return all_shortest_vertice_and_coordinate

# def starting_optimizer(list_of_vertices, number_of_robots, patrol_route):

#     while len(list_of_vertices) > number_of_robots:

#         print(len(list_of_vertices))

#         list_of_total_distance = []
#         pointer = 0

#         for vertice in list_of_vertices:
            
#             previous_x_coordinate = list_of_vertices[pointer - 1][0]
#             previous_y_coordinate = list_of_vertices[pointer - 1][1]
#             current_x_coordinate = list_of_vertices[pointer][0]
#             current_y_coordinate = list_of_vertices[pointer][1]

#             if pointer == len(list_of_vertices) - 1 :

#                 next_x_coordinate = list_of_vertices[-1][0]
#                 next_y_coordinate = list_of_vertices[-1][1]

#             else:

#                 next_x_coordinate = list_of_vertices[pointer + 1][0]
#                 next_y_coordinate = list_of_vertices[pointer + 1][1]

#             pointer = pointer + 1
#             print(pointer)
#             distance_before = int(math.hypot(previous_x_coordinate - current_x_coordinate, previous_y_coordinate - current_y_coordinate))
#             distance_after = int(math.hypot(next_x_coordinate - current_x_coordinate, next_y_coordinate - current_y_coordinate))
#             list_of_total_distance.append(distance_after + distance_before)

#         index_of_smallest_distance = list_of_total_distance.index(min(list_of_total_distance))
#         list_of_vertices.pop(index_of_smallest_distance)
#         patrol_route.pop(index_of_smallest_distance)

#         vertice_and_coordinates = dict(zip(patrol_route, list_of_vertices))

#     return vertice_and_coordinates

def starting_payload(start_point):

    payload = '''{
                "modificationType": "CREATE",
                "abort": false,
                "taskType": "GOTO",
                "parameters": {},
                "point": {
                    "mapVerID": "b2a546f9-b7a1-4623-8c93-8a574b8db1f6",
                    "positionName": "Showroom",
                    "x": %s,
                    "y": %s,
                    "heading": 360
                },
                "totalTaskNo": 1,
                "currTaskNo": 1
    }'''%(start_point[0],start_point[1])

    return payload

def normal_payload(selected_node):

    payload = '''{
                "modificationType": "CREATE",
                "abort": false,
                "taskType": "GOTO",
                "parameters": {},
                "point": {
                    "mapVerID": "b2a546f9-b7a1-4623-8c93-8a574b8db1f6",
                    "positionName": "Showroom",
                    "x": %s,
                    "y": %s,
                    "heading": 360
                },
                "totalTaskNo": 1,
                "currTaskNo": 1
    }'''%(selected_node[0],selected_node[1])

    return payload

def localisation(robot):

    t_end = time.time() + 1

    while time.time() < t_end:

        client.subscribe("%s/robot/status"%robot)
        client.on_message=localisation_message
        client.loop(1)

def localisation_message(client, userdata, message):

    global all_robots_current_coordinates
    message = message.payload.decode("utf-8")
    message = json.loads(message)
    robot_id = message.get('robot_id')
    x_coordinates = message.get('positionX')
    y_coordinate = message.get('positionY')
    all_robots_current_coordinates[robot_id] = [x_coordinates,y_coordinate]

def complete_message(client, userdata, message):

    global complete_from_robot_id
    message = message.payload.decode("utf-8")
    message = json.loads(message)
    complete_from_robot_id = message['robot_id']

def starting_position(list_of_robots,vertices_and_coordinates):

    global complete_from_robot_id
    global all_robots_current_vertice

    # print(vertices_and_coordinates)

    list_of_starting_coordinates = list(vertices_and_coordinates.values())

    for robot in list_of_robots:

        # list_of_starting_coordinates = list(vertices_and_coordinates.values())
        # print(list_of_starting_coordinates)
        mqtt_payload = starting_payload(list_of_starting_coordinates[0])
        client.publish("%s/robot/task"%robot, mqtt_payload)
        print("[GOTO] %s is moving to starting point."%robot)

        while complete_from_robot_id != robot:

            client.subscribe("%s/robot/task/status"%robot)
            client.on_message=complete_message
            client.loop(1)

        complete_from_robot_id = None

        list_of_starting_coordinates.pop(0)

        print("[Notification] %s has reached starting point."%robot)

        localisation(robot)

        list_of_starting_vertices = list(vertices_and_coordinates.keys())
        # print(list_of_starting_vertices)

    all_robots_current_vertice = dict(zip(list_of_robots, list_of_starting_vertices))

    print("[Status] All robots at starting positions.")
    # print(list_of_starting_vertices)
    # print(all_robots_current_coordinates)

    return list_of_starting_vertices

def route_planning(list_of_starting_vertices, list_of_patrol_route, list_of_robots, input_data, ):

    number_of_loop = input_data['numberOfLoop']
    st = set(list_of_starting_vertices)
    list_of_index = [i for i, e in enumerate(list_of_patrol_route) if e in st]
    list_of_robot_paths = []

    for index in list_of_index:

        repeated_robot_path = []
        robot_path = []
        robot_path = list_of_patrol_route[int(index):] + list_of_patrol_route[:int(index)]

        if number_of_loop == 1:

            repeated_robot_path = robot_path

        else:
                
            for _ in range(number_of_loop):

                repeated_robot_path.extend(robot_path) 

        repeated_robot_path.pop(0)
        list_of_robot_paths.append(repeated_robot_path)

    robots_planned_route = dict(zip(list_of_robots, list_of_robot_paths))

    return robots_planned_route

def go_to(vertice, robot, all_vertices_and_coordinates):

    global complete_from_robot_id
    coordinate = all_vertices_and_coordinates[vertice]
    mqtt_payload = starting_payload(coordinate)
    client.publish("%s/robot/task"%robot, mqtt_payload)
    print("[GOTO] %s is moving to waypoint."%robot)

    while complete_from_robot_id != robot:

        client.subscribe("%s/robot/task/status"%robot)
        client.on_message=complete_message
        client.loop(1)

    complete_from_robot_id = None

    print("[Notification] %s has reached waypoint."%robot)

    localisation(robot)

def patrol_task(input_data):

    global complete_from_robot_id
    global all_robots_current_vertice
    global current_node_used
    complete_from_robot_id = None
    all_vertices_and_coordinates = initialisation(input_data)
    list_of_patrol_route = get_patrol_route(input_data)
    list_of_vertices = get_list_of_vertices(input_data, list_of_patrol_route.copy())
    list_of_robots = create_list_of_robots(input_data)
    number_of_robots = len(list_of_robots)
    starting_vertices_and_coordinates = starting_optimizer(all_vertices_and_coordinates, number_of_robots, list_of_patrol_route.copy())
    # print(starting_vertices_and_coordinates)
    list_of_starting_vertices = starting_position(list_of_robots, starting_vertices_and_coordinates)
    # print(list_of_starting_vertices)
    robots_planned_route = route_planning(list_of_starting_vertices, list_of_patrol_route, list_of_robots, input_data)
    current_node_used = list_of_starting_vertices

    finish = False
    
    while not finish:

        for robot in random.sample(list_of_robots,len(list_of_robots)):

            selected_node = robots_planned_route[robot][0]

            if selected_node in current_node_used:

                break

            current_node_used.remove(all_robots_current_vertice[robot])
            current_node_used.append(selected_node)
            all_robots_current_vertice[robot] = selected_node

            go_to(robots_planned_route[robot][0], robot, all_vertices_and_coordinates)

            robots_planned_route[robot].pop(0)

            if robots_planned_route[robot] == []:

                list_of_robots.remove(robot)

        if len(list_of_robots) == 0:

            finish = True
    