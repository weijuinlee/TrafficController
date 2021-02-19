from flask import Flask, abort, jsonify, request
from rq.job import Job
import requests
from .functions import patrol_task, goto_task
from .redis_resc import redis_conn, redis_queue

app = Flask(__name__)

@app.errorhandler(404)
def resource_not_found(exception):

    return jsonify(error=str(exception)), 404


@app.route("/")
def home():

    return "Running!"


@app.route("/enqueue", methods=["POST", "GET"])
def enqueue():

    if request.method == "GET":
        query_param = request.args.get("external_id")
        if not query_param:
            abort(
                404,
                description=(
                    "No query parameter external_id passed. "
                    "Send a value to the external_id query parameter."
                ),
            )
        data = {"external_id": query_param}

    if request.method == "POST":

        data = request.json
        task_ID = data["taskID"]
        URL = "http://18.140.162.221:8080/editor/task/%s"%task_ID
        r = requests.get(url = URL)
        task_data = r.json()
        task_type = task_data['type']
        task_list = []
        task_list.append(task_data)

        if task_type == 0:

            job = redis_queue.enqueue(patrol_task, task_list, job_timeout=1000000)

        if task_type == 1:

            job = redis_queue.enqueue(goto_task, task_list, job_timeout=1000000)

    # job = redis_queue.enqueue(some_long_function, data)
    return jsonify({"job_id": job.id})


@app.route("/check_status")
def check_status():

    job_id = request.args["job_id"]

    try:

        job = Job.fetch(job_id, connection=redis_conn)

    except Exception as exception:

        abort(404, description=exception)

    return jsonify({"job_id": job.id, "job_status": job.get_status()})


@app.route("/get_result")
def get_result():

    job_id = request.args["job_id"]

    try:

        job = Job.fetch(job_id, connection=redis_conn)

    except Exception as exception:

        abort(404, description=exception)

    if not job.result:
        abort(
            404,
            description=f"No result found for job_id {job.id}. Try checking the job's status.",
        )
    return jsonify(job.result)

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0",port=3003)
