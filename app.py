import json
from flask import Flask, jsonify, abort, make_response,request
from traffic_control_func import patrol_task
from retrieve_delete import patrol_data, goto_data, delete_task
from flask_cors import CORS
from redis_func import redis_conn, redis_queue
# from multiprocessing import Process

# app = Flask(__name__)
# cors = CORS(app)

# @app.route('/')
# def main():
#     return "App is running!"

# @app.route('/schedule/task', methods=['POST'])
# def create_task():
#     if not request.json:
#         about(400)
#     data = request.json
#     patrol_task(data)
#     return "Task completed."

# @app.route("/task", methods=['POST'])
# def task():
#     print(request.json)
#     body_job_id = request.json.get("job_id")
#     body_operator = request.json.get("operator")
#     if is_valid_request(body_job_id, body_operator) == False:
#         return "Bad request, invalid job_id: %s or operator: %s" % (body_job_id, body_operator), 401

#     task_cb = Process(target=run_task, args=( body_job_id, body_operator))
#     task_cb.start()
#     return "Job_id received!", 202

# @app.errorhandler(404)
# def not_found(error):
#     return make_response(jsonify({'error': 'Not found'}), 404)

# if __name__ == '__main__':
# 	app.run(debug=True,host="0.0.0.0", threaded=True)

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
        task_type = input_data["type"]

        if task_type == 0:

            tasks = patrol_data()

            if tasks != None:

                delete_task(tasks)
                job = redis_queue.enqueue(patrol_task(tasks),job_timeout=1000000)

            else:

                return "No scheduled task to be executed."

        if task_type == 1:

            tasks = goto_data()

            if tasks != None:

                delete_task(tasks)
                job = redis_queue.enqueue(goto_task(tasks),job_timeout=1000000)

            else:

                return "No scheduled task to be executed."

    print("[Status] Tasks completed.")
    # return jsonify({"job_id": job.id})
    return "Scheduled tasks completed"

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")