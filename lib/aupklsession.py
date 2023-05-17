#!/usr/bin/env python3
"""
        
        #'MSQ-WEB-0001' title: 'Ship movements',
        #'MSQ-WEB-0018' title: 'Vessels At Berth',
"""

def update_aupkl():
    log_name = 'aupkl'
    url = 'https://www.portauthoritynsw.com.au/umbraco/Api/VesselMovementAPI/GetApiVesselMovement?portCode=P04'
    pkl_data = pd.read_json(url)
    df = pd.json_normalize(pkl_data['items'])
    #export_table("pkl_eta", df)
    filename = '%s.csv'%log_name
    df.to_csv(filename, encoding='utf-8', index=False)
    return df

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

class AuPklSession:
    def __init__(self,
                 sessionFile='aupkl_session.dat',
                 maxSessionTimeSeconds = 60 * 30,
                 agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                 debug = False):
     
        self.dataUrl = "https://www.portauthoritynsw.com.au/umbraco/Api/VesselMovementAPI/GetApiVesselMovement?portCode=P04"
        self.baseUrl = "https://www.portauthoritynsw.com.au/port-kembla/"
        self.debug = debug
        self.maxSessionTime = maxSessionTimeSeconds  
        self.sessionFile = sessionFile
        self.userAgent = agent
        self.daily_vessel_movements = None
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

    def get_report(self):
        res = self.retrieveContent(self.baseUrl)
        pkl_data = pd.read_json(self.dataUrl)
        df = pd.json_normalize(pkl_data['items'])
        #export_table("pkl_eta", df)
        df.columns = df.columns.str.upper()
        try:
            df['TIME']=df['TIME'].str.strip().apply(self.convert_string_time)
        except:
            pass
        for column in df.columns:
            try:
                df[column] = df[column].str.strip().str.upper()
            except:
                pass  
        filename = 'aupkl.csv'
        df.to_csv(filename, encoding='utf-8', index=False)
        return df

    def legacy_process(self, df): #previous processing of csv (expected only)
        df = df.loc[df['movementType'] == 'Arrival']
        df['port_eta'] = df['time'].str.strip().apply(convert_string_time)
        df = df[['vesselName', 'port_eta']]
        df.columns = ['ship_name', 'port_eta']
        df['ship_name'] = df['ship_name'].str.strip().str.upper()
        df['port'] = 'AUPKL'
        return df
            
    def get_eta_by_name(self, vessel_name):
        vessel_name = vessel_name.strip().upper()
        results = self.daily_vessel_movements.loc[(self.daily_vessel_movements['VESSELNAME'] == vessel_name) &
            (self.daily_vessel_movements['MOVEMENTTYPE'] == "ARRIVAL")]['TIME'].to_frame()
        return results

    #def get_ata_by_name(self, vessel_name):
    #    vessel_name = vessel_name.strip().upper()
    #    results = self.comp_ship_movements.loc[(self.comp_ship_movements['SHIP'] == vessel_name) &
    #        (self.comp_ship_movements['JOB TYPE'] == "ARR")]['START TIME'].to_frame()
    #    return results 

    def get_eta(self):
        results = self.daily_vessel_movements.loc[(self.daily_vessel_movements['MOVEMENTTYPE'] == "ARRIVAL")].copy()#['TIME'].to_frame()
        results['PORT_ETA'] = results['TIME']
        results['PORT'] = 'AUPKL'
        results = results[['PORT','VESSELNAME', 'PORT_ETA']]
        results.columns = ['PORT','SHIP_NAME', 'PORT_ETA']
        return results
    
    def get_is_inport(self, vessel_name):
        results = self.daily_vessel_movements.loc[(self.daily_vessel_movements['VESSELNAME'] == vessel_name) &
            (self.daily_vessel_movements['INPORT'] == "Y")]['TIME'].to_frame()
        return len(results)>0
    
    def refresh_all(self):
        try:
            self.daily_vessel_movements = self.get_report()
        except:
            print("Refresh failed. Loading from file")
            self.daily_vessel_movements = pd.read_csv('aupkl_daily_vessel_movements.csv')
        if self.debug:
            print(self.daily_vessel_movements)
        self.write_to_csv()
        return True
    
    def write_to_csv(self):
        self.daily_vessel_movements.to_csv('aupkl_daily_vessel_movements.csv', encoding='utf-8', index=False)

def main():
    aupklsession = AuPklSession(debug=True)
    print(aupklsession.get_eta_by_name("HOEGH TRAPPER"))
    #print(aubnesession.get_ata_by_name("HOEGH TRAVELLER"))
    print(aupklsession.get_is_inport("HOEGH TRAPPER"))
    print(aupklsession.get_is_inport("CORONA SPLENDOR"))
    
if __name__ == "__main__":
    main()
    