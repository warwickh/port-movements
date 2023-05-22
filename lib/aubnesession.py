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

class AuBneSession:
    def __init__(self,
                 sessionFile='aubne_session.dat',
                 maxSessionTimeSeconds = 60 * 30,
                 agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                 debug = False):
     
        self.dataUrl = "https://qships.tmr.qld.gov.au/webx/services/wxdata.svc/GetDataX"
        self.baseUrl = "https://qships.tmr.qld.gov.au/webx/"
        self.debug = debug
        self.maxSessionTime = maxSessionTimeSeconds  
        self.sessionFile = sessionFile
        self.userAgent = agent
        self.exp_ship_movements = None
        self.comp_ship_movements = None
        self.vessels_at_berth = None
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
        
    def get_request_time(self):
        dateTime = datetime.today()
        timeDelta = timedelta(hours=8) 
        tzObject = timezone(timeDelta)
        perthTimeNow = dateTime.replace(tzinfo=tzObject)
        print(perthTimeNow.isoformat("T","auto"))
        print(perthTimeNow.isoformat("T","milliseconds"))

    def get_report(self, report_name):
        res = self.retrieveContent(self.baseUrl)
        soup = BeautifulSoup(res.text, "html.parser") 
        if report_name == 'exp_ship_movements':
            report_code = 'MSQ-WEB-0001'
            filter_name = "Next 7 days"
            get_data_query = {"token": None,"reportCode": report_code,"dataSource": None, "filterName": filter_name, 
                "parameters": [{"__type": "ParameterValueDTO:#WebX.Core.DTO", "sName": "DOMAIN_ID", "iValueType": 0, "aoValues": [{"Value": "67"}],}],"metaVersion": 0,}
            headers = ["VOYAGE ID","ID","JOB TYPE","SHIP","SHIP TYPE","LOA","AGENCY","START TIME","END TIME","FROM LOCATION","TO LOCATION","STATUS","LAST PORT","NEXT PORT","VOYAGE #","VESSEL ID","STATUS TYPE"]
        elif report_name == 'comp_ship_movements':
            report_code = 'MSQ-WEB-0001'
            filter_name = "Last 7 Days"
            #get_data_query = {"token": None,"reportCode": report_code,"dataSource": None, "filterName": filter_name, 
            #    "parameters": [{"__type": "ParameterValueDTO:#WebX.Core.DTO", "sName": "DOMAIN_ID", "iValueType": 0, "aoValues": [{"Value": "67"}],}],"metaVersion": 0,}
            start_date = (datetime.combine(date.today(), datetime.min.time()) + timedelta(days=-10)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            end_date = (datetime.combine(date.today(), datetime.min.time())).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] 
            #Get 10 days of history
            get_data_query = {"token": None,"reportCode": report_code,"dataSource": None,"filterName": None,
                "parameters":[{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"DOMAIN_ID","iValueType":0,
                "aoValues":[{"Value":-1}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"DATE_TIME","iValueType":0,"aoValues":[{"Value":"6"}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"START_DATE","iValueType":0,"aoValues":[{"Value": start_date}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"END_DATE","iValueType":0,"aoValues":[{"Value": end_date}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"TOP","iValueType":0,"aoValues":[{"Value":"500"}]}],"metaVersion":0}  
            headers = ["VOYAGE ID","ID","JOB TYPE","SHIP","SHIP TYPE","LOA","AGENCY","START TIME","END TIME","FROM LOCATION","TO LOCATION","STATUS","LAST PORT","NEXT PORT","VOYAGE #","VESSEL ID","STATUS TYPE"]
        elif report_name == 'vessels_at_berth':
            report_code = 'MSQ-WEB-0018'
            get_data_query = {"token": None,"reportCode":"MSQ-WEB-0018","dataSource": None,"filterName": None,
                "parameters":[{"__type":"ParameterValueDTO:#WebX.Core.DTO","aoValues":[{"__type":"ValueItemDTO:#WebX.Core.DTO","Value":1500}],"iValueType":0,"sName":"TOP"},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"DOMAIN_ID","iValueType":0,"aoValues":[{"Value":-1}]}],"metaVersion":0} 
            headers = ["ARR DATE", "DEP DATE","SHIP INFO","SHIP", "BERTH","PORT", "AGENT INFO", "TO","ID","VESSEL ID", "AGENCY ID"]
        else:
            print("Invalid code")
        res = self.retrieveContent(self.dataUrl, method="post", postData=get_data_query)
        data = res.json()
        #print(data)
        df = pd.DataFrame(data['d']['Tables'][0]['Data'])
        df.columns = headers
        try:
            df['START TIME'] = df['START TIME'].apply(self.convert_unix_time)#(tz_string, value):
            df['END TIME'] = df['END TIME'].apply(self.convert_unix_time)#(tz_string, value):
        except:
            pass
        try:
            df['ARR DATE'] = df['ARR DATE'].apply(self.convert_string_time)#(tz_string, value):
            df['DEP DATE'] = df['DEP DATE'].apply(self.convert_string_time)#(tz_string, value):
        except:
            pass
        for column in df.columns:
            try:
                df[column] = df[column].str.strip().str.upper()
            except:
                pass            
        filename = 'aubne_%s.csv'%report_name
        df.to_csv(filename, encoding='utf-8', index=False)
        return df
                
    def refresh_exp_ship_movements(self):
        report_name = 'exp_ship_movements'
        return self.get_report(report_name)
    
    def refresh_comp_ship_movements(self):
        report_name = 'comp_ship_movements'
        return self.get_report(report_name)
        
    def refresh_vessels_at_berth(self):
        report_name = 'vessels_at_berth'   
        return self.get_report(report_name)

    def next_week(self):
        from_time = datetime.combine(date.today(), datetime.min.time()).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        to_time = (datetime.combine(date.today(), datetime.min.time()) + timedelta(days = 7)).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] 
        return [from_time, to_time]
    
    def last_week(self):
        from_time = (datetime.combine(date.today(), datetime.min.time()) + timedelta(days = -7)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        to_time = (datetime.combine(date.today(), datetime.min.time())).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] 
        return [from_time, to_time]
        
    def next_month(self):
        from_time = datetime.combine(date.today(), datetime.min.time()).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        to_time = (datetime.combine(date.today(), datetime.min.time()) + timedelta(days=30)).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] 
        return [from_time, to_time]
        
    def last_month(self):
        from_time = (datetime.combine(date.today(), datetime.min.time()) + timedelta(days=-30)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        to_time = (datetime.combine(date.today(), datetime.min.time())).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] 
        return [from_time, to_time]

    def get_eta_by_name(self, vessel_name):
        vessel_name = vessel_name.strip().upper()
        results = self.exp_ship_movements.loc[(self.exp_ship_movements['SHIP'] == vessel_name) &
            (self.exp_ship_movements['JOB TYPE'] == "ARR")]['START TIME'].to_frame()
        return results

    def get_ata_by_name(self, vessel_name):
        vessel_name = vessel_name.strip().upper()
        results = self.comp_ship_movements.loc[(self.comp_ship_movements['SHIP'] == vessel_name) &
            (self.comp_ship_movements['JOB TYPE'] == "ARR")]['START TIME'].to_frame()
        return results      

    def get_eta(self):
        results = self.exp_ship_movements.loc[self.exp_ship_movements['JOB TYPE'] == "ARR"].copy()#['START TIME'].to_frame()
        results['PORT_ETA'] = results['START TIME']
        results['PORT'] = 'AUBNE'
        results = results[['PORT', 'SHIP', 'PORT_ETA']]
        results.columns = ['PORT', 'SHIP_NAME', 'PORT_ETA']
        return results    

    def get_in_port(self):
        results = self.vessels_at_berth.copy()
        results['PORT'] = 'AUBNE'
        results = results[['PORT','ARR DATE','DEP DATE', 'SHIP']]
        results.columns = ['PORT','ARR_DATE','DEP_DATE', 'SHIP_NAME']
        return results   
        
    def refresh_all(self):
        try:
            self.exp_ship_movements = self.refresh_exp_ship_movements()
            self.comp_ship_movements = self.refresh_comp_ship_movements()
            self.vessels_at_berth = self.refresh_vessels_at_berth()
        except:
            print("Refresh failed. Loading from file") 
            self.exp_ship_movements = pd.read_csv('aubne_exp_ship_movements.csv')
            self.comp_ship_movements = pd.read_csv('aubne_comp_ship_movements.csv')
            self.vessels_at_berth = pd.read_csv('aubne_vessels_at_berth.csv')
        if self.debug:
            print(self.exp_ship_movements)
            print(self.comp_ship_movements)
            print(self.vessels_at_berth)
        self.write_to_csv()
        return True
    
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
    aubnesession = AuBneSession(maxSessionTimeSeconds = 60, debug=True)
    print(aubnesession.get_eta_by_name("MSC ALABAMA III"))
    print(aubnesession.get_ata_by_name("HOEGH TRAVELLER"))
    print(aubnesession.get_in_port())
       
if __name__ == "__main__":
    main()
    
    """
    Status column on the public pages denotes the following:    1. PLAN = Planned movement, the relevant Vessel Traffic Service Centre (VTSC) has not reviewed or scheduled the movement    2. SCHD = Scheduled movement, the relevant VTSC has reviewed and scheduled the movement into the port    3. CONF = Confirmed movement, all service providers (marine pilots, tugs, lines launches and lines men) have confirmed their availability for the job and the movement is considered to be occurring at the scheduled time    4. ACTV = Active movement, the ship has commenced the movement    5. COMP = Completed movement, the ship has arrived at the end location of the movement, be that external anchorage, berth, internal anchorage, or SEA    6. RELS = Released movement, this is related to invoicing and means the movement is ready for billing of any applicable fees    7. INVC = Invoiced movement, the invoice for any relevant fees has been issued    8. CANC = Cancelled movement
    
    Job Type column on the public pages denotes the following:    1. EXT = External movement, this is a movement to an anchorage outside of the compulsory pilotage area, the ship comes from sea and anchors off the port waiting till berthing time.    2. ARR = Arrival movement, this is the first movement of a ship into the compulsory pilotage area and can be to a berth or internal anchorage    3. REM = Removal movement, this is where a ship moves from one location within the port to another, for example may move from one berth to another for loading of different goods    4. DEP = Departure movement, this is where the ship departs the port to sea and heads to it's next destination.
    
    {"token":null,"reportCode":"MSQ-WEB-0001","dataSource":null,"filterName":null,"parameters":[{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"DOMAIN_ID","iValueType":0,"aoValues":[{"Value":-1}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"DATE_TIME","iValueType":0,"aoValues":[{"Value":"6"}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"START_DATE","iValueType":0,"aoValues":[{"Value":"2023-05-01T00:00:00"}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"END_DATE","iValueType":0,"aoValues":[{"Value":"2023-05-16T00:00:00"}]},{"__type":"ParameterValueDTO:#WebX.Core.DTO","sName":"TOP","iValueType":0,"aoValues":[{"Value":"500"}]}],"metaVersion":0}
    
    """