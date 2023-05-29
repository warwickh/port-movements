import json
from datetime import datetime, timezone
import folium
from folium import plugins
from geopy import distance
import math, numpy as np
import requests
import time
import shipdata
import ast
   
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
    ship = shipdata.ShipData(db_api_url, db_api_key,map_path = '/srv/fastapi/public/index.html')
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


if __name__ == "__main__":
    main()