import json
from datetime import datetime, timezone
import folium
from folium import plugins, TileLayer
from geopy import distance
import math, numpy as np
import requests
import time
import ast
   
class ShipData:
    def __init__(self,
                 db_api_url='',
                 db_api_key='',
                 map_path='index.html',
                 debug = False):
        self.ship_data_file = 'ships.json'
        self.ship_data = None
        self.port_data = None
        self.db_api_key = db_api_key
        self.db_api_url = db_api_url
        self.map_path = map_path
        self.port_data={'AUPKL': {'Latitude': '-34.46346', 'Longitude': '150.901482691176'}, 'AUMEL': {'Latitude': '-37.81325655', 'Longitude': '144.924152576608'}, 'AUBNE': {'Latitude': '-27.385741', 'Longitude': '153.17374430786'}, 'NZAKL': {'Latitude': '-36.9323169', 'Longitude': '174.784926235455'}, 'AUFRE': {'Latitude': '-32.0307289', 'Longitude': '115.7480727'}  }
        self.home_loc = [5,46] 
        self.home_zoom = 3        
        self.world_map = folium.Map(self.home_loc, zoom_start=self.home_zoom, tiles='stamenterrain')
        #self.load_ports_from_db()

    def load_ports_from_db(self):
        url = "%s/%s"%(self.db_api_url,'port')
        response = requests.get(url)
        s = response.text
        print(response.text)
        port_data = ast.literal_eval(s.replace(':false', ':False').replace(':true', ':True'))
        for port in port_data:
            #print(port)
            self.port_data[port['port_code']]=port
        print(self.port_data)

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
    db_api_key = config["db_api_key"]
    db_api_url = config["db_api_url_local"] 
    shipdata = ShipData(db_api_url, db_api_key)
    shipdata.load_ports_from_db()
    
if __name__ == "__main__":
    main()