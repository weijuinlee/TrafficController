import requests
import time
import json
import math
import paho.mqtt.client as mqtt
from ast import literal_eval

broker_address="18.140.162.221"
client = mqtt.Client("TrafficController") 
client.connect(broker_address)
robots_shortest_path = {}
all_coordinates = {}
all_robots_position = {}
robots_at_destinatiton = {}
reply_from_robot_id = ''
code_red_message = ''

def __init__(input_data):

    graph_ID = input_data['graphID']
    URL = "https://go-pq.herokuapp.com/editor/graph/detailed/%s"%graph_ID
    r = requests.get(url = URL)
    graph_data = r.json()
    list_of_verticies = []
    vertices = graph_data['vertices']

    for vertice in vertices:
        vertice = vertices.get(vertice)
        x_coordinate = vertice.get('x')
        y_coordinate = vertice.get('y')
        list_of_verticies.append([x_coordinate,y_coordinate])

    return list_of_verticies

def create_list_of_robots(input_data):

    list_of_robots = []

    for robot in input_data['robots']:

        list_of_robots.append(robot['robotID'])

    return list_of_robots

def starting_position(list_of_robots):

    global reply_from_robot_id

    for robot in list_of_robots:

        if robots_shortest_path[robot] == []:

            break

        selected_node = robots_shortest_path[robot][0]
        mqtt_payload = normal_payload(robot,selected_node)
        client.publish("%s/robot/task"%robot, mqtt_payload)
        # current_node_used.append(selected_node)
        robot_shortest_path = robots_shortest_path[robot]
        robot_shortest_path.remove(selected_node)
        print("[GOTO] %s is moving to initial waypoint."%robot)

        while reply_from_robot_id != robot:

            client.subscribe("%s/robot/task/status"%robot)
            client.on_message=init_message
            client.loop(1)

        robot_shortest_path = robots_shortest_path[robot]
        reply_from_robot_id = ''
        print("[Notification] %s has reached initial waypoint."%robot)

        t_end = time.time() + 1

        while time.time() < t_end:

            client.subscribe("%s/robot/status"%robot)
            client.on_message=normal_message
            client.loop(1)

    print("[Status] All robots initialized.")

def init_message(client, userdata, message):

    global reply_from_robot_id
    global code_red_message
    message = message.payload.decode("utf-8")
    message = json.loads(message)
    # print(message)
    reply_from_robot_id = message['robot_id']

    try:
        code_red_message = message['taskStatusType']

    except:

        pass

def normal_message(client, userdata, message):

    global all_robots_position
    message = message.payload.decode("utf-8")
    message = json.loads(message)
    robot_id = message.get('robot_id')
    x_coordinates = message.get('positionX')
    y_coordinate = message.get('positionY')
    all_robots_position[robot_id] = [x_coordinates,y_coordinate]

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

def send_coordinates(input_data):

    global reply_from_robot_id
    finish = False
    current_node_used = []

    repeated = input_data['repeated']
    list_of_vertices = __init__(input_data)
    list_of_robots = create_list_of_robots(input_data)
    
    print(list_of_vertices)
    print(list_of_robots)
    print(repeated)

    while not finish:

        for robot in list_of_robots:

            if code_red_message == "FAILED":

                print("[Notification] Code red!!!")

            if robots_shortest_path[robot] == []:

                list_of_robots.remove(robot)

                break

            selected_node = robots_shortest_path[robot][0]

            if selected_node in current_node_used:

                break

            if selected_node in robots_at_destinatiton:
  
                robot_blocking = robots_at_destinatiton.get(selected_node)
                print("[Notification] Robot id: %s is blocking Robot id: %s"%(robot_blocking,robot))

                mqtt_payload = evasive_payload(robot_blocking,selected_node)
                client.publish("%s/robot/task"%robot_blocking, mqtt_payload)  
                print("[Status] Robot id: %s is giving way to %s."%(robot_blocking,robot))

                time.sleep(1)

                mqtt_payload = normal_payload(robot,selected_node)
                client.publish("%s/robot/task"%robot, mqtt_payload)
                distance = calculate_distance(robot,selected_node)  
                robot_shortest_path = robots_shortest_path[robot]
                robot_shortest_path.remove(selected_node)
                print("[Status] Robot id: %s is moving to next waypoint."%robot) 

                t_end = time.time() + (distance/600)

                while time.time() < t_end:

                    client.subscribe("/robot/status")
                    client.on_message=normal_message
                    client.loop(1)

                print("[Status] Robot id: %s is reached waypoint."%robot)

            else:

                t_end = time.time() + 1

                while time.time() < t_end:

                    client.subscribe("%s/robot/status"%robot)
                    client.on_message=init_message
                    client.loop(1)

                if reply_from_robot_id != robot:

                    current_node_used.append(selected_node)
                    mqtt_payload = normal_payload(robot,selected_node)
                    distance = calculate_distance(robot,selected_node)
                    client.publish("%s/robot/task"%robot, mqtt_payload)
                    print("[Status] Robot id: %s is moving to next waypoint."%robot)

                    t_end = time.time() + (distance/400)

                    while time.time() < t_end:

                        client.subscribe("%s/robot/status"%robot)
                        client.on_message=normal_message
                        client.loop(1)

                    t_end = time.time() + 1

                    while time.time() < t_end:

                        client.subscribe("%s/robot/status"%robot)
                        client.on_message=normal_message
                        client.loop(1)

                    robot_shortest_path = robots_shortest_path[robot]
                    robot_shortest_path.remove(selected_node)

                else:

                    selected_node = robots_shortest_path[robot][0]
                    mqtt_payload = normal_payload(robot,selected_node)
                    client.publish("%s/robot/task"%robot, mqtt_payload)
                    current_node_used.append(selected_node)
                    robot_shortest_path = robots_shortest_path[robot]
                    print("[GOTO] Robot id: %s is moving to next waypoint."%robot)

                    while reply_from_robot_id != robot:

                        client.subscribe("%s/robot/status"%robot)
                        client.on_message=init_message
                        client.loop(1)

                    robot_shortest_path = robots_shortest_path[robot]
                    robot_shortest_path.remove(selected_node)
                    reply_from_robot_id = ''
                    print("[Status] %s has reached next waypoint."%robot)

            if len(robot_shortest_path) == 0:

                robots_at_destinatiton.update({selected_node:robot})

        if len(list_of_robots) == 0:
            
            for selected_node in robots_at_destinatiton:
        
                robot = robots_at_destinatiton.get(selected_node)
                mqtt_payload = normal_payload(robot,selected_node)
                client.publish("%s/robot/task"%robot, mqtt_payload)  
                print("[Status] Robot id: %s returning to their destination."%robot)
                time.sleep(1)

            print("[Status] Robots have reached their destination.")
            finish = True

        current_node_used.clear()