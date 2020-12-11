import os
import sys, logging
import json
from flask import Flask
# from flask import render_template
from flask import request
import json
import argparse
from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
from traffic_control_func import patrol_task
from flask_cors import CORS

app = Flask(__name__)
# api = Api(app)
cors = CORS(app)

@app.route('/')
def main():
    return "Queue is running!"

@app.route('/enqueue', methods=['POST'])
def get_patrol():
    data_json = json.loads(request.data)
    patrol_task(data_json)
    return "Finished"

# if __name__ == '__main__':
#     app.run(debug=True)

if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)


# @app.route("/get_word_count_result/<job_key>", methods=['GET'])
# def get_word_count_result(job_key):
#     job_key = job_key.replace("rq:job:", "")
#     job = Job.fetch(job_key, connection=conn)

#     if(not job.is_finished):
#         return "Not yet", 202
#     else:
#         return str(job.result), 200

# if __name__ == '__main__':
# 	# Bind to PORT if defined, otherwise default to 5000.
#     port = int(os.environ.get('PORT', 5000))
#     app.debug = True
#     app.run(host='0.0.0.0', port=port)

# from flask import Flask  
# from filmService import film_api  
  
# app = Flask(__name__)  
# app.register_blueprint(film_api, url_prefix='/film_api')  
 
# @app.route("/")  
# def service():  
#     return "Service is running!"  
  
# if __name__ == "__main__":  
#     app.run()  

# from flask import Flask, request
# from flask_restful import Resource, Api
# from json import dumps

# app = Flask(__name__)
# api = Api(app)

# api.add_resource(Departments_Meta, '/departments')  # bind url identifier to class
# api.add_resource(Departmental_Salary, '/dept/<string:department_name>')  # bind url identifier to class; also make it querable
# api.add_resource(multiply, '/multiply/<int:number>')  # whatever the number is, multiply by 2


# from flask import Flask
# app = Flask(__name__)

# @app.route('/patrol')
# def patrol_task():
#     patrol_task

# if __name__ == '__main__':
#     app.run()