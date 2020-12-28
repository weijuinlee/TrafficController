import json
from flask import Flask, jsonify, abort, make_response,request
from traffic_control_func import patrol_task
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app)

@app.route('/')
def main():
    return "App is running!"

@app.route('/schedule/task', methods=['POST'])
def create_task():
    if not request.json:
        about(400)
    data = request.json
    patrol_task(data["taskDetails"])
    return "Task completed."

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True)