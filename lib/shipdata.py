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
        self.db_api_key = db_api_key
        self.db_api_url = db_api_url
        self.map_path = map_path
        self.port_data={'AUPKL': {'Latitude': '-34.46346', 'Longitude': '150.901482691176'}, 'AUMEL': {'Latitude': '-37.81325655', 'Longitude': '144.924152576608'}, 'AUBNE': {'Latitude': '-27.385741', 'Longitude': '153.17374430786'}, 'NZAKL': {'Latitude': '-36.9323169', 'Longitude': '174.784926235455'}, 'AUFRE': {'Latitude': '-32.0307289', 'Longitude': '115.7480727'}  }
        self.home_loc = [5,46] 
        self.home_zoom = 3        
        self.world_map = folium.Map(self.home_loc, zoom_start=self.home_zoom, tiles='stamenterrain')
        self.load_ships()
        self.load_ships_from_db()

    def set_map_zoom(self, zoom):
        try:
            self.home_zoom = int(zoom)
        except:
            pass

    def set_data(self, ship_data):
        self.ship_data = ship_data
        self.save_ships()
        
    def get_data(self):
        return self.ship_data
        
    def get_ship(self, mmsi):
        return self.ship_data[str(mmsi)]

    def ships_to_db(self):
        self.align_fields()
        for mmsi in self.ship_data.keys():
            ship = self.ship_data[mmsi]
            #print(ship)
            print("Sending %s"%ship)
            #print(self.post_data('last_pos/', ship))
            #time.sleep(2)

    def align_fields(self):
        ship_data = {}
        for mmsi in self.ship_data.keys():
            ship = self.ship_data[mmsi]
            try:
                ship['UPDATED'] = int(str(ship['UPDATED'])[:10])
            except:
                ship['UPDATED'] = 0
            ship['MMSI'] = int(mmsi)
            try:
                ship["LAT"] = float(ship["LAT"])
            except:
                ship["LAT"] = 0
            try:
                ship["LON"] = float(ship["LON"])
            except:
                ship["LON"] = 0
            try:
                ship["SPEED"] = float(ship["SPEED"])
            except:
                ship["SPEED"] = 0
            try:
                ship["DIR"] = int(round(ship["DIR"]))
            except:
                ship["DIR"] = 0
            ship_data[int(mmsi)] = ship
        #print(ship_data)
        self.ship_data = ship_data
        self.save_ships()
        
    def load_ships_from_db(self):
        url = "%s/%s"%(self.db_api_url,'last_pos')
        response = requests.get(url)
        s = response.text
        #print(response)
        #print(response.text)
        last_pos = ast.literal_eval(s.replace(':false', ':False').replace(':true', ':True').replace('null', 'None'))
        for ship in last_pos:
            #print(ship)
            self.ship_data[ship['MMSI']]=ship
        
    def load_ships(self):
        try:
            #print("Opening %s"%self.ship_data_file)
            with open(self.ship_data_file) as f:
                self.ship_data = json.load(f)
                self.align_fields()
                #ship['UPDATED'] = ship['UPDATED'][:10]
                #ship['MMSI'] = mmsi
        except:
            print("File not available %s"%self.ship_data_file)
        #self.load_ships_from_db()

    def save_ships(self):
        if self.ship_data is not None:
            with open(self.ship_data_file, 'w') as f:
                f.write(json.dumps(self.ship_data, indent=4))

    def get_bearing(self, lat1, lon1, lat2, lon2):
        #print("Getting bearing from %s %s %s %s"%(lat1, lon1, lat2, lon2))
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

    def post_data(self, post_url, message):
        url = "%s/%s"%(self.db_api_url,post_url)
        #print(url)
        headers = {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer %s'%self.db_api_key
        }
        response = requests.post(url, headers=headers, json=message)
        #print(response)
        return (response.status_code == 200)
    
    def process_pos_report(self, ais_message):
        #print(int(ais_message['UserID']))
        if int(ais_message['UserID']) in self.ship_data.keys():
            ship = self.ship_data[int(ais_message['UserID'])]
            d = datetime.now()
            unixtime = int(round(datetime.timestamp(d)))
            print("%s %skn %s°"%(ship["SHIPNAME"],str(ais_message['Sog']), str(ais_message['TrueHeading'])))
            ship["UPDATED"] = str(unixtime)
            ship["LAT"] = float(ais_message['Latitude'])
            ship["LON"] = float(ais_message['Longitude'])
            ship["SPEED"] = float(ais_message['Sog'])
            ship["DIR"] = int(ais_message['TrueHeading'])
            self.ship_data[int(ais_message['UserID'])] = ship
            ship['MMSI'] = int(ais_message['UserID'])
            ais_message['Timestamp'] = unixtime
            #self.post_data('update_ais/', ais_message)
            print(ship)
            self.post_data('last_pos/', ship)
            self.save_ships()
            self.plot_all()
    
    def plot_all(self):
        self.load_ships()
        self.world_map = folium.Map(self.home_loc, zoom_start=self.home_zoom, tiles='stamenterrain')
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
                unixtime = int(round(datetime.timestamp(d)))
                seconds = int(round(unixtime))-int(round(last_time)) 
                age = (seconds/(60*60))
                #print("%s %s %s"%(int(round(unixtime)),int(round(last_time)), seconds/(60*60)))
                #print("%s %s %s %s"%(name, age, last_lat, last_lon))
                if last_lat!=0 and last_lon!=0:
                    #print("Plotting %s at %s %s"%(name, last_lat, last_lon))
                    self.plot_ship(name, last_lat, last_lon, heading, trav_speed, age)
                else:                
                    #print("Skipping %s at %s %s"%(name, last_lat, last_lon))
                    #print(ship)
                    pass
            except:
                pass 
        self.world_map.save(self.map_path)

    def locate_ship_in_port(self, shipname, port):
        lat = self.port_data[port.upper()]['Latitude']
        lon = self.port_data[port.upper()]['Longitude']
        self.update_location_by_name(shipname.upper(), lat, lon)

    def plot_ports(self):
        for port in self.port_data.keys():
            self.plot_port(port, self.port_data[port]['Latitude'],  self.port_data[port]['Longitude'])
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

def load_json_config(config_filename):
    config = None
    with open(config_filename, "r") as jsonfile:
        try:
            config = json.load(jsonfile)
        except Exception as exc:
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
                #ship['IMO'] = i['IMO']
                mmsi_data[mmsi] = ship
    print(mmsi_data)
    return mmsi_data

def main():
    config_filename = 'config.json'
    config = load_json_config(config_filename)
    db_api_key = config["db_api_key"]
    db_api_url = config["db_api_url"] 
    shipdata = ShipData(db_api_url, db_api_key)
    #shipdata.ships_to_db()
    #shipdata.locate_ship_in_port("HOEGH BANGKOK", "AUPKL")
    #shipdata.locate_ship_in_port("HOEGH CHIBA", "AUBNE")
    #shipdata.locate_ship_in_port("HOEGH TOKYO", "AUFRE")

if __name__ == "__main__":
    main()