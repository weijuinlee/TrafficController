import json
import requests
from flask import Flask, jsonify, abort, make_response,request
from traffic_control_func import patrol_task, goto_task
# from retrieve_delete import patrol_data, goto_data, delete_task
from flask_cors import CORS
from redis_func import redis_conn, redis_queue

app = Flask(__name__)
cors = CORS(app)

@app.errorhandler(404)
def resource_not_found(exception):
    return jsonify(error=str(exception)), 404

@app.route("/")
def home():
    return "Queue is running!"

@app.route("/enqueue", methods=["POST"])
def enqueue():

    if request.method == "POST":
        
        input_data = request.json
        task_ID = input_data["taskID"]
        URL = "http://18.140.162.221:8080/editor/task/%s"%task_ID
        r = requests.get(url = URL)
        task_data = r.json()
        task_type = task_data['type']
        task_list = []
        task_list.append(task_data)
        # print(input_data)

        if task_type == 0:
            # print(task_list)
            # patrol_task(task_list)
            print("patrol")
            redis_queue.enqueue(patrol_task(task_list),job_timeout=1000000)

        if task_type == 1:

            # tasks = goto_data()
            print("Goto")
            redis_queue.enqueue(goto_task(task_list),job_timeout=1000000)

        # print(job)
        # print(task_ID)
        # URL = "http://18.140.162.221:8080/editor/task/%s"%task_ID
        # r = requests.delete(url = URL)
        # print("[Status] Task %s deleted."%task_ID)

    print("[Status] Tasks completed.")
    # return jsonify({"job_id": job.id})
    return "Scheduled tasks completed"

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0", port=3003)