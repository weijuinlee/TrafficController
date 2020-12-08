import requests
import time
import json
import math
import paho.mqtt.client as mqtt
from ast import literal_eval

broker_address="18.140.162.221"
client = mqtt.Client("TrafficController") 
client.connect(broker_address)
all_robots_position = {}
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

def starting_optimizer(list_of_vertices, number_of_robots, patrol_route):

    while len(list_of_vertices) > number_of_robots:

        list_of_total_distance = []
        pointer = 0

        for vertice in list_of_vertices:
            
            previous_x_coordinate = list_of_vertices[pointer - 1][0]
            previous_y_coordinate = list_of_vertices[pointer - 1][1]
            current_x_coordinate = list_of_vertices[pointer][0]
            current_y_coordinate = list_of_vertices[pointer][1]

            if pointer == len(list_of_vertices) - 1 :

                next_x_coordinate = list_of_vertices[-1][0]
                next_y_coordinate = list_of_vertices[-1][1]

            else:

                next_x_coordinate = list_of_vertices[pointer + 1][0]
                next_y_coordinate = list_of_vertices[pointer + 1][1]

            pointer = pointer + 1
            distance_before = int(math.hypot(previous_x_coordinate - current_x_coordinate, previous_y_coordinate - current_y_coordinate))
            distance_after = int(math.hypot(next_x_coordinate - current_x_coordinate, next_y_coordinate - current_y_coordinate))
            list_of_total_distance.append(distance_after + distance_before)

        index_of_smallest_distance = list_of_total_distance.index(min(list_of_total_distance))
        list_of_vertices.pop(index_of_smallest_distance)
        patrol_route.pop(index_of_smallest_distance)

    return list_of_vertices

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

def localisation(robot):

    t_end = time.time() + 1

    while time.time() < t_end:

        client.subscribe("%s/robot/status"%robot)
        client.on_message=localisation_message
        client.loop(1)

def localisation_message(client, userdata, message):

    global all_robots_position
    message = message.payload.decode("utf-8")
    message = json.loads(message)
    robot_id = message.get('robot_id')
    x_coordinates = message.get('positionX')
    y_coordinate = message.get('positionY')
    all_robots_position[robot_id] = [x_coordinates,y_coordinate]

def complete_message(client, userdata, message):

    global complete_from_robot_id
    message = message.payload.decode("utf-8")
    message = json.loads(message)
    complete_from_robot_id = message['robot_id']

def starting_position(list_of_robots, list_of_vertices,list_of_starting_vertices):

    global complete_from_robot_id

    for robot in list_of_robots:

        mqtt_payload = starting_payload(list_of_starting_vertices[0])
        client.publish("%s/robot/task"%robot, mqtt_payload)
        print("[GOTO] %s is moving to starting point."%robot)

        while complete_from_robot_id != robot:

            client.subscribe("%s/robot/task/status"%robot)
            client.on_message=complete_message
            client.loop(1)

        complete_from_robot_id = None

        list_of_starting_vertices.pop(0)

        print("[Notification] %s has reached starting point."%robot)

        localisation(robot)

    print("[Status] All robots at starting positions.")

def normal_payload(robot,node):

    node_coordinate = all_coordinates[robot][node]
    x_coordinate = str(node_coordinate['x'])
    y_coordinate = str(node_coordinate['y'])

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
    }'''%(x_coordinate,y_coordinate)

    return payload

def evasive_payload(robot,node):

    node_coordinate = all_coordinates[robot][node]
    x_coordinate = str(node_coordinate['x']+20)
    y_coordinate = str(node_coordinate['y']+20)

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
    }'''%(x_coordinate,y_coordinate)

    return payload

def calculate_distance(robot,node):

    node_coordinate = all_coordinates[robot][node]
    next_x_coordinate = node_coordinate['x']
    next_y_coordinate = node_coordinate['y']
    coordinates =  all_robots_position[robot]
    current_x_coordinate = coordinates[0]
    current_y_coordinate = coordinates[1]
    distance = math.sqrt( ((next_x_coordinate + current_x_coordinate)**2) + ((next_y_coordinate + current_y_coordinate)**2) )

    return distance

def patrol_task(input_data):

    repeated = input_data['repeated']
    patrol_route = get_patrol_route(input_data)
    list_of_vertices = get_list_of_vertices(input_data, patrol_route)
    list_of_robots = create_list_of_robots(input_data)
    number_of_robots = len(list_of_robots)
    list_of_starting_vertices = starting_optimizer(list_of_vertices,number_of_robots, patrol_route)
    starting_position(list_of_robots, list_of_vertices, list_of_starting_vertices)
