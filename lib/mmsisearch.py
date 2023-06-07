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
from urllib.parse import urlparse  
import csv
import random
import re
import pandas as pd
import ast
import unidecode
import cloudscraper

class MmsiSearch:
    def __init__(self,
                 sessionFile='balticshipping_session.dat',
                 maxSessionTimeSeconds = 60 * 30,
                 agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                 debug = False):
     
        self.dataUrl = "https://www.balticshipping.com/"
        self.baseUrl = "https://www.balticshipping.com"
        self.debug = debug
        self.maxSessionTime = maxSessionTimeSeconds  
        self.sessionFile = sessionFile
        self.scraper = cloudscraper.create_scraper()
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
        if method == 'scrape':
            res = self.scraper.get(url)
        elif method == 'get':
            res = self.session.get(url)
        else:
            res = self.session.post(url , data = postData)
            #res = self.session.post(url , json = postData)
        #self.saveSessionToCache()            
        return res

    def search_mmsi(self, vessel_name):
        mmsi = None
        vessel_name = vessel_name.strip().upper()
        url = "%s"%(self.dataUrl)
        payload = {
            "request[0][module]": "ships",
            "request[0][action]": "list",
            "request[0][id]": "0",
            "request[0][data][0][name]": "search_id",
            "request[0][data][0][value]": "0",
            "request[0][data][1][name]": "name",
            "request[0][data][1][value]": vessel_name,
            "request[0][data][2][name]": "imo",
            "request[0][data][2][value]": "",
            "request[0][data][3][name]": "ship_type",
            "request[0][data][3][value]": "12",
            "request[0][data][4][name]": "page",
            "request[0][data][4][value]": "0",
            "request[0][sort]": "",
            "request[0][limit]": "9",
            "request[0][stamp]": "0",
            "request[1][module]": "top_stat",
            "request[1][action]": "list",
            "request[1][id]": "0",
            "request[1][data]": "",
            "request[1][sort]": "",
            "request[1][limit]": "",
            "request[1][stamp]": "0"
        }
        res = self.retrieveContent(url, method = "post", postData = payload)
        #print(res)
        data = res.json()
        print(res)
        print(data)
        vessel_list = data["data"]["request"][0]["ships"]
        for vessel in vessel_list:
            if vessel["data"]["name"].strip().upper() == vessel_name:
                mmsi = vessel["data"]["mmsi"]
                print("Found match %s %s"%(vessel_name, mmsi))
        return mmsi
        
    def convert_unix_time(self, value):
        #print(value)
        pattern = "\/Date\((\d{10})\d{3}([+-])(\d{2})\d{2}"
        times = re.findall(pattern, str(value))
        if(len(times)>0):
            ts = int(times[0][0])
            td = int(times[0][2])
            unix_time = datetime.utcfromtimestamp(ts)
            local_time = unix_time+timedelta(hours=td)
            return(local_time.strftime('%d-%m-%Y %H:%M:%S'))
        else:
            return value    

    def remove_accents(self, a):
        return unidecode.unidecode(a)
        
    def convert_string_time(self, value):
        date_formats = ['%b %d %Y %I:%M%p','%Y-%m-%dT%H:%M:%S','%d/%m/%Y %H:%M','%d %b %Y %H:%M','%a %d %b %Y %H:%M']
        for date_format in date_formats:
            try:
                time = datetime.strptime(value, date_format)
                return(time.strftime('%d-%m-%Y %H:%M:%S'))
            except:
                pass
        if self.debug:
            print("No format found for %s"%value)
        return ""
               
    def next_month(self):
        from_time = datetime.combine(date.today(), datetime.min.time()).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        to_time = (datetime.combine(date.today(), datetime.min.time()) + timedelta(days=30)).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] 
        return [from_time, to_time]
    
    def next_60_days(self):
        from_time = datetime.combine(date.today(), datetime.min.time()).strftime("%Y-%m-%d")
        to_time = (datetime.combine(date.today(), datetime.min.time()) + timedelta(days=60)).strftime("%Y-%m-%d")
        return [from_time, to_time]        
        
    def next_x_days(self, no_of_days):    
        from_time = datetime.combine(date.today(), datetime.min.time()).strftime("%Y-%m-%d")
        to_time = (datetime.combine(date.today(), datetime.min.time()) + timedelta(days=no_of_days)).strftime("%Y-%m-%d")
        return [from_time, to_time]  
        
    def get_vessel_list(self):
        req_type = "vessel"
        #vessel_name = vessel_name.strip().upper()
        url = "%s%s/"%(self.dataUrl, req_type)
        #print(url)
        result = self.retrieveContent(url)
        #print(result.text)
        vessel_list = ast.literal_eval(result.text.replace(':false', ':False').replace(':true', ':True').replace(':null', ':None'))['mappedObject']
        #print(vessel_list)
        return vessel_list
        
    def get_schedule_by_name(self, vessel_name, date_from, date_to):
        req_type = "vessel"
        vessel_name = vessel_name.strip().upper()
        url = "%s%s/%s/schedule/%s/%s"%(self.dataUrl, req_type, vessel_name, date_from, date_to)
        print(url)
        result = self.retrieveContent(url)
        #print(result.text)
        schedule = ast.literal_eval(result.text.replace(':false', ':False').replace(':true', ':True').replace(':null', ':None'))['mappedObject']
        return schedule     

    def get_schedule_by_code(self, vessel_code, date_from, date_to):
        req_type = "vessel"
        url = "%s%s/%s/schedule/%s/%s"%(self.dataUrl, req_type, vessel_code, date_from, date_to)
        print(url)
        result = self.retrieveContent(url)
        #print(result.text)
        schedule = ast.literal_eval(result.text.replace(':false', ':False').replace(':true', ':True').replace(':null', ':None'))['mappedObject']
        return schedule            

    def get_vessel_code(self, vessel_name):
        vessel_code = None
        vessel_name = self.remove_accents(vessel_name).strip().upper()
        vessel_list = self.get_vessel_list()
        for vessel in vessel_list:
            if self.remove_accents(vessel['VESSEL_NAME']).strip().upper() == vessel_name:
                vessel_code = vessel['VESSEL_CODE']
                print("Found match %s %s"%(vessel_name, vessel_code))
        return vessel_code    

    def get_scheduled_arrival(self, vessel_name, port_code):
        arrival = None
        vessel_code = self.get_vessel_code(vessel_name)
        date_from, date_to = self.next_60_days()
        schedule = self.get_schedule_by_code(vessel_code, date_from, date_to)
        #print(schedule)
        for stop in schedule:
            #print(stop)
            #print(stop['port_CODE'])
            if stop['port_CODE'] == port_code:
                print("Found port code %s"%port_code)
                #print(type(stop['arrival_DATE']))
                #print(int(stop['arrival_DATE'][:10]))
                arrival = datetime.fromtimestamp(int(str(stop['arrival_DATE'])[:10]))
                #print(arrival)
                break #First result                 
        return arrival

    def get_schedule(self, vessel_name):
        #arrival = None
        vessel_code = self.get_vessel_code(vessel_name)
        date_from, date_to = self.next_x_days(90)
        schedule = self.get_schedule_by_code(vessel_code, date_from, date_to)
        return schedule
        
def main():
    mmsisearch = MmsiSearch(debug=True)
    vessels = ["HMM MIR", "MAERSK SEBAROK"]
    for vessel in vessels:
        mmsi = mmsisearch.search_mmsi(vessel)
        print(mmsi)
    #print(hapagsession.retrieveContent("https://www.hapag-lloyd.cn/en/online-business/track/track-by-booking-solution.html?blno=HLCUGOA230499437"))
    #print(hoeghsession.get_vessel_list())
    #print(hoeghsession.get_schedule_by_name("TRPR","2023-05-25","2023-07-30"))
    #print(hoeghsession.next_60_days())
    #print(hoeghsession.get_vessel_code("HOEGH TRAPPER"))
    #print(hoeghsession.get_scheduled_arrival("HOEGH TRAPPER", "NZAKL"))
    #print(hoeghsession.get_scheduled_arrival("HOEGH BANGKOK", "NZAKL"))
    #schedule = hoeghsession.get_schedule("HOEGH BANGKOK")
    #for stop in schedule:
        #print(stop)
    #    print("%s %s"%(stop['port_CODE'],datetime.fromtimestamp(int(str(stop['arrival_DATE'])[:10]))))
    
if __name__ == "__main__":
    main()
    