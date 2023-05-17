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

class NzAklSession:
    def __init__(self,
                 sessionFile='nzakl_session.dat',
                 maxSessionTimeSeconds = 60 * 30,
                 agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                 debug = False):
     
        self.dataUrl = "https://www.poal.co.nz/operations/schedules/"
        self.baseUrl = "https://www.poal.co.nz/operations"
        self.debug = debug
        self.maxSessionTime = maxSessionTimeSeconds  
        self.sessionFile = sessionFile
        self.userAgent = agent
        self.expected_arrivals = None
        self.recent_departures = None
        self.vessels_in_port = None
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

    def remove_accents(self, a):
        return unidecode.unidecode(a)
        
    def convert_string_time(self, value):
        #      Mar  1 2023  1:30PM
        try:
            time = datetime.strptime(value, '%b %d %Y %I:%M%p')
            return(time.strftime('%d-%m-%Y %H:%M:%S'))
        except:
            pass
        try:
            time = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            return(time.strftime('%d-%m-%Y %H:%M:%S'))
        except:
            pass    
        try:
            time = datetime.strptime(value, '%d/%m/%Y %H:%M')
            return(time.strftime('%d-%m-%Y %H:%M:%S'))
        except:
            pass
        try:
            time = datetime.strptime(value, '%d %b %Y %H:%M')
            return(time.strftime('%d-%m-%Y %H:%M:%S'))
        except:
            pass
        print("No format found for %s"%value)
        return ""
    
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

    def get_request_time(self):
        dateTime = datetime.today()
        timeDelta = timedelta(hours=8) 
        tzObject = timezone(timeDelta)
        perthTimeNow = dateTime.replace(tzinfo=tzObject)
        print(perthTimeNow.isoformat("T","auto"))
        print(perthTimeNow.isoformat("T","milliseconds"))

    def get_report(self, report_code):
        res = self.retrieveContent(self.baseUrl)
        url = "%s%s"%(self.dataUrl,report_code)
        data = self.retrieveContent(url)
        df = pd.read_html(data.text)[0]
        #df['port_eta'] = df['Arrival'].str.strip().apply(convert_string_time)
        df.columns = df.columns.str.upper()
        try:
            df['Arrival']=df['Arrival'].str.strip().apply(self.convert_string_time)
        except:
            pass
        for column in df.columns:
            try:
                df[column] = df[column].str.strip().str.upper()
            except:
                pass
        filename = 'nzakl%s.csv'%report_code
        df.to_csv(filename, encoding='utf-8', index=False)
        return df

    def refresh_all(self):
        try:
            self.arrivals = self.get_report('arrivals')
            self.departures = self.get_report('departures')
            self.vessels_in_port = self.get_report('vessels-in-port')
        except:
            print("Refresh failed. Loading from file")
            self.arrivals = pd.read_csv('nzakl_arrivals.csv')
            self.departures = pd.read_csv('nzakl_departures.csv')
            self.vessels_in_port = pd.read_csv('nzakl_vessels_in_port.csv')
        if self.debug:
            print(self.arrivals)
            print(self.departures)
            print(self.vessels_in_port)
        self.write_to_csv()
        return True
    
    def write_to_csv(self):
        self.arrivals.to_csv('nzakl_arrivals.csv', encoding='utf-8', index=False)
        self.departures.to_csv('nzakl_departures.csv', encoding='utf-8', index=False)
        self.vessels_in_port.to_csv('nzakl_vessels_in_port.csv', encoding='utf-8', index=False)

    def get_eta_by_name(self, vessel_name):
        vessel_name = vessel_name.strip().upper()
        results = self.arrivals.loc[self.arrivals['VESSEL'] == vessel_name]['ARRIVAL'].to_frame()
        return results

    def get_ata_by_name(self, vessel_name):
        vessel_name = vessel_name.strip().upper()
        results = self.departures.loc[self.departures['VESSEL'] == vessel_name]['ARRIVAL'].to_frame()
        return results

    def get_eta(self):
        results = self.arrivals.copy()
        results['PORT_ETA'] = results['ARRIVAL'].str.strip().apply(self.convert_string_time)
        results['PORT'] = 'NZAKL'
        results = results[['PORT', 'VESSEL', 'PORT_ETA']]
        results.columns = ['PORT', 'SHIP_NAME', 'PORT_ETA']
        return results    

    def legacy_process(self, df):
        df = df[['Vessel', 'Arrival']]
        df.columns = ['ship_name', 'port_eta']
        df['ship_name'] = df['ship_name'].str.strip().str.upper()
        df['port'] = 'NZAKL'
        return df
               
def main():
    nzaklsession = NzAklSession(debug=True)
    print(nzaklsession.get_eta_by_name("OLOMANA"))
    print(nzaklsession.get_ata_by_name("OLOMANA"))
    
if __name__ == "__main__":
    main()
    