from rq.job import Job
from flask_restful import reqparse
from flask import Flask, abort, jsonify, request
from traffic_control_func import patrol_task
from redis_func import redis_conn, redis_queue
from flask_cors import CORS

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
        job = redis_queue.enqueue(patrol_task,input_data,job_timeout=600)
    return jsonify({"job_id": job.id})

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")

# import os
# import sys, logging
# import json
# from flask import Flask, jsonify
# # from flask import render_template
# from flask import request
# from flask_cors import CORS

# from rq import Queue
# from rq.job import Job
# from rq import get_current_job
# from worker import conn

# # from lib.word_counter import WordCounter
# from traffic_control_func import patrol_task

# q = Queue(connection=conn)
# app = Flask(__name__)
# cors = CORS(app)
# # word_counter = WordCounter()

# @app.errorhandler(404)
# def resource_not_found(exception):
#     return jsonify(error=str(exception)), 404

# @app.route('/')
# def main():
#     return "Queue is running!"

# # @app.route('/get_word_count', methods=['POST'])
# # def get_word_count():
# #     data_json = json.loads(request.data)
# #     job = q.enqueue(word_counter.count_words, data_json["sentence"])
# #     return job.key

# @app.route("/enqueue", methods=["POST"])
# def enqueue():

#     if request.method == "POST":
#         input_data = request.json
#         job = q.enqueue(patrol_task,input_data,job_timeout=600)
#     return jsonify({"job_id": job.id})

# # @app.route("/get_word_count_result/<job_key>", methods=['GET'])
# # def get_word_count_result(job_key):
# #     job_key = job_key.replace("rq:job:", "")
# #     job = Job.fetch(job_key, connection=conn)

# #     if(not job.is_finished):
# #         return "Not yet", 202
# #     else:
# #         return str(job.result), 200

# if __name__ == '__main__':
# 	# Bind to PORT if defined, otherwise default to 5000.
#     port = int(os.environ.get('PORT', 5000))
#     app.debug = True
#     app.run(host='0.0.0.0', port=port)

# import os
# import sys, logging
# import json
# from flask import Flask
# # from flask import render_template
# from flask import request
# from flask_cors import CORS

# from rq import Queue
# from rq.job import Job
# from rq import get_current_job
# from worker import conn

# from traffic_control_func import patrol_task

# q = Queue(connection=conn)
# app = Flask(__name__)
# cors = CORS(app)

# @app.route('/')
# def main():
#     return "Queue is running!"

# @app.route('/enqueue', methods=['POST'])
# def get_word_count():
#     data_json = json.loads(request.data)
#     job = q.enqueue(patrol_task, data_json)
#     return job.key

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     app.debug = True
#     app.run(host='0.0.0.0', port=port)

# @app.route("/get_word_count_result/<job_key>", methods=['GET'])
# def get_word_count_result(job_key):
#     job_key = job_key.replace("rq:job:", "")
#     job = Job.fetch(job_key, connection=conn)

#     if(not job.is_finished):
#         return "Not yet", 202
#     else:
#         return str(job.result), 200
