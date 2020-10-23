from rq.job import Job
from flask_restful import reqparse
from flask import Flask, abort, jsonify, request
from traffic_control_func import send_coordinates
from redis_func import redis_conn, redis_queue

app = Flask(__name__)

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
        job = redis_queue.enqueue(send_coordinates,input_data)
    return jsonify({"job_id": job.id})

if __name__ == "__main__":
    app.run(debug=True)
