import folium
import os 
import json
from datetime import datetime, timezone
from folium import plugins 

class PlotMap:
    def __init__(self,
                debug = False):
        self.ship_data_file = 'ships.json'
        self.ship_data = None
        self.load_ships()
        self.world_map = folium.Map([30, 0], zoom_start=3)
        
    def set_data(self, ship_data):
        self.ship_data = ship_data
        
    def load_ships(self):
        try:
            with open(self.ship_data_file) as f:
                self.ship_data = json.load(f)
        except:
            print("File not available %s"%self.ship_data_file)
        
    def plot_all(self):
        self.load_ships()
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
                trav_time = (millis/(1000*60*60))%24
                if trav_time > (7*24): #Old data will be red
                    color = '#f88'
                else:
                    color = '#8f8'
                #print(name)
                self.plot_ship(name, last_lat, last_lon, heading, trav_speed, color)
            except:
                pass 
        self.world_map.save('index.html')
    
    def plot_ship(self, name, lat, lon, heading, speed, color):
        print("Plotting: %s"%name)
        plugins.BoatMarker(
            popup = "%s(%.2fkn,%.2f°)"%(name,speed,heading),
            location=(lat, lon),
            heading=heading,
            color=color
        ).add_to(self.world_map)

def main():
    plotmap = PlotMap()
    plotmap.plot_all()

if __name__ == "__main__":
    main()