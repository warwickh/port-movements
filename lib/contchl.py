#!/usr/bin/env python3

import requests 
from bs4 import BeautifulSoup 
import pickle
from datetime import datetime, date, timezone, timedelta
import time
import os
import re
import pandas as pd


class ContChlngSession:
    def __init__(self,
                sessionFile='hl_cf_session.dat',
                 maxSessionTimeSeconds = 60 * 30,
                 debug = False):
        self.baseUrl = "https://www.hapag-lloyd.cn/en/online-business/track/track-by-container-solution.html"
        self.challengeUrl = "http://192.168.25.18:8002/challenge"
        self.debug = debug
        self.maxSessionTime = maxSessionTimeSeconds  
        self.sessionFile = sessionFile
        self.cookies = {}
        self.headers = {}
        self.ua = ""
        #self.refresh_cookies()
        self.get_session()
        
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
                    self.cookies = requests.utils.dict_from_cookiejar(self.session.cookies)  # turn cookiejar into dict
                    self.headers = self.session.headers
                    if self.debug:
                        print("loaded session from cache (last access %ds ago) "%lastModification)
                        print(self.cookies)
                        print(self.headers)
        if not wasReadFromCache:
            self.session = requests.Session()
            self.refresh_cookies()
            cookies = requests.utils.cookiejar_from_dict(self.cookies)  # turn dict to cookiejar
            self.session.cookies.update(cookies)
            self.session.headers.update(self.headers)
            if self.debug:
                print('created new session')
                print(self.session.cookies)
                print(self.session.headers)
            self.saveSessionToCache()

    def saveSessionToCache(self):
        with open(self.sessionFile, "wb") as f:
            pickle.dump(self.session, f)
            if self.debug:
                print('updated session cache-file %s' % self.sessionFile)

    def retrieveContent(self, url, timeout = 120):
        #print("compare %s to %s"%(self.headers, self.session.headers))
        #print("compare %s to %s"%(self.cookies, requests.utils.dict_from_cookiejar(self.session.cookies)))
        
        #resp = self.session.get(url, headers=self.headers, cookies=self.cookies)
        resp = self.session.get(url)
        self.saveSessionToCache()           
        return resp

    def doChallenge(self, url, timeout = 120):
        resp = self.session.post(self.challengeUrl,json={"timeout": timeout,"url": url})
        return resp

    def refresh_cookies(self):
        #resp = requests.post(self.challengeUrl,json={"timeout": 120,"url": self.baseUrl})
        resp = self.doChallenge(self.baseUrl, timeout=120)
        resp_json = resp.json()
        print(resp_json)
        if resp_json.get("success"):
            self.ua = resp_json.get("user_agent")
            self.cookies = resp_json.get("cookies") 
            self.headers = {
                'authority': 'www.hapag-lloyd.cn',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                'cache-control': 'max-age=0',
                'referer': self.baseUrl,
                'user-agent': self.ua,
            }
        return resp
          
    def get_updates(self, container):
        print("Getting updates for %s"%container)
        updates = {}
        data_url = "%s?container=%s"%(self.baseUrl,container)
        #res = requests.get(data_url, headers=self.headers, cookies=self.cookies)
        resp = self.retrieveContent(data_url, timeout=120)
        if '<title>Just a moment...</title>' in resp.text:
            print("Cookies not valid, refreshing. Please wait, this may take a while")
            self.refresh_cookies()
            data_url = "%s?container=%s"%(self.baseUrl,container)
            #res = requests.get(data_url, headers=self.headers, cookies=self.cookies)
            resp = self.retrieveContent(data_url, timeout=120)
            if '<title>Just a moment...</title>' in resp.text:
                print("Refresh failed, quitting")
                return {}
        with open('%s_status.txt'%container, 'w', encoding="utf-8") as f:
            f.write(resp.text)
        update_table = pd.read_html(resp.text, attrs={"id": "tracing_by_container_f:hl66"})[0]
        update_table = update_table[update_table['Status'].notna()]
        updates = update_table.to_dict('records')
        return updates

def main():
    containers = ["FCIU7037660","TCLU8072263"]
    current_cs = ContChlngSession(debug=True)
    for container in containers:
        updates = current_cs.get_updates(container)
        #print(updates)
        for update in updates:
            print(update)
    
if __name__ == "__main__":
    main()
    