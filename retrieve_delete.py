import requests
import time
import json

def patrol_data():

    URL = "https://go-patrol.herokuapp.com/editor/task/patrol"
    r = requests.get(url = URL)
    patrol_data = r.json()
    
    try:
        
        result = patrol_data[:2]
                
        return result

    except:

        return None

    # if len(result) > 0:

    #     return result

def goto_data():

    URL = "https://go-patrol.herokuapp.com/editor/task/goto"
    r = requests.get(url = URL)
    goto_data = r.json()
    # print(goto_data)
    # print(patrol_route)
    result = goto_data[0]
    return result

def delete_task(tasks):

    for task in tasks:

        task_id = str(task["id"])
        URL = "https://go-patrol.herokuapp.com/editor/task/%s"%task_id
        r = requests.delete(url = URL)
        print("[Status] Task %s deleted."%task_id)

