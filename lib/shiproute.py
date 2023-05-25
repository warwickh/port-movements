#!/usr/bin/env python3
"""

"""
import requests 
from bs4 import BeautifulSoup 
import pickle
from datetime import datetime, date, timezone, timedelta
import time
import os
import urllib.parse 
import csv
import random
import re
import pandas as pd
import json
import folium
from folium import plugins

class ShipRoute:
    def __init__(self,
                 sessionFile='shiproute_session.dat',
                 maxSessionTimeSeconds = 60 * 30,
                 agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                 debug = False):
        self.port_data = {
            'NZAKL': {'name': 'Port of Auckland, New Zealand', 'url': 'port-of-auckland,new-zealand'}, 
            'ESSDR': {'name': 'Port of Santander, Spain', 'url': 'port-of-santander,spain'}, 
            'BEANR': {'name': 'Port of Antwerp, Belgium', 'url': 'port-of-antwerp,belgium'}, 
            'AUMEL': {'name': 'Port of Melbourne, Australia', 'url': 'port-of-melbourne,australia'}, 
            'AUPKL': {'name': 'Port Kembla , Australia', 'url': 'port-kembla,australia'}, 
            'AUBNE': {'name': 'Port of Brisbane, Australia', 'url': 'port-of-brisbane,australia'}, 
            'AUFRE': {'name': 'Port of Fremantle (Perth), Australia', 'url': 'port-of-fremantle-perth,australia'}}
        self.origins = ['ESSDR', 'BEANR']
        self.destinations = ['NZAKL','AUMEL','AUPKL','AUBNE','AUFRE']
        self.routes = {}
        self.baseUrl = "http://ports.com/sea-route/"
        self.dataUrl = "http://ports.com/aj/sea-route/"
        self.debug = debug
        self.maxSessionTime = maxSessionTimeSeconds  
        self.sessionFile = sessionFile
        self.userAgent = agent
        self.get_session()
        self.refresh_all()

    def modification_date(self, filename):
        """
        return last file modification date as datetime object
        """
        t = os.path.getmtime(filename)
        return datetime.fromtimestamp(t)
        
    def get_session(self):
        wasReadFromCache = False
        if self.debug:
            print('loading or generating session...')
        if os.path.exists(self.sessionFile):
            time = self.modification_date(self.sessionFile)         
            lastModification = (datetime.now() - time).seconds
            if lastModification < self.maxSessionTime:
                with open(self.sessionFile, "rb") as f:
                    self.session = pickle.load(f)
                    wasReadFromCache = True
                    if self.debug:
                        print("loaded session from cache (last access %ds ago) "%lastModification)
        if not wasReadFromCache:
            self.session = requests.Session()
            self.session.headers.update({'user-agent' : self.userAgent})
            if self.debug:
                print('created new session')
            self.saveSessionToCache()

    def saveSessionToCache(self):
        with open(self.sessionFile, "wb") as f:
            pickle.dump(self.session, f)
            if self.debug:
                print('updated session cache-file %s' % self.sessionFile)

    def retrieveContent(self, url, method = "get", postData = None):
        if method == 'get':
            res = self.session.get(url)
        else:
            #res = self.session.post(url , data = postData)
            res = self.session.post(url , json = postData)
        self.saveSessionToCache()            
        return res

    def get_route(self, origin, dest):
        route_name = "%s_%s"%(origin, dest)
        return self.routes[route_name]
     
    def refresh_route(self, origin, dest):
        res = self.retrieveContent(self.baseUrl)
        #print(res.cookies)
        url = "http://ports.com/aj/sea-route/?a=0&amp;b=0&amp;c=%s&amp;d=%s"%(self.port_data[origin]['name'].split(',')[0],self.port_data[dest]['name'].split(',')[0])
        headers = {
            "accept": "application/json, text/javascript, */*",
            "accept-language": "en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "proxy-connection": "keep-alive",
            "x-requested-with": "XMLHttpRequest",
            "Referer": "http://ports.com/sea-route/",
            "Referrer-Policy": "strict-origin-when-cross-origin"
          }
        self.session.headers.update(headers)
        res = self.retrieveContent(url)
        #print(res)
        #print(res.text)
        data = res.json()
        return data                    

    def flatten(self,lst):
        if isinstance(lst, list):
            if isinstance(lst[0], list):
                for v in lst:
                    yield from self.flatten(v)
            else:
                yield lst

    def flip_points(self, points):
        new_points = []
        for point in self.flatten(points):
            new_points.append([point[1],point[0]])
        return new_points
       
    def refresh_all(self):
        for origin in self.origins:#self.port_data:
            for dest in self.destinations:
                route_name = "%s_%s"%(origin, dest)
                route_filename = "%s.json"%route_name
                if os.path.isfile(route_filename):
                    print("File exists, loading %s"%route_filename)
                    with open(route_filename, "r") as infile:
                        data = json.load(infile)
                else:
                    data = self.refresh_route(origin, dest)
                    json_object = json.dumps(data, indent=4)
                    with open(route_filename, "w") as outfile:
                        outfile.write(json_object)
                route = {'dist': data['cost']['kms'], 'days_at_sea': data['days_at_sea'], 'points': self.flip_points(data['route'])}
                self.routes[route_name] = route
def main():
    shiproute = ShipRoute(debug=True)
    points = shiproute.get_route("ESSDR","AUMEL")['points']
    #print(points)
    home_loc = [5,46] 
    home_zoom = 3   
    world_map = folium.Map(home_loc, zoom_start=home_zoom)
    folium.PolyLine(points).add_to(world_map)
    world_map.save('indexrt.html')
       
if __name__ == "__main__":
    main()
    