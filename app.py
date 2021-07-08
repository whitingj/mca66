#!/usr/bin/env python
from flask import Flask, jsonify
from mca66 import MCA66Command as mca66
from flask_cors import CORS  # The typical way to import flask-cors
from flask import request
import serial 

app = Flask(__name__, 
    static_url_path='', 
    static_folder='static')
cors = CORS(app)

def execute_command(command):
  ser = ser_connect()
  result_json = ser_execute(ser, command)
  ser_close(ser)
  return result_json
  
def ser_connect():
  port = "/dev/ttyUSB0"
  ser = serial.Serial(port, 38400, timeout=2)
  return ser

def ser_execute(ser, command):
  result = command.execute(ser)
  return result.json_data()

def ser_close(ser):
  ser.close()

@app.route('/')
def index():   
  return app.send_static_file('audio.html')

@app.route('/status')
def status():
  command = mca66.get_zone_state()
  return jsonify(execute_command(command))

@app.route('/zone/<int:zone_id>/power', methods=['PUT'])
def zone_power(zone_id):
  if request.values['power'] == '1':
    power = True
  else:
    power = False
  print zone_id, "setting power to", power
  command = mca66.set_power(zone_id, power)
  return jsonify(execute_command(command))
  #return "" 

@app.route('/zone/<int:zone_id>/volume', methods=['PUT'])
def zone_volume(zone_id):
  ser = ser_connect()
  command = mca66.get_zone_state()
  zone_state = ser_execute(ser, command)
  current_volume = zone_state[zone_id]['volume']
  volume = int(request.values['volume'])
  if current_volume < volume:
    while current_volume < volume:
      command = mca66.vol_up(zone_id)
      zone_state = ser_execute(ser, command)
      current_volume = zone_state[zone_id]['volume']
      #print "+", current_volume, "desired", volume
  else:
    while current_volume > volume:
      command = mca66.vol_down(zone_id)
      zone_state = ser_execute(ser, command)
      current_volume = zone_state[zone_id]['volume']
      #print "-", current_volume, "desired", volume
  ser_close(ser)
  return jsonify(zone_state)

@app.route('/zone/<int:zone_id>/input', methods=['PUT'])
def zone_input(zone_id):
  input = request.values['input']
  command = mca66.set_input(zone_id, input)
  return jsonify(execute_command(command))

if __name__ == '__main__':
    #app.run(port=8080, debug = True, host='0.0.0.0')
    app.run(port=8080, host='0.0.0.0')
