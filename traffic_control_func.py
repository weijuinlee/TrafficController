import requests
import time
import json
import math
import random
import paho.mqtt.client as mqtt
# import threading
# import logging

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
    # print(patrol_route)
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

        vertice_and_coordinates = dict(zip(patrol_route, list_of_vertices))

    return vertice_and_coordinates

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

def starting_position(list_of_robots, list_of_vertices,vertices_and_coordinates):

    global complete_from_robot_id
    global all_robots_current_vertice

    list_of_starting_coordinates = list(vertices_and_coordinates.values())

    for robot in list_of_robots:
        # print(list_of_starting_coordinates[0])
        mqtt_payload = starting_payload(list_of_starting_coordinates[0])
        # print(mqtt_payload)
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

    all_robots_current_vertice = dict(zip(list_of_robots, list_of_starting_vertices))

    print("[Status] All robots at starting positions.")

    return list_of_starting_vertices

def route_planning(list_of_starting_vertices, list_of_patrol_route, list_of_robots, input_data, ):

    # print(list_of_robots)
    # print(list_of_starting_vertices)
    # print(list_of_patrol_route)

    number_of_loop = input_data['numberOfLoop']
    st = set(list_of_starting_vertices)
    list_of_index = [i for i, e in enumerate(list_of_patrol_route) if e in st]

    list_of_robot_paths = []

    # print(list_of_index)

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
    
    # print(list_of_robots)

    # print(list_of_robot_paths)
    
    robots_planned_route = dict(zip(list_of_robots, list_of_robot_paths))

    # print("test")

    print(robots_planned_route)

    return robots_planned_route

def go_to(vertice, robot, all_vertices_and_coordinates):

    global complete_from_robot_id

    # print(list_of_vertices)

    # for vertice in list_of_vertices:

    # print(vertice)
    coordinate = all_vertices_and_coordinates[vertice]
    # print(coordinate)
    mqtt_payload = starting_payload(coordinate)
    client.publish("%s/robot/task"%robot, mqtt_payload)
    print("[GOTO] %s is moving to waypoint."%robot)

    while complete_from_robot_id != robot:

        client.subscribe("%s/robot/task/status"%robot)
        client.on_message=complete_message
        client.loop(1)
    
    # print("list_of_vertices%s"%list_of_vertices)
    complete_from_robot_id = None

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
    starting_vertices_and_coordinates = starting_optimizer(list_of_vertices, number_of_robots, list_of_patrol_route.copy())
    list_of_starting_vertices = starting_position(list_of_robots, list_of_vertices, starting_vertices_and_coordinates)
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

            print(robots_planned_route)

            print(current_node_used)

            robots_planned_route[robot].pop(0)

            if robots_planned_route[robot] == []:

                list_of_robots.remove(robot)

        if len(list_of_robots) == 0:

            finish = True

    # print(robots_planned_route)

        #     selected_node = robots_planned_route[robot][0]
        #     print(all_robots_current_vertice)
        #     print(current_node_used)
        #     previous_node = all_robots_current_vertice[robot]
        #     current_node_used.remove(previous_node)

        #     if selected_node in current_node_used:
        # current_node_used.clear()
        #         break
            
        #     all_robots_current_vertice[robot] = selected_node
        #     current_node_used.append(selected_node)
        #     # print(selected_node)
        #     # print(all_vertices_and_coordinates[selected_node])
        #     robots_planned_route[robot].pop(0)
        #     mqtt_payload = starting_payload(all_vertices_and_coordinates[selected_node])
        #     # print(mqtt_payload)
        #     client.publish("%s/robot/task"%robot, mqtt_payload)
        #     print("[GOTO] %s is moving to waypoint."%robot)

        #     # while complete_from_robot_id != robot:
        #     #     print(complete_from_robot_id)
        #     #     client.subscribe("%s/robot/task/status"%robot)
        #     #     client.on_message=complete_message
        #     #     client.loop(1)

        #     # print(complete_from_robot_id)

        #     while complete_from_robot_id != robot:

        #         client.subscribe("%s/robot/task/status"%robot)
        #         client.on_message=complete_message
        #         client.loop(1)

            # complete_from_robot_id = None

                # list_of_starting_coordinates.pop(0)

        #     print("[Notification] %s has reached waypoint."%robot)
        #     # print(robots_planned_route)

        #     # print(current_node_used)

        #     localisation(robot)

        # # print(list_of_robots)
        # # print(robots_planned_route)
        # current_node_used.clear()
    #         if selected_node in current_node_used:

    #             break

    #         if selected_node in robots_at_destinatiton:
  
    #             robot_blocking = robots_at_destinatiton.get(selected_node)
    #             print("[Notification] Robot id: %s is blocking Robot id: %s"%(robot_blocking,robot))

    #             mqtt_payload = evasive_payload(robot_blocking,selected_node)
    #             client.publish("%s/robot/task"%robot_blocking, mqtt_payload)  
    #             print("[Status] Robot id: %s is giving way to %s."%(robot_blocking,robot))

    #             time.sleep(1)

    #             mqtt_payload = normal_payload(robot,selected_node)
    #             client.publish("%s/robot/task"%robot, mqtt_payload)
    #             distance = calculate_distance(robot,selected_node)  
    #             robot_shortest_path = robots_shortest_path[robot]
    #             robot_shortest_path.remove(selected_node)
    #             print("[Status] Robot id: %s is moving to next waypoint."%robot) 

    #             t_end = time.time() + (distance/600)

    #             while time.time() < t_end:

    #                 client.subscribe("/robot/status")
    #                 client.on_message=normal_message
    #                 client.loop(1)

    #             print("[Status] Robot id: %s is reached waypoint."%robot)

        # for  in list_of_values: 

        #     if robots_planned_route[robot] == []: 

        #         break

        #     print("here")

        #     finish = True