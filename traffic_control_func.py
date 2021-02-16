import requests
import time
import json
import math
import random
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import numpy as np
from ast import literal_eval
from sklearn.cluster import KMeans

broker_address="18.140.162.221"
client = mqtt.Client("TrafficController") 
client.connect(broker_address)
all_robots_current_coordinates = {}
all_robots_current_vertice = {}
robots_planned_route = {}
current_node_used = []
near_to_goto = False
complete_from_robot_id = None

# create_list_of_robots returns a list of robots
def create_list_of_robots(input_data):

    list_of_robots = []

    for task in input_data:

        task = task['taskDetails']

        for robot in task['robots']:

            list_of_robots.append(robot['robotID'])

    return list_of_robots

# create_group_of_robots returns a group of robots
def create_group_of_robots(input_data):

    group_of_robots = []

    for task in input_data:

        task = task['taskDetails']
        robot_task = task['robots']
        list_of_robots = []

        for robot in robot_task:

            list_of_robots.append(robot['robotID'])

        group_of_robots.append(list_of_robots)

    return group_of_robots

# get_detailed_graph retrieves all graph details
def get_detailed_graph(input_data):

    all_vertices_and_coordinates = {}

    for i, task in enumerate(input_data):

        task = task['taskDetails']
        graph_ID = task['graphID']
        URL = "http://18.140.162.221:8080/editor/graph/detailed/%s"%graph_ID
        r = requests.get(url = URL)
        graph_data = r.json()

    for i in input_data:

        vertices_and_coordinates = list()

    return graph_data

# get_patrol_route pull patrol data from traffic editor
def get_patrol_route(input_data):

    patrol_route = {}

    for task in input_data:

        task = task['taskDetails']
        patrol_ID = task['patrolID']
        graph_ID = task['graphID']
        robots = task['robots']
        URL = "http://18.140.162.221:8080/editor/patrol"
        r = requests.get(url = URL)
        graph_data = r.json()
        searched_patrol = next((item for item in graph_data if item.get("id") == patrol_ID and item["graphID"] == graph_ID), None)

        for robot in robots:

            patrol_route[robot['robotID']] = (searched_patrol['points'])

    return patrol_route

# patrol_initialisation generate the vertice data to show only vertice and corresponding coordinates
def patrol_initialisation(input_data, list_of_patrol_route):

    all_vertices_and_coordinates = {}

    for i, task in enumerate(input_data):

        task = task['taskDetails']
        graph_ID = task['graphID']
        URL = "http://18.140.162.221:8080/editor/graph/detailed/%s"%graph_ID
        r = requests.get(url = URL)
        graph_data = r.json()
        vertices = graph_data['vertices']
        list_of_vertices = list_of_patrol_route[i]
        coordinates_of_vertices = []

        for vertice in list_of_vertices:

            x_coordinate = vertices[vertice].get('x')
            y_coordinate = vertices[vertice].get('y')
            coordinates_of_vertices.append([x_coordinate,y_coordinate])

        vertices_and_coordinates = dict(zip(list_of_vertices, coordinates_of_vertices))
        
        all_vertices_and_coordinates.update(vertices_and_coordinates)

    return all_vertices_and_coordinates

# goto_initialisation cleans the vertice data to show only vertice and corresponding coordinates
def goto_initialisation(all_vertices_and_coordinates):

    # print("goto_init")
    # print(all_vertices_and_coordinates)
    # all_vertices_and_coordinates = {}

    # for vertice in list(all_vertices_and_coordinates):

    #     if "." in vertice:

    #         del all_vertices_and_coordinates[vertice]

    for vertice, vertice_details in all_vertices_and_coordinates.items():

        x_coordinate = vertice_details['x']
        y_coordinate = vertice_details['y']
        coordinates_of_vertice = [x_coordinate,y_coordinate]
        all_vertices_and_coordinates[vertice] = coordinates_of_vertice

    # print(all_vertices_and_coordinates)
    return all_vertices_and_coordinates
    
# starting_optimizer optimizes the starting positions of patrol robots
def starting_optimizer(all_vertices_and_coordinates, number_of_robots):

    list_of_vertices = list(all_vertices_and_coordinates.values())
    X = np.array(list_of_vertices)
    plt.scatter(X[:,0],X[:,1], label='True Position')
    kmeans = KMeans(n_clusters=number_of_robots*2)
    kmeans.fit(X)
    list_of_starting_vertices = []

    for center in kmeans.cluster_centers_:

        shortest_distance = 99999

        for vertice in all_vertices_and_coordinates:

            vertice_coordinates = all_vertices_and_coordinates[vertice]
            distance = int(math.hypot(center[0] - vertice_coordinates[0], center[1] - vertice_coordinates[1]))

            if distance < shortest_distance:

                shortest_distance = distance
                shortest_distance_vertice = vertice

        list_of_starting_vertices.append(shortest_distance_vertice)

    all_shortest_vertice_and_coordinate = {x: all_vertices_and_coordinates[x] for x in list_of_starting_vertices}

    return all_shortest_vertice_and_coordinate

def normal_payload(start_point):

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

# normal_payload generate mqtt payload to any point     
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

# localisation retrieves the position of all robots
def localisation(robot):

    t_end = time.time() + 1

    while time.time() < t_end:

        client.subscribe("%s/robot/status"%robot)
        client.on_message=localisation_message
        client.loop(1)

#localisation_message is the message sent to update robot location
def localisation_message(client, userdata, message):

    global all_robots_current_coordinates
    message = message.payload.decode("utf-8")
    message = json.loads(message)
    robot_id = message.get('robot_id')
    x_coordinates = message.get('positionX')
    y_coordinate = message.get('positionY')
    all_robots_current_coordinates[robot_id] = [x_coordinates,y_coordinate]
    # print(all_robots_current_coordinates)

#complete_message is the extracts the robot id from complete message
def complete_message(client, userdata, message):

    global complete_from_robot_id
    global near_to_goto
    message = message.payload.decode("utf-8")
    message = json.loads(message)
    # print(near_to_goto)

    try: 

        if message['taskStatusType'] == 'COMPLETED' or near_to_goto == True:

            complete_from_robot_id = message['robot_id']
        
        near_to_goto = False

    except:

        return None

#starting_position determines the optimal starting position of robots in multi patrol
def starting_position(group_of_robots,list_of_robots,vertices_and_coordinates,patrol_route):

    # print(group_of_robots)
    # print(list_of_robots)
    # print(patrol_route)
    global complete_from_robot_id
    global all_robots_current_vertice
    global all_robots_current_coordinates
    starting_coordinates = {}
    distance_groups = []
    
    while len(all_robots_current_coordinates) != len(list_of_robots):
        
        for robot in list_of_robots:

            localisation(robot)

    # print(all_robots_current_coordinates)
    # print(vertices_and_coordinates)
    for list_of_robots in group_of_robots:

        # for robot in list_of_robots:

        #     localisation(robot)
        # print(all_robots_current_coordinates)
        list_of_starting_vertices = list(vertices_and_coordinates.keys())

        list_of_distance = []

        for robot in list_of_robots:

            current_coordinate = all_robots_current_coordinates[robot]

            for vertice, start_coordinates in vertices_and_coordinates.items():

                distance = math.sqrt(int( ((current_coordinate[0]-start_coordinates[0])**2)+((current_coordinate[1]-start_coordinates[1])**2) ))
                vertice_distance = [distance, robot, vertice]

                if vertice in patrol_route[robot]:

                    list_of_distance.append(vertice_distance)

        list_of_distance.sort(key = lambda list_of_distance: list_of_distance[0]) 
        distance_groups.append(list_of_distance)

    # print(distance_groups)
        # print(list_of_distance)
        # print(patrol_route)
        # print(list_of_robots)
        # print(list_of_starting_vertices)
        # print(starting_vertices)
        # print(starting_coordinates)
    starting_vertices = {}

    for i, list_of_robots in enumerate(group_of_robots):
        # print(list_of_robots)
        for list_of_distance in distance_groups:

            # print(list_of_distance)

            for distance in list_of_distance:
        # while len(list_of_distance) > 0:
                # print(list_of_robots)
                # print(distance)
                # print(distance[2])
                # print(group_of_robots[i])
                # print(group_of_robots)
                # print(list_of_starting_vertices)
                # print(patrol_route[distance[1]])
                if distance[1] in list_of_robots and distance[2] in list_of_starting_vertices and distance[2] in patrol_route[distance[1]]:
    #  and distance[2] in patrol_route[distance[1]]
                    # print(distance)
                    # print(list_of_starting_vertices)
                    # print(list_of_robots)
                    starting_vertices[distance[1]] = distance[2]
                    list_of_robots.remove(distance[1])
                    list_of_starting_vertices.remove(distance[2])
                    list_of_distance.remove(distance) 
                
    # print(starting_vertices)

    for robot, vertice in starting_vertices.items():

        starting_coordinates[robot] = vertices_and_coordinates[vertice]

    for robot, coordinate in starting_coordinates.items():

        mqtt_payload = normal_payload(coordinate)
        client.publish("%s/robot/task"%robot, mqtt_payload)
        print("[GOTO] %s is moving to starting point."%robot)

        while complete_from_robot_id != robot:

            client.subscribe("%s/robot/task/status"%robot)
            client.on_message=complete_message
            client.loop(1)

        complete_from_robot_id = None

        print("[Notification] %s has reached starting point."%robot)

        localisation(robot)

    # time.sleep(10)
    print("[Status] All robots at starting positions.")

    all_robots_current_vertice = starting_vertices

    # print(starting_vertices)
    return starting_vertices

# route_planning performs sequence based approach of path planning
def route_planning(starting_vertices, patrol_route, input_data):

    robots_planned_route = {}

    for i, task in enumerate(input_data):

        task = task['taskDetails']
        number_of_loop = task['numberOfLoop']

        for robot, vertices in patrol_route.items():

            if vertices[0] == vertices[-1]:

                del vertices[-1]

            index = vertices.index(starting_vertices[robot])
            repeated_robot_path = []
            robot_path = []
            robot_path = vertices[int(index):] + vertices[:int(index)]

            if number_of_loop == 1:

                repeated_robot_path = robot_path

            else:

                for _ in range(number_of_loop):

                    repeated_robot_path.extend(robot_path)

            repeated_robot_path.pop(0)
            robots_planned_route[robot] = repeated_robot_path

    return robots_planned_route

def proximity_to_goto(robot, goto_coordinates):

    global near_to_goto
    # print(robot)
    # print(goto_coordinates)
    localisation(robot)
    robot_current_coordinates = all_robots_current_coordinates[robot]
    # print(robot_current_coordinates)

    distance_from_goto = math.sqrt((goto_coordinates[0] - robot_current_coordinates[0]) ** 2 + (goto_coordinates[1] - robot_current_coordinates[1]) ** 2)

    print(distance_from_goto)
    # if distance_from_goto < 50:

    #     near_to_goto = True

    # # print(all_vertices_and_coordinates)

    # for vertice, coordinate in all_vertices_and_coordinates.items():

    #     # print(vertice)
    #     # print(vertice.find('.'))

    #     dist =  math.sqrt((coordinate[0] - robot_current_coordinates[0])**2 + (coordinate[1] - robot_current_coordinates[1])**2)

    #     if min_dist is 0:

    #         min_dist = dist

    #     else:

    #         if dist < min_dist:

    #             min_dist = dist
    #             min_vertice = vertice

    return None

def go_to(vertice, robot, all_vertices_and_coordinates):

    global complete_from_robot_id
    coordinate = all_vertices_and_coordinates[vertice]
    mqtt_payload = normal_payload(coordinate)
    client.publish("%s/robot/task"%robot, mqtt_payload)
    print("[GOTO] %s is moving to waypoint."%robot)
    # localisation(robot)
    print(all_robots_current_coordinates)

    while complete_from_robot_id != robot:

        proximity_to_goto(robot,coordinate)
        client.subscribe("%s/robot/task/status"%robot)
        client.on_message=complete_message
        client.loop(1)

    localisation(robot)
    complete_from_robot_id = None

    print("[Notification] %s has reached waypoint."%robot)

# get_patrol_route_list generates a list of patrol route
def get_patrol_route_list(input_data):

    patrol_route = []

    for task in input_data:

        task = task['taskDetails']
        patrol_ID = task['patrolID']
        graph_ID = task['graphID']
        URL = "http://18.140.162.221:8080/editor/patrol"
        r = requests.get(url = URL)
        graph_data = r.json()
        searched_patrol = next((item for item in graph_data if item.get("id") == patrol_ID and item["graphID"] == graph_ID), None)
        patrol_route.append(searched_patrol['points'])
    
    return patrol_route

# dijkstra algorithm is used to determine the shortest route
def dijkstra(start,end,graph):

    unvisitedNodes = graph
    shortestDistance = {}
    trackPredecessor = {}
    infinity = 99999
    trackPath = []

    for node in unvisitedNodes:

        shortestDistance[node] = infinity

    shortestDistance[start] = 0
    
    while unvisitedNodes:

        minDistanceNode = None

        for node in unvisitedNodes:

            if minDistanceNode is None:

                minDistanceNode = node

            elif shortestDistance[node] < shortestDistance[minDistanceNode]:

                minDistanceNode = node

        pathOptions = graph[minDistanceNode].items()

        for childNode, weight in pathOptions:

            if weight + shortestDistance[minDistanceNode] < shortestDistance[childNode]:

                shortestDistance[childNode] = weight + shortestDistance[minDistanceNode]
                trackPredecessor[childNode] = minDistanceNode

        unvisitedNodes.pop(minDistanceNode)

    currentNode = end

    while currentNode != start:

        try:
            trackPath.insert(0,currentNode)
            currentNode = trackPredecessor[currentNode]

        except KeyError:

            print("Path is not reachable")
            break

    trackPath.insert(0,start)
    end = str(end)

    if shortestDistance[end] != infinity:
        
        return trackPath

# nearest_vertice finds vertice closest to robots
def nearest_vertice(all_vertices_and_coordinates, robot):

    global all_robots_current_coordinates
    robot_current_coordinates = all_robots_current_coordinates[robot]
    min_dist = 0
    min_vertice = 0

    # print(all_vertices_and_coordinates)

    for vertice, coordinate in all_vertices_and_coordinates.items():

        # print(vertice)
        # print(vertice.find('.'))

        dist =  math.sqrt((coordinate[0] - robot_current_coordinates[0])**2 + (coordinate[1] - robot_current_coordinates[1])**2)

        if min_dist is 0:

            min_dist = dist

        else:

            if dist < min_dist:

                min_dist = dist
                min_vertice = vertice

    return min_vertice

# patrol_task performs the patrol task
def patrol_task(input_data):

    # print(input_data)
    global complete_from_robot_id
    global all_robots_current_vertice
    global current_node_used

    complete_from_robot_id = None
    patrol_route = get_patrol_route(input_data)
    list_of_patrol_route = get_patrol_route_list(input_data)
    all_vertices_and_coordinates = patrol_initialisation(input_data, list_of_patrol_route)
    list_of_robots = create_list_of_robots(input_data)
    group_of_robots = create_group_of_robots(input_data)
    number_of_robots = len(list_of_robots)
    starting_vertices_and_coordinates = starting_optimizer(all_vertices_and_coordinates, number_of_robots)
    starting_vertices = starting_position(group_of_robots,list_of_robots, starting_vertices_and_coordinates, patrol_route)
    robots_planned_route = route_planning(starting_vertices, patrol_route, input_data)
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

    return "[Notification] Robots have completed their task."

# patrol_task performs the patrol task
def goto_task(input_data):

    global complete_from_robot_id
    global all_robots_current_vertice
    global current_node_used

    complete_from_robot_id = None
    detailed_graph = get_detailed_graph(input_data)
    robot = input_data[0]['taskDetails']['robots'][0]['robotID']
    localisation(robot)
    all_vertices_and_coordinates = goto_initialisation(detailed_graph['vertices'])
    start_vertice = nearest_vertice(all_vertices_and_coordinates, robot)
    end_vertice = input_data[0]['taskDetails']['end']
    start_vertice = str(float(start_vertice))
    end_vertice = str(float(end_vertice))
    lanes = detailed_graph['lanes']
    shortest_route = dijkstra(start_vertice,end_vertice,lanes)
    robots_planned_route = {robot:shortest_route}
    list_of_robots = create_list_of_robots(input_data)
    finish = False

    while not finish:

        for robot in list_of_robots:

            selected_node = robots_planned_route[robot][0]
            current_node_used.append(selected_node)
            all_robots_current_vertice[robot] = selected_node
            go_to(robots_planned_route[robot][0], robot, all_vertices_and_coordinates)
            robots_planned_route[robot].pop(0)
            current_node_used.remove(all_robots_current_vertice[robot])

            if robots_planned_route[robot] == []:

                list_of_robots.remove(robot)

            if len(list_of_robots) == 0:

                finish = True

    return "Completed GOTO Task"