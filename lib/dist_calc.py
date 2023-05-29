import json
from datetime import datetime, timezone
import folium
from folium import plugins
from geopy import distance
import math, numpy as np
import requests
import time
import shipdata, portdata
import ast

def get_dist(lat1, lon1, lat2, lon2):
    return_val = distance.distance((lat1, lon1),(lat2, lon2)).km
    return return_val
   
def get_ais(db_api_url, db_api_key):
    url = "%s/%s"%(db_api_url,'ais')
    print(url)
    if db_api_key:
        headers = {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer %s'%db_api_key
        }
    else:
        headers = {'Content-Type': 'application/json'}
    response = requests.get(url, headers=headers)
    s = response.text
    return_val = ast.literal_eval(s.replace(':false', ':False').replace(':true', ':True'))
    print(return_val)
    return return_val


def load_json_config(config_filename):
    config = None
    with open(config_filename, "r") as jsonfile:
        try:
            config = json.load(jsonfile)
        except Exception as exc:
            print(exc)
    return config
    
def main():
    config_filename = 'config.json'
    config = load_json_config(config_filename)
    ais_api_key = config["ais_api_key"]
    db_api_key = config["db_api_key"]
    db_api_url = config["db_api_url"] 
    shipsession = shipdata.ShipData(db_api_url, db_api_key)
    portsession = portdata.PortData(db_api_url, db_api_key)
    ship_data = shipsession.get_data()
    ports = portsession.get_ports()
    
    for mmsi in ship_data:
        ship = ship_data[mmsi]
        if ship['UPDATED']!=0:
            lat = ship['LAT']
            lon = ship['LON']
            name = ship['SHIPNAME']
            min_dist = 999999
            closest_port=""
            for port in ports:
                dist = get_dist(port['lat'],port['lon'], lat, lon)
                #print(dist)
                if dist<min_dist:
                    min_dist = dist
                    closest_port=port['port_code']
            print("Closest port to %s is %s at %skm"%(name, closest_port, min_dist)) 
            print(min_dist)
            print(closest_port)
            """
            history = get_ais(db_api_url, db_api_key)
            print(history)
            print(type(history))
            for message in history:
                d = datetime.now()
                last_time = message['Timestamp']
                unixtime = int(round(datetime.timestamp(d)))
                seconds = int(round(unixtime))-int(round(last_time)) 
                age = (seconds/(60*60))
                print(age)
                ship.process_pos_report(message)
            """

if __name__ == "__main__":
    main()