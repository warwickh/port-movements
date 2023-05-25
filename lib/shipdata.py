import json
from datetime import datetime, timezone
import folium
from folium import plugins
from geopy import distance
import math, numpy as np
import requests
   
class ShipData:
    def __init__(self,
                 db_api_url='',
                 db_api_key='',
                 debug = False):
        self.ship_data_file = 'ships.json'
        self.ship_data = None
        self.db_api_key = db_api_key
        self.db_api_url = db_api_url
        self.port_data={'AUPKL': {'Latitude': '-34.46346', 'Longitude': '150.901482691176'}, 'AUMEL': {'Latitude': '-37.81325655', 'Longitude': '144.924152576608'}, 'AUBNE': {'Latitude': '-27.385741', 'Longitude': '153.17374430786'}, 'NZAKL': {'Latitude': '-36.9323169', 'Longitude': '174.784926235455'}, 'AUFRE': {'Latitude': '-32.0307289', 'Longitude': '115.7480727'}  }
        self.home_loc = [5,46] 
        self.home_zoom = 3        
        self.world_map = folium.Map(self.home_loc, zoom_start=self.home_zoom)
        self.load_ships()

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
        if str(ais_message['UserID']) in self.ship_data.keys():
            #print(ais_message)
            #self.update_location_by_mmsi(ais_message['UserID'], ais_message['Latitude'], ais_message['Longitude'])
            ship = self.ship_data[str(ais_message['UserID'])]
            d = datetime.now()
            unixtime = int(round(datetime.timestamp(d)))
            print("%s %skn %s°"%(ship["SHIPNAME"],str(ais_message['Sog']), str(ais_message['TrueHeading'])))
            ship["UPDATED"] = str(unixtime)
            ship["LAT"] = str(ais_message['Latitude'])
            ship["LON"] = str(ais_message['Longitude'])
            ship["SPEED"] = str(ais_message['Sog'])
            ship["DIR"] = str(ais_message['TrueHeading'])
            self.ship_data[str(ais_message['UserID'])] = ship
            ship['MMSI'] = str(ais_message['UserID'])
            ais_message['Timestamp'] = str(unixtime)[:-3]
            #self.post_data('update_ais/', ais_message)
            self.post_data('last_pos/', ship)
            self.save_ships()
            self.plot_all()

    def update_location_by_name(self, name, lat, lon):
        for mmsi, ship in self.ship_data.items():
            if ship['SHIPNAME']==name:
                #print("Update %s %s %s"%(mmsi, lat, lon))
                self.update_location_by_mmsi(mmsi, lat, lon)     
      
    def update_location_by_mmsi(self, mmsi, lat, lon):
        ship = self.ship_data[str(mmsi)]
        d = datetime.now()
        unixtime = int(round(datetime.timestamp(d)))
        try:
            last_time = float(ship["UPDATED"][0:10])
            last_lat = float(ship["LAT"])
            last_lon = float(ship["LON"])
            trav_dist = distance.distance((last_lat, last_lon),(lat, lon)).km
            seconds = int(round(unixtime))-int(round(last_time))
            trav_time = (seconds/(60*60))%24
            trav_speed = trav_dist/trav_time
            trav_dir = self.get_bearing(last_lat, last_lon, lat, lon)
        except:
            trav_dist = 0
            trav_time = 0
            trav_speed = 0
            trav_dir = 0
        print("%s %skn %s°"%(ship["SHIPNAME"],str(trav_speed/1.852), trav_dir))
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
        self.world_map = folium.Map(self.home_loc, zoom_start=self.home_zoom)
        self.plot_ports()
        for mmsi in self.ship_data.keys():
            try:
                ship = self.ship_data[mmsi]
                #print(ship)
                name = ship["SHIPNAME"]
                last_time = float(ship["UPDATED"][0:10])
                last_lat = float(ship["LAT"])
                last_lon = float(ship["LON"])
                trav_speed = float(ship["SPEED"])
                heading = float(ship["DIR"])
                d = datetime.now()
                unixtime = int(round(datetime.timestamp(d)))
                seconds = int(round(unixtime))-int(round(last_time)) 
                age = (seconds/(60*60))
                #print("%s %s %s"%(int(round(unixtime)),int(round(last_time)), seconds/(60*60)))
                #print("%s %s"%(name, age))
                self.plot_ship(name, last_lat, last_lon, heading, trav_speed, age)
            except:
                pass 
        self.world_map.save('index.html')

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
    shipdata = ShipData()
    #shipdata.locate_ship_in_port("HOEGH BANGKOK", "AUPKL")
    #shipdata.locate_ship_in_port("HOEGH CHIBA", "AUBNE")
    #shipdata.locate_ship_in_port("HOEGH TOKYO", "AUFRE")

if __name__ == "__main__":
    main()