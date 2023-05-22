#!/usr/bin/env python3
"""
        
        #'MSQ-WEB-0001' title: 'Ship movements',
        #'MSQ-WEB-0018' title: 'Vessels At Berth',
"""

mel_exp_headers = ['STATUS','ACTL_MVMT_START_DATETIME','MOVEMENT_TYPE','SHIP_NAME','BERTH_NAME_FROM','NEXT_PORT_NAME','AGENT']
mel_act_headers = ['SHIP_NAME','MOVEMENT_T','ORIGIN','FROM_DATETIME','DESTINATION','TO_DATETIME','FAWKNERDATETIME','AGENT_NAME']
mel_sip_headers = ['SHIP_NAME','FROM_BERTH_NAME','ARR_DATEIME','DEP_DATETIME','TO_BERTH_NAME','PHONE_NUMBER','AGENT_NAME','AGENT_PHONE']


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

class AuMelSession:
    def __init__(self,
                 sessionFile='aumel_session.dat',
                 maxSessionTimeSeconds = 60 * 30,
                 agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                 debug = False):
     
        self.dataUrl = "https://www.vicports.vic.gov.au/ShipMovementLogs/"
        self.baseUrl = "https://www.vicports.vic.gov.au/operations/Pages/ship-movements.aspx"
        self.debug = debug
        self.maxSessionTime = maxSessionTimeSeconds  
        self.sessionFile = sessionFile
        self.userAgent = agent
        self.expected_movements = None
        self.actual_movements = None
        self.ships_in_port = None
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
        if report_code == "expected_movements":
            headers = mel_exp_headers
            url = "%s%s"%(self.dataUrl, "www_expected_movements.log")
        elif report_code == "actual_movements":
            headers = mel_act_headers
            url = "%s%s"%(self.dataUrl, "www_actual_movements.log")
        elif report_code == "ships_in_port":
            headers = mel_sip_headers
            url = "%s%s"%(self.dataUrl, "www_ships_in_port.log")
        else:
            return
        df = pd.read_csv(url, skiprows=2, names=headers)
        try:
            df['ACTL_MVMT_START_DATETIME']=df['ACTL_MVMT_START_DATETIME'].str.strip().apply(self.convert_string_time)
        except:
            pass
        for column in df.columns:
            try:
                df[column] = df[column].str.strip().str.upper()
            except:
                pass
        filename = 'aumel_%s.csv'%report_code
        df.to_csv(filename, encoding='utf-8', index=False)
        #print(df)
        return df

    def legacy_process(self, df): #previous processing of csv (expected only)
        df = df.loc[df['movement_type'].str.strip() == 'Arrival']
        df['port_eta'] = df['actl_mvmt_start_datetime'].str.strip().apply(convert_string_time)
        #df['port_eta'] = datetime.strptime(df['actl_mvmt_start_datetime'], '%d-%m-%Y %H:%M:%S')
        #df.columns = ['ship_name', 'port_eta']
        df['ship_name'] = df['ship_name'].str.strip().str.upper()
        df = df[['ship_name', 'port_eta']]
        df['port'] = 'AUMEL'
        return df

    def get_eta_by_name(self, vessel_name):
        vessel_name = vessel_name.strip().upper()
        results = self.expected_movements.loc[(self.expected_movements['SHIP_NAME'] == vessel_name) &
            (self.expected_movements['MOVEMENT_TYPE'] == "ARRIVAL")]['ACTL_MVMT_START_DATETIME'].to_frame()
        return results

    def get_ata_by_name(self, vessel_name):
        vessel_name = vessel_name.strip().upper()
        results = self.actual_movements.loc[(self.actual_movements['SHIP_NAME'] == vessel_name) &
            (self.actual_movements['MOVEMENT_T'] == "ARRIVAL")]['TO_DATETIME'].to_frame()
        return results        

    def get_eta(self):   
        results = self.expected_movements.loc[self.expected_movements['MOVEMENT_TYPE'] == "ARRIVAL"].copy()#['ACTL_MVMT_START_DATETIME'].to_frame()
        results['PORT_ETA'] = results[['ACTL_MVMT_START_DATETIME']]
        results['PORT'] = 'AUMEL'
        results = results[['PORT','SHIP_NAME', 'PORT_ETA']]
        results.columns = ['PORT','SHIP_NAME', 'PORT_ETA']
        return results

    def get_in_port(self):
        results = self.ships_in_port.copy()
        results['PORT'] = 'AUMEL'
        results = results[['PORT','ARR_DATEIME','DEP_DATETIME', 'SHIP_NAME']]
        results.columns = ['PORT','ARR_DATE','DEP_DATE', 'SHIP_NAME']
        return results 
        
    def refresh_all(self):
        try:
            self.expected_movements = self.get_report('expected_movements')
            self.actual_movements = self.get_report('actual_movements')
            self.ships_in_port = self.get_report('ships_in_port')
        except:
            print("Refresh failed. Loading from file") 
            self.expected_movements = pd.read_csv('aumel_expected_movements.csv')
            self.actual_movements = pd.read_csv('aumel_actual_movements.csv')
            self.ships_in_port = pd.read_csv('aumel_ships_in_port.csv')            
        if self.debug:
            print(self.expected_movements)
            print(self.actual_movements)
            print(self.ships_in_port)
        self.write_to_csv()
        return True
    
    def write_to_csv(self):
        self.expected_movements.to_csv('aumel_expected_movements.csv', encoding='utf-8', index=False)
        self.actual_movements.to_csv('aumel_actual_movements.csv', encoding='utf-8', index=False)
        self.ships_in_port.to_csv('aumel_ships_in_port.csv', encoding='utf-8', index=False)
        
def main():
    aumelsession = AuMelSession(debug=True)
    print(aumelsession.get_eta_by_name("Hoegh Chiba"))
    print(aumelsession.get_ata_by_name("HSL Anna (T)"))
    
if __name__ == "__main__":
    main()
    