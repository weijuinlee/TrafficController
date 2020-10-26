import requests
import time
import json
import paho.mqtt.client as mqtt
from ast import literal_eval

broker_address="localhost"
client = mqtt.Client("1") 
client.connect(broker_address)
dict_of_priority = {}
dict_of_robot_shortest_path = {}
dict_of_coordinates = {}

def payload(robot,node):

    node_coordinate = dict_of_coordinates[robot][node]
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

def send_coordinates(input_data):

    finish = False
    nodes_occupied = []

    for robot in input_data['robot_id']:
        
        URL = "https://shortestpathfinderapi.herokuapp.com/robot/%s"%robot
        r = requests.get(url = URL)
        path_data = r.json()
        coordinates = literal_eval(path_data['coordinates'])
        dict_of_coordinates.update({robot:coordinates})
        coordinates_of_shortest = literal_eval(path_data['shortest_path'])
        dict_of_robot_shortest_path.update({robot:coordinates_of_shortest})
        robot_priority = (path_data['priority'])
        dict_of_priority.update({robot:robot_priority})
        mqtt_payload = payload(robot,'0')
        client.publish("%s/robot/task"%robot, mqtt_payload)

    time.sleep(15)

    print(dict_of_robot_shortest_path)

    if len(input_data['robot_id']) == 1:

        print("One robot")

    else:
        
        print("More than one robot")

        # for i in range(15):
        while not finish:

            list_of_robots = input_data['robot_id']

            for robot in list_of_robots:

                if dict_of_robot_shortest_path[robot] == []:

                    list_of_robots.remove(robot)
                    break

                selected_node = dict_of_robot_shortest_path[robot][0]

                if selected_node in nodes_occupied:

                    print("Node occupied")
                    break
                
                else:

                    nodes_occupied.append(selected_node)
                    mqtt_payload = payload(robot,selected_node)
                    client.publish("%s/robot/task"%robot, mqtt_payload)
                    print("Robot_Id: %s moving to next waypoint."%robot)
                    robot_shortest_path = dict_of_robot_shortest_path[robot]
                    robot_shortest_path.remove(selected_node)

                time.sleep(4)
            
            if len(list_of_robots) == 0:

                print("Robots have reached their destination.")
                finish = True

            nodes_occupied.clear()

