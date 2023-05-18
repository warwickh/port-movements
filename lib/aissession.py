import asyncio
import websockets
import json
from datetime import datetime, timezone
import json
import yaml
from geopy import distance
import math, numpy as np
import folium
from folium import plugins 
   
class AisSession:
    def __init__(self,
                 ais_api_key='',
                 debug = False):
        self.ais_api_key = ais_api_key
        self.baseUrl = "https://qships.tmr.qld.gov.au/webx/"
        self.ship_data_file = 'ships.json'
        self.ship_data = None
        self.world_map = folium.Map([30, 0], zoom_start=3)
        self.load_ships()
        asyncio.run(self.connect_ais_stream())

    def set_data(self, ship_data):
        self.ship_data = ship_data
        
    def load_ships(self):
        try:
            with open(self.ship_data_file) as f:
                self.ship_data = json.load(f)
        except:
            print("File not available %s"%self.ship_data_file)

    def save_ships(self):
        if self.ship_data is not None:
            with open(self.ship_data_file, 'w') as f:
                f.write(json.dumps(self.ship_data, indent=4))

    def get_bearing(self, lat1, lon1, lat2, lon2):
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)
        dLon = lon2 - lon1;
        y = math.sin(dLon) * math.cos(lat2);
        x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon);
        brng = np.rad2deg(math.atan2(y, x));
        if brng < 0: brng+= 360
        return brng

    def update_location(self, mmsi, lat, lon):
        ship = self.ship_data[str(mmsi)]
        d = datetime.now()
        unixtime = int(round(datetime.timestamp(d)*1000))
        try:
            last_time = float(ship["UPDATED"])
            last_lat = float(ship["LAT"])
            last_lon = float(ship["LON"])
            trav_dist = distance.distance((last_lat, last_lon),(lat, lon)).km
            millis = int(round(unixtime))-int(round(last_time))
            trav_time = (millis/(1000*60*60))%24
            trav_speed = trav_dist/trav_time
            trav_dir = self.get_bearing(last_lat, last_lon, lat, lon)
        except:
            trav_dist = 0
            trav_time = 0
            trav_speed = 0
            trav_dir = 0
        print("Speed %s knts"%str(trav_speed/1.852))
        print("Dir: %s"%trav_dir)
        ship["UPDATED"] = str(unixtime)
        ship["LAT"] = str(lat)
        ship["LON"] = str(lon)
        ship["SPEED"] = str(trav_speed/1.852)
        ship["DIR"] = str(trav_dir)
        self.ship_data[str(mmsi)] = ship
        self.save_ships()
        self.plot_all()
       
    def plot_all(self):
        self.load_ships()
        self.world_map = folium.Map([30, 0], zoom_start=3)
        self.plot_ports()
        for mmsi in self.ship_data.keys():
            try:
                ship = self.ship_data[mmsi]
                #print(ship)
                name = ship["SHIPNAME"]
                last_time = float(ship["UPDATED"])
                last_lat = float(ship["LAT"])
                last_lon = float(ship["LON"])
                trav_speed = float(ship["SPEED"])
                heading = float(ship["DIR"])
                d = datetime.now()
                unixtime = int(round(datetime.timestamp(d)*1000))
                millis = int(round(unixtime))-int(round(last_time)) 
                age = (millis/(1000*60*60))
                #print("%s %s %s"%(int(round(unixtime)),int(round(last_time)), millis/(1000*60*60)))
                #print("%s %s"%(name, age))
                self.plot_ship(name, last_lat, last_lon, heading, trav_speed, age)
            except:
                pass 
        self.world_map.save('index.html')

    def plot_ports(self):
        port_data={'AUPKL': {'Latitude': '-34.46346', 'Longitude': '150.901482691176'}, 'AUMEL': {'Latitude': '-37.81325655', 'Longitude': '144.924152576608'}, 'AUBNE': {'Latitude': '-27.385741', 'Longitude': '153.17374430786'}, 'NZAKL': {'Latitude': '-36.9323169', 'Longitude': '174.784926235455'}, 'AUFRE': {'Latitude': '-32.0307289', 'Longitude': '115.7480727'}  }  
        for port in port_data.keys():
            self.plot_port(port, port_data[port]['Latitude'],  port_data[port]['Longitude'])
        return    

    def plot_port(self, name, lat, lon):
        folium.Marker(
            popup = "%s"%(name),
            location=(lat, lon),
        ).add_to(self.world_map)
    
    def plot_ship(self, name, lat, lon, heading, speed, age):
        #print("Plotting: %s"%name)
        if age > (2*24): #2d Old data will be red
            color = '#f88'
        else:
            color = '#8f8'
        plugins.BoatMarker(
            popup = "%s(%.2fkn,%.2f°) %d h"%(name,speed,heading, age),
            location=(lat, lon),
            heading=heading,
            color=color
        ).add_to(self.world_map)
        
    async def connect_ais_stream(self):
        async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
            subscribe_message = {"APIKey": self.ais_api_key, "BoundingBoxes": [[[-180, -90], [180, 90]]]}
            subscribe_message_json = json.dumps(subscribe_message)
            await websocket.send(subscribe_message_json)

            async for message_json in websocket:
                message = json.loads(message_json)
                message_type = message["MessageType"]
                if message_type == "PositionReport":
                    ais_message = message['Message']['PositionReport']
                    if str(ais_message['UserID']) in self.ship_data.keys():
                        #print(ais_message)
                        print(f"[{datetime.now(timezone.utc)}] ShipName: {self.ship_data[str(ais_message['UserID'])]['SHIPNAME']} ShipId: {ais_message['UserID']} Latitude: {ais_message['Latitude']} Longitude: {ais_message['Longitude']}")
                        self.update_location(ais_message['UserID'], ais_message['Latitude'], ais_message['Longitude'])

def load_config(config_filename):
    config = None
    with open(config_filename, "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return config

def init_load_ships():
    with open('mt_ships.json') as f:
        data = json.load(f)
        mmsi_data = {}
        #print(data)
        for i in data['data']:
            if "HOEGH" in i['SHIPNAME'].upper() and int(i['MMSI'])>0:
                #print("%s %s"%(i['SHIPNAME'], i['MMSI']))
                ship = {}
                mmsi = i['MMSI']
                shipname = i['SHIPNAME']
                ship['SHIPNAME'] = i['SHIPNAME']
                ship['LAT'] = ""
                ship['LON'] = ""
                ship['IMO'] = i['IMO']
                mmsi_data[mmsi] = ship
    print(mmsi_data)
    return mmsi_data

def main():
    config_filename = 'config.yml'
    config = load_config(config_filename)
    ais_api_key = config["ais_api_key"]
    aissession = AisSession(ais_api_key)
    aissession.set_data(init_load_ships())
    aissession.save_ships()

if __name__ == "__main__":
    main()