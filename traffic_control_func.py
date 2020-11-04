import requests
import time
import json
import paho.mqtt.client as mqtt
from ast import literal_eval

broker_address="localhost"
client = mqtt.Client("TrafficController") 
client.connect(broker_address)
priority = {}
robots_shortest_path = {}
all_coordinates = {}
reply_from_robot_id = ''

def __init__(input_data):

    for robot in input_data:
    
        URL = "https://shortestpathfinderapi.herokuapp.com/robot/%s"%robot
        r = requests.get(url = URL)
        path_data = r.json()
        coordinates = literal_eval(path_data['coordinates'])
        all_coordinates.update({robot:coordinates})
        coordinates_of_shortest = literal_eval(path_data['shortest_path'])
        robots_shortest_path.update({robot:coordinates_of_shortest})
        robot_priority = (path_data['priority'])
        priority.update({robot:robot_priority})

def on_message(client, userdata, message):

    global reply_from_robot_id
    message = message.payload.decode("utf-8")
    message = json.loads(message)
    reply_from_robot_id = message['robot_id']

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
    x_coordinate = str(node_coordinate['x'])
    y_coordinate = str(node_coordinate['y']+40)

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

def send_coordinates(input_data):

    global reply_from_robot_id
    finish = False
    current_node_used = []
    nodes_occupied = []

    __init__(input_data)

    while not finish:

        list_of_robots = input_data

        for robot in list_of_robots:

            if robots_shortest_path[robot] == []:

                list_of_robots.remove(robot)
                break

            selected_node = robots_shortest_path[robot][0]

            if selected_node in current_node_used:

                break

            if selected_node in nodes_occupied:

                print("Robot id: %s is blocked."%robot)
                mqtt_payload = evasive_payload(robot,selected_node)
                client.publish("%s/robot/task"%robot, mqtt_payload)  
                robot_shortest_path = robots_shortest_path[robot]
                robot_shortest_path.remove(selected_node)
                print("Robot id: %s is moving to waiting point."%robot) 

                while reply_from_robot_id != robot:

                    client.subscribe("/robot/task/status")
                    client.on_message=on_message
                    client.loop(1)
                
                print("Robot id: %s is reached waypoint."%robot)
            
            else:

                current_node_used.append(selected_node)
                mqtt_payload = normal_payload(robot,selected_node)
                client.publish("%s/robot/task"%robot, mqtt_payload)
                print("Robot id: %s is moving to next waypoint."%robot)

                while reply_from_robot_id != robot:

                    client.subscribe("/robot/task/status")
                    client.on_message=on_message
                    client.loop(1)

                print("Robot id: %s is reached waypoint."%robot)
                robot_shortest_path = robots_shortest_path[robot]

                if len(robot_shortest_path) == 1:

                    nodes_occupied.append(selected_node)
                    
                robot_shortest_path.remove(selected_node)

            reply_from_robot_id = ''
        
        if len(list_of_robots) == 0:

            print("Robots have reached their destination.")
            finish = True

        current_node_used.clear()