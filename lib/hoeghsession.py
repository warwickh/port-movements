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

class HoeghSession:
    def __init__(self,
                 sessionFile='hoegh_session.dat',
                 maxSessionTimeSeconds = 60 * 30,
                 agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                 debug = False):
     
        self.dataUrl = "https://m.hoegh.com/vesselintegration/rest/"#vessel/"#ASIA/schedule/2023-05-30/2023-07-30"
        self.baseUrl = "https://www.hoeghautoliners.com/sailing-schedule"
        self.debug = debug
        self.maxSessionTime = maxSessionTimeSeconds  
        self.sessionFile = sessionFile
        self.userAgent = agent
        self.exp_ship_schedule = None
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
        
def main():
    hoeghsession = HoeghSession(debug=True)
    #print(hoeghsession.get_vessel_list())
    #print(hoeghsession.get_schedule_by_name("TRPR","2023-05-25","2023-07-30"))
    print(hoeghsession.next_60_days())
    print(hoeghsession.get_vessel_code("HOEGH TRAPPER"))
    print(hoeghsession.get_scheduled_arrival("HOEGH TRAPPER", "NZAKL"))
    print(hoeghsession.get_scheduled_arrival("HOEGH BANGKOK", "NZAKL"))
    
if __name__ == "__main__":
    main()
    