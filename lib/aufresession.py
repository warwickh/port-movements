#!/usr/bin/env python3
"""

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
   
class AuFreSession:
    def __init__(self,
                 sessionFile='aufre_session.dat',
                 maxSessionTimeSeconds = 60 * 30,
                 agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                 debug = False):
     
        self.dataUrl = "https://www3.fremantleports.com.au/VTMIS/services/wxdata.svc/GetDataX"
        self.baseUrl = "https://www3.fremantleports.com.au/VTMIS/dashb.ashx?db=fmp.public&btn=ExpectedMovements"
        self.debug = debug
        self.maxSessionTime = maxSessionTimeSeconds  
        self.sessionFile = sessionFile
        self.userAgent = agent
        self.expected_movements = None
        self.completed_movements = None
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
        timeNow = dateTime.replace(tzinfo=tzObject)
        #print(perthTimeNow.isoformat("T","auto"))
        #print(perthTimeNow.isoformat("T","milliseconds"))
        return timeNow
        

    def get_report(self, report_name):
        res = self.retrieveContent(self.baseUrl)
        soup = BeautifulSoup(res.text, "html.parser") 
        for script in soup.find_all("script"):
            if script.string is not None and "scope.__stamp" in script.string:
                scope_stamp = re.findall(r"scope.__stamp = \'([^\']*)';", str(script.string))[0]       
        #print(scope_stamp)
        request_id = "%13d-%d"%(int(datetime.now().timestamp() * 1000),random.randint(1,10))
        if report_name == 'expected_movements':
            report_code = 'FMP-WEB-0001'
            from_time = self.next_week()[0]
            to_time = self.next_week()[1]
            get_data_query = {'request': {'requestID': request_id, 'reportCode': report_code, 'dataSource': None, 'filterName': None,
                'parameters': [{'__type': 'ParameterValueDTO:#WebX.Core.DTO', 'sName': 'FROM_TIME', 'iValueType': 0, 
                'aoValues': [{'__type': 'ValueItemDTO:#WebX.Core.DTO', 'Value': from_time,}, ],},
                    {'__type': 'ParameterValueDTO:#WebX.Core.DTO','sName': 'TO_TIME', 'iValueType': 0, 'aoValues': [{'__type': 'ValueItemDTO:#WebX.Core.DTO','Value': to_time,},],},],
                'metaVersion': 0, '_type': 'TGetDataXREQ:#WebX.Services', 'stamp': "%s\u000bfmp.public/main-view"%scope_stamp,},}
            headers = ["ID","VISIT #","SHIP","SHIP TYPE","MOVE TYPE","MOVE STATUS","MOVE START","FROM LOCATION","TO LOCATION","AGENCY","LAST PORT","NEXT PORT","VESSEL ID"]
        elif report_name == 'completed_movements':
            report_code = 'FMP-WEB-0001'
            from_time = self.last_week()[0]
            to_time = self.last_week()[1]
            start_date = (datetime.combine(date.today(), datetime.min.time()) + timedelta(days=-10)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            end_date = (datetime.combine(date.today(), datetime.min.time())).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]       
            get_data_query = {'request': {'requestID': request_id, 'reportCode': report_code, 'dataSource': None, 'filterName': None,
                'parameters': [{'__type': 'ParameterValueDTO:#WebX.Core.DTO', 'sName': 'FROM_TIME', 'iValueType': 0, 
                'aoValues': [{'__type': 'ValueItemDTO:#WebX.Core.DTO', 'Value': from_time,}, ],},
                    {'__type': 'ParameterValueDTO:#WebX.Core.DTO','sName': 'TO_TIME', 'iValueType': 0, 'aoValues': [{'__type': 'ValueItemDTO:#WebX.Core.DTO','Value': to_time,},],},],
                'metaVersion': 0, '_type': 'TGetDataXREQ:#WebX.Services', 'stamp': "%s\u000bfmp.public/main-view"%scope_stamp,},}  
            headers = ["ID","VISIT #","SHIP","SHIP TYPE","MOVE TYPE","MOVE STATUS","MOVE START","FROM LOCATION","TO LOCATION","AGENCY","LAST PORT","NEXT PORT","VESSEL ID"]
        elif report_name == 'ships_in_port':
            report_code = 'FMP-WEB-0004'
            get_data_query = {'request': {'requestID': request_id, 'reportCode': report_code, 'dataSource': None, 'filterName': None,
                'parameters': [],
                'metaVersion': 0, '_type': 'TGetDataXREQ:#WebX.Services', 'stamp': "%s\u000bfmp.public/main-view"%scope_stamp,},}  
            headers = ["ID", "VISIT #","BERTH/ANCHORAGE","LOCATION TYPE", "VESSEL ID","SHIP", "TYPE", "DEPARTURE","TO LOCATION", "AGENCY", "LAST PORT", "NEXT PORT", "VOYAGE ID", "FP VISIT ID"]
        else:
            print("Invalid code")
        res = self.retrieveContent(self.dataUrl, method="post", postData=get_data_query)
        data = res.json()
        #print(data)
        df = pd.DataFrame(data['d']['Tables'][0]['Data'])
        df.columns = headers
        try:
            df['MOVE START'] = df['MOVE START'].apply(self.convert_unix_time)#(tz_string, value):        
        except:
            pass
        try:
            df['DEPARTURE'] = df['DEPARTURE'].apply(self.convert_unix_time)#(tz_string, value):
        except:
            pass
        for column in df.columns:
            try:
                df[column] = df[column].str.strip().str.upper()
            except:
                pass            
        filename = 'aufre_%s.csv'%report_name
        df.to_csv(filename, encoding='utf-8', index=False)
        return df

    def refresh_expected_movements(self):
        report_name = 'expected_movements'
        return self.get_report(report_name)

    def refresh_completed_movements(self):
        report_name = 'completed_movements'
        return self.get_report(report_name)

    def refresh_ships_in_port(self):
        report_name = 'ships_in_port'   
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
        results = self.expected_movements.loc[(self.expected_movements['SHIP'] == vessel_name) &
            (self.expected_movements['MOVE TYPE'] == "ARRIVAL")]['MOVE START'].to_frame()
        return results

    def get_ata_by_name(self, vessel_name):
        vessel_name = vessel_name.strip().upper()
        results = self.completed_movements.loc[(self.completed_movements['SHIP'] == vessel_name) &
            (self.completed_movements['MOVE TYPE'] == "ARRIVAL") &
            (self.completed_movements['MOVE STATUS'] == "COMPLETED")]['MOVE START'].to_frame()
        return results        

    def get_eta(self):
        results = self.expected_movements.loc[self.expected_movements['MOVE TYPE'] == "ARRIVAL"].copy()#['MOVE START'].to_frame()
        results['PORT_ETA'] = results['MOVE START']
        results['PORT'] = 'AUFRE'
        results = results[['PORT','SHIP', 'PORT_ETA']]
        results.columns = ['PORT','SHIP_NAME', 'PORT_ETA']
        return results
    
    def get_in_port(self):
        results = self.ships_in_port.copy()
        results['PORT'] = 'AUFRE'
        results['ARR_DATE'] = self.get_request_time().strftime('%d-%m-%Y %H:%M:%S')#It was sometime before now
        #print(results[['PORT','ARR_DATE','DEPARTURE', 'SHIP']])
        results = results[['PORT','ARR_DATE','DEPARTURE', 'SHIP']]
        results.columns = ['PORT','ARR_DATE','DEP_DATE', 'SHIP_NAME']
        return results  
    
    def refresh_all(self):
        try:
            self.expected_movements = self.refresh_expected_movements()
            self.completed_movements = self.refresh_completed_movements()
            self.ships_in_port = self.refresh_ships_in_port()
        except:
            print("Refresh failed. Loading from file")
            self.expected_movements = pd.read_csv('aufre_expected_movements.csv')
            self.completed_movements = pd.read_csv('aufre_completed_movements.csv')
            self.ships_in_port = pd.read_csv('aufre_ships_in_port.csv')
        if self.debug:
            print(self.expected_movements)
            print(self.completed_movements)
            print(self.ships_in_port)
        self.write_to_csv()
        return True
    
    def write_to_csv(self):
        self.expected_movements.to_csv('aufre_expected_movements.csv', encoding='utf-8', index=False)
        self.completed_movements.to_csv('aufre_completed_movements.csv', encoding='utf-8', index=False)
        self.ships_in_port.to_csv('aufre_ships_in_port.csv', encoding='utf-8', index=False)

    def legacy_process(self, df):
        df = df.loc[df['Move Type'] == 'Arrival']
        df = df[['Ship', 'Move Start']]
        df.columns = ['ship_name', 'port_eta']
        df['ship_name'] = df['ship_name'].str.strip().str.upper()
        df['port'] = 'AUFRE'
        return df
        
def main():
    aufresession = AuFreSession(debug=True)
    #print(aufresession.get_eta_by_name("HOEGH TOKYO"))
    #print(aufresession.get_ata_by_name("UNION TAYLOR"))
    print(aufresession.get_in_port())
    
if __name__ == "__main__":
    main()
    