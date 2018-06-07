#!flask/bin/python
import os
import json
import random, string
from pprint import pprint
from flask import Flask, jsonify, render_template, url_for
from flask import abort
from flask import make_response
from flask import request
from DataManager import DataManager
import configparser

#datafile = '/home/pi/time-attendence/dati.json'
#jsonfile = open(datafile, 'a+')
#data = json.load(jsonfile)


app = Flask(__name__)

config = configparser.ConfigParser()
config.read("defaults.ini")


@app.route('/classes', methods=['GET'])
def get_all():
    return jsonify(DataManager().get_all_data())

@app.route('/classes/<node>', methods=['GET'])
def get_node(node):
    res = DataManager().get_node(node, request.json)
    
    return jsonify(res)
    
@app.route('/classes/<node>/<row_id>', methods=['GET'])
def get_node_id(node,row_id):
    r = DataManager().get_object_for_id(node,row_id)
    
    if len(r) == 0:
        abort(404)
    
    return jsonify({'result' : r[0]})

@app.route('/classes/<node>', methods=['POST'])
def create(node):
    if not request.json:
        abort(400)

    return jsonify(DataManager().add_row(node,request.json))

@app.route('/classes/<node>/<row_id>', methods=['PUT'])
def update(node,row_id):
    if not request.json:
        abort(400)
    
    return jsonify(DataManager().edit_row(node,row_id,request.json))

@app.route('/classes/<node>/<row_id>', methods=['DELETE'])
def delete(node,row_id):
    return jsonify(DataManager().delete(node,row_id))

@app.route('/classes/<node>/dump/<mode>', methods=['POST'])
def import_logs_dump(node, mode):
    if not request.json:
        return jsonify({"resp" : "error"})
    ids = request.json["ids"]
    print("mode=" + mode + " , " + str(ids))
    for id in ids:
        if mode == "delete":
            DataManager().delete(node,id)
        if mode == "edit":
            DataManager().edit_row(node,id,{"downloaded" : "1"})
    return jsonify({"resp" : "ok"})

@app.route('/classes/logs/<mode>', methods=['GET'])
def import_logs(mode):
    edit = False
    if request.json:
        for key,value in request.items():
            if key == "edit":
                if value == "1":
                    edit = True
    return jsonify(DataManager().import_logs(mode, edit))

@app.route('/device/name', methods=['GET'])
def device_name():
    name = config["SETTINGS"]["devicename"]
    print(name)
    return jsonify({"name":str(name)})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(500)
def internal_error(error):
    return make_response(jsonify({'error': 'Internal Server Error'}), 500)

@app.route('/')
def index():
    return "Time Attendence Rest API"

def randomword(length):
   return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

def runserver():
    app.use_reloader = False
    app.run(debug=False, host='0.0.0.0')
    
if __name__ == '__main__':
    runserver()
    
