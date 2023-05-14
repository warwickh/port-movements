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
        perthTimeNow = dateTime.replace(tzinfo=tzObject)
        print(perthTimeNow.isoformat("T","auto"))
        print(perthTimeNow.isoformat("T","milliseconds"))

    def get_report(self, report_code, from_time, to_time):
        headers = ["ID","VISIT #","SHIP","SHIP TYPE","MOVE TYPE","MOVE STATUS","MOVE START","FROM LOCATION","TO LOCATION","AGENCY","LAST PORT","NEXT PORT","VESSEL ID"]
        res = self.retrieveContent(self.baseUrl)
        soup = BeautifulSoup(res.text, "html.parser") 
        for script in soup.find_all("script"):
            if script.string is not None and "scope.__stamp" in script.string:
                scope_stamp = re.findall(r"scope.__stamp = \'([^\']*)';", str(script.string))[0]       
        request_id = "%13d-%d"%(int(datetime.now().timestamp() * 1000),random.randint(1,10))
        get_data_query = {'request': {'requestID': request_id, 'reportCode': report_code, 'dataSource': None, 'filterName': None,
            'parameters': [{'__type': 'ParameterValueDTO:#WebX.Core.DTO', 'sName': 'FROM_TIME', 'iValueType': 0, 
            'aoValues': [{'__type': 'ValueItemDTO:#WebX.Core.DTO', 'Value': from_time,}, ],},
                {'__type': 'ParameterValueDTO:#WebX.Core.DTO','sName': 'TO_TIME', 'iValueType': 0, 'aoValues': [{'__type': 'ValueItemDTO:#WebX.Core.DTO','Value': to_time,},],},],
            'metaVersion': 0, '_type': 'TGetDataXREQ:#WebX.Services', 'stamp': "%s\u000bfmp.public/main-view"%scope_stamp,},}
        res = self.retrieveContent(self.dataUrl, method="post", postData=get_data_query)
        data = res.json()
        #print(data)
        df = pd.DataFrame(data['d']['Tables'][0]['Data'])
        df.columns = headers
        df['MOVE START'] = df['MOVE START'].apply(self.convert_unix_time)#(tz_string, value):
        for column in df.columns:
            try:
                df[column] = df[column].str.strip().str.upper()
            except:
                pass
        filename = 'aufre_%s.csv'%report_code
        df.to_csv(filename, encoding='utf-8', index=False)
        print(df)
        return df
        
    def get_expected_movements(self):
        report_code = 'FMP-WEB-0001' 
        return self.get_report(report_code, self.next_week()[0], self.next_week()[1])

    def get_completed_movements(self):
        report_code = 'FMP-WEB-0002'   
        return self.get_report(report_code, self.last_week()[0], self.last_week()[1])

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

    def refresh_all(self):
        self.expected_movements = self.get_expected_movements()
        self.completed_movements = self.get_completed_movements()
        return True

    def legacy_process(self, df):
        df = df.loc[df['Move Type'] == 'Arrival']
        df = df[['Ship', 'Move Start']]
        df.columns = ['ship_name', 'port_eta']
        df['ship_name'] = df['ship_name'].str.strip().str.upper()
        df['port'] = 'AUFRE'
        return df
        
def main():
    aufresession = AuFreSession(debug=True)
    print(aufresession.get_eta_by_name("HOEGH TOKYO"))
    print(aufresession.get_ata_by_name("UNION TAYLOR"))
    
if __name__ == "__main__":
    main()
    