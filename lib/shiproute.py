#!/usr/bin/env python3
"""
        
        #'MSQ-WEB-0001' title: 'Ship movements',
        #'MSQ-WEB-0018' title: 'Vessels At Berth',
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
        #http://ports.com/sea-route/port-of-melbourne,australia/port-of-fremantle-perth,australia/
        #http://ports.com/sea-route/port-of-brisbane,australia/port-kembla,australia/
        #http://ports.com/sea-route/port-of-antwerp,belgium/port-kembla,australia/
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
        self.baseUrl = "http://ports.com/sea-route/"
        self.dataUrl = "http://ports.com/aj/sea-route/"
        self.debug = debug
        self.maxSessionTime = maxSessionTimeSeconds  
        self.sessionFile = sessionFile
        self.userAgent = agent
        self.get_session()
        #self.refresh_all()

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
       
    def get_route(self, origin_name, dest_name):
        res = self.retrieveContent(self.baseUrl)
        print(res.cookies)
        url = "http://ports.com/aj/sea-route/?a=0&amp;b=0&amp;c=%s&amp;d=%s"%(self.port_data[origin_name]['name'].split(',')[0],self.port_data[dest_name]['name'].split(',')[0])
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
        print(res)
        #print(res.text)
        data = res.json()
        return data                    
       
    def refresh_all(self):
        for origin in self.origins:#self.port_data:
            for dest in self.destinations:
                data = self.get_route(origin, dest)
                json_object = json.dumps(data, indent=4)
                with open("%s_%s.json"%(origin, dest), "w") as outfile:
                    outfile.write(json_object)
        
    def write_to_csv(self):
        self.exp_ship_movements.to_csv('aubne_exp_ship_movements.csv', encoding='utf-8', index=False)
        self.comp_ship_movements.to_csv('aubne_comp_ship_movements.csv', encoding='utf-8', index=False)
        self.vessels_at_berth.to_csv('aubne_vessels_at_berth.csv', encoding='utf-8', index=False)

    def legacy_process(self, df):
        df = df.loc[df['Job Type'] == 'ARR']
        df = df[['Ship', 'Start Time']]
        df.columns = ['ship_name', 'port_eta']
        df['ship_name'] = df['ship_name'].str.strip().str.upper()
        df['port'] = 'AUBNE'
        return df
        
def main():
    shiproute = ShipRoute(debug=True)
    
    points = [
        [
            1.99830732586389,
            51.0028014636403
        ],
        [
            2.44541181805317,
            51.0667540553761
        ],
        [
            2.52478681805349,
            51.0969072536184
        ],
        [
            2.96031578940941,
            51.2651915553769
        ],
        [
            3.2254158870667,
            51.351439520872
        ],
        [
            3.35031782391616,
            51.3778978542055
        ],
        [
            3.42597212079147,
            51.3932457545962
        ],
        [
            3.58947635256297,
            51.3996019557681
        ],
        [
            3.71649702313638,
            51.3689061549867
        ],
        [
            3.88315351727766,
            51.354617621458
        ],
        [
            3.99828860842396,
            51.3917182551466
        ]
    ]   
    home_loc = [5,46] 
    home_zoom = 3   
    world_map = folium.Map(home_loc, zoom_start=home_zoom)
    folium.PolyLine(points).add_to(world_map)
    world_map.save('indexrt.html')
       
if __name__ == "__main__":
    main()
    
    """
    Status column on the public pages denotes the following:    1. PLAN = Planned movement, the relevant Vessel Traffic Service Centre (VTSC) has not reviewed or scheduled the movement    2. SCHD = Scheduled movement, the relevant VTSC has reviewed and scheduled the movement into the port    3. CONF = Confirmed movement, all service providers (marine pilots, tugs, lines launches and lines men) have confirmed their availability for the job and the movement is considered to be occurring at the scheduled time    4. ACTV = Active movement, the ship has commenced the movement    5. COMP = Completed movement, the ship has arrived at the end location of the movement, be that external anchorage, berth, internal anchorage, or SEA    6. RELS = Released movement, this is related to invoicing and means the movement is ready for billing of any applicable fees    7. INVC = Invoiced movement, the invoice for any relevant fees has been issued    8. CANC = Cancelled movement
    
    Job Type column on the public pages denotes the following:    1. EXT = External movement, this is a movement to an anchorage outside of the compulsory pilotage area, the ship comes from sea and anchors off the port waiting till berthing time.    2. ARR = Arrival movement, this is the first movement of a ship into the compulsory pilotage area and can be to a berth or internal anchorage    3. REM = Removal movement, this is where a ship moves from one location within the port to another, for example may move from one berth to another for loading of different goods    4. DEP = Departure movement, this is where the ship departs the port to sea and heads to it's next destination.
    
    {"token":null,"reportCode":"MSQ-WEB-0001","dataSource":null,"filterName":null,"parameters":[{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"DOMAIN_ID","iValueType":0,"aoValues":[{"Value":-1}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"DATE_TIME","iValueType":0,"aoValues":[{"Value":"6"}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"START_DATE","iValueType":0,"aoValues":[{"Value":"2023-05-01T00:00:00"}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"END_DATE","iValueType":0,"aoValues":[{"Value":"2023-05-16T00:00:00"}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"TOP","iValueType":0,"aoValues":[{"Value":"500"}]}],"metaVersion":0}
    
    """