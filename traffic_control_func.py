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
    URL = "https://go-patrol.herokuapp.com/editor/graph/detailed/%s"%graph_ID
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

def initialisation(input_data, list_of_vertices):

    graph_ID = input_data['graphID']
    URL = "https://go-patrol.herokuapp.com/editor/graph/detailed/%s"%graph_ID
    r = requests.get(url = URL)
    graph_data = r.json()
    vertices = graph_data['vertices']

    coordinates_of_verticies = []

    for vertice in list_of_vertices:

        x_coordinate = vertices[vertice].get('x')
        y_coordinate = vertices[vertice].get('y')
        coordinates_of_verticies.append([x_coordinate,y_coordinate])

    all_vertices_and_coordinates = dict(zip(list_of_vertices, coordinates_of_verticies))

    return all_vertices_and_coordinates

def starting_optimizer(all_vertices_and_coordinates, number_of_robots, patrol_route):

    list_of_vertices = list(all_vertices_and_coordinates.values())

    X = np.array(list_of_vertices)
    plt.scatter(X[:,0],X[:,1], label='True Position')
    kmeans = KMeans(n_clusters=number_of_robots)
    kmeans.fit(X)
    list_of_starting_vertices = []

    for center in kmeans.cluster_centers_:

        shortest_distance = 99999

        for vertice in all_vertices_and_coordinates:

            # print(vertice)
            vertice_coordinates = all_vertices_and_coordinates[vertice]
            # print(vertice_coordinates)
            distance = int(math.hypot(center[0] - vertice_coordinates[0], center[1] - vertice_coordinates[1]))

            if distance < shortest_distance:

                shortest_distance = distance
                shortest_distance_vertice = vertice

        list_of_starting_vertices.append(shortest_distance_vertice)

    all_shortest_vertice_and_coordinate = {x: all_vertices_and_coordinates[x] for x in list_of_starting_vertices}

    return all_shortest_vertice_and_coordinate

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

    for robot in list_of_robots:

        localisation(robot)

    list_of_starting_vertices = list(vertices_and_coordinates.keys())

    global complete_from_robot_id
    global all_robots_current_vertice
    global all_robots_current_coordinates
    starting_vertices = {}
    starting_coordinates = {}

    list_of_distance = []

    for robot in list_of_robots:

        current_coordinate = all_robots_current_coordinates[robot]

        for vertice, start_coordinates in vertices_and_coordinates.items():

            distance = math.sqrt( ((current_coordinate[0]-start_coordinates[0])**2)+((current_coordinate[1]-start_coordinates[1])**2) )
            vertice_distance = [distance, robot, vertice]
            list_of_distance.append(vertice_distance)

    list_of_distance.sort(key = lambda list_of_distance: list_of_distance[0]) 

    for distance in list_of_distance:

        if distance[1] in list_of_robots and distance[2] in list_of_starting_vertices:

            starting_vertices[distance[1]] = distance[2] 
            list_of_robots.remove(distance[1])
            list_of_starting_vertices.remove(distance[2])

    for robot, vertice in starting_vertices.items():

        starting_coordinates[robot] = vertices_and_coordinates[vertice]

    for robot, coordinate in starting_coordinates.items():

        mqtt_payload = starting_payload(coordinate)
        client.publish("%s/robot/task"%robot, mqtt_payload)
        print("[GOTO] %s is moving to starting point."%robot)

        while complete_from_robot_id != robot:

            client.subscribe("%s/robot/task/status"%robot)
            client.on_message=complete_message
            client.loop(1)

        complete_from_robot_id = None

        print("[Notification] %s has reached starting point."%robot)

        localisation(robot)

    print("[Status] All robots at starting positions.")

    all_robots_current_vertice = starting_vertices

    return starting_vertices

def route_planning(starting_vertices, patrol_route, input_data):

    robots_planned_route = {}

    number_of_loop = input_data['numberOfLoop']

    for robot, vertice in starting_vertices.items():

        index = patrol_route.index(vertice)
        repeated_robot_path = []
        robot_path = []
        robot_path = patrol_route[int(index):] + patrol_route[:int(index)]

        if number_of_loop == 1:

            repeated_robot_path = robot_path

        else:
                
            for _ in range(number_of_loop):

                repeated_robot_path.extend(robot_path) 

        repeated_robot_path.pop(0)
        robots_planned_route[robot] = repeated_robot_path

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
    list_of_patrol_route = get_patrol_route(input_data)
    all_vertices_and_coordinates = initialisation(input_data, list_of_patrol_route)
    list_of_vertices = get_list_of_vertices(input_data, list_of_patrol_route.copy())
    list_of_robots = create_list_of_robots(input_data)
    number_of_robots = len(list_of_robots)
    starting_vertices_and_coordinates = starting_optimizer(all_vertices_and_coordinates, number_of_robots, list_of_patrol_route.copy())
    starting_vertices = starting_position(list_of_robots, starting_vertices_and_coordinates)
    robots_planned_route = route_planning(starting_vertices, list_of_patrol_route, input_data)
    current_node_used = list(starting_vertices.values())
    list_of_robots = create_list_of_robots(input_data)

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
        
        print(robots_planned_route)
    