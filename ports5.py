import os, time
import requests, pickle
import requests.cookies
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timezone, timedelta
import unidecode
import pytz
import re
import certifi

port_list = ['aubne','aumel','aufre','aupkl', 'nzakl']

mel_exp_headers = ['status','actl_mvmt_start_datetime','movement_type','ship_name','berth_name_from','next_port_name','agent']
bne_headers = ["Voyage Id","Id","Job Type","Ship","Ship Type","LOA","Agency","Start Time","End Time","From Location","To Location","Status","Last Port","Next Port","Voyage #","Vessel Id","Status Type"]
fre_headers = ["Id","Visit #","Ship","Ship Type","Move Type","Move Status","Move Start","From Location","To Location","Agency","Last Port","Next Port","Vessel Id"]

def remove_accents(a):
    return unidecode.unidecode(a)
    
def convert_string_time(value):
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
        
def convert_unix_time(value):
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

def load_aubne():
    filename = 'aubne.csv'
    df = pd.read_csv(filename, encoding='utf-8')
    df = df.loc[df['Job Type'] == 'ARR']
    df = df[['Ship', 'Start Time']]
    df.columns = ['ship_name', 'port_eta']
    df['ship_name'] = df['ship_name'].str.strip().str.upper()
    df['port'] = 'AUBNE'
    return df

def load_aumel():
    filename = 'aumel.csv'
    df = pd.read_csv(filename, encoding='utf-8')
    df = df.loc[df['movement_type'].str.strip() == 'Arrival']
    df['port_eta'] = df['actl_mvmt_start_datetime'].str.strip().apply(convert_string_time)
    #df['port_eta'] = datetime.strptime(df['actl_mvmt_start_datetime'], '%d-%m-%Y %H:%M:%S')
    #df.columns = ['ship_name', 'port_eta']
    df['ship_name'] = df['ship_name'].str.strip().str.upper()
    df = df[['ship_name', 'port_eta']]
    df['port'] = 'AUMEL'
    return df

def load_aufre():
    filename = 'aufre.csv'
    df = pd.read_csv(filename, encoding='utf-8')
    df = df.loc[df['Move Type'] == 'Arrival']
    df = df[['Ship', 'Move Start']]
    df.columns = ['ship_name', 'port_eta']
    df['ship_name'] = df['ship_name'].str.strip().str.upper()
    df['port'] = 'AUFRE'
    return df

def load_nzakl():
    filename = 'nzakl.csv'
    df = pd.read_csv(filename, encoding='utf-8')
    df = df[['Vessel', 'Arrival']]
    df.columns = ['ship_name', 'port_eta']
    df['ship_name'] = df['ship_name'].str.strip().str.upper()
    df['port'] = 'NZAKL'
    return df
    
def load_aupkl():
    filename = 'aupkl.csv'
    df = pd.read_csv(filename, encoding='utf-8')
    df = df.loc[df['movementType'] == 'Arrival']
    df['port_eta'] = df['time'].str.strip().apply(convert_string_time)
    df = df[['vesselName', 'port_eta']]
    df.columns = ['ship_name', 'port_eta']
    df['ship_name'] = df['ship_name'].str.strip().str.upper()
    df['port'] = 'AUPKL'
    return df

def update_aupkl():
    log_name = 'aupkl'
    url = 'https://www.portauthoritynsw.com.au/umbraco/Api/VesselMovementAPI/GetApiVesselMovement?portCode=P04'
    pkl_data = pd.read_json(url)
    df = pd.json_normalize(pkl_data['items'])
    #export_table("pkl_eta", df)
    filename = '%s.csv'%log_name
    df.to_csv(filename, encoding='utf-8', index=False)
    return df

def update_aumel():
    log_name = 'aumel'
    url='https://www.vicports.vic.gov.au/ShipMovementLogs/www_expected_movements.log'
    df = pd.read_csv(url, skiprows=2, names=mel_exp_headers)
    filename = '%s.csv'%log_name
    df.to_csv(filename, encoding='utf-8', index=False)
    return df

def update_aubne():    
    log_name = 'aubne'
    get_session_url = "https://qships.tmr.qld.gov.au/webx/"
    get_data_url = "https://qships.tmr.qld.gov.au/webx/services/wxdata.svc/GetDataX"
    get_data_query = {
        "token": None,
        "reportCode": "MSQ-WEB-0001",
        "dataSource": None,
        "filterName": "Next 7 days",
        "parameters": [{
                "__type": "ParameterValueDTO:#WebX.Core.DTO",
                "sName": "DOMAIN_ID",
                "iValueType": 0,
                "aoValues": [{"Value": "67"}],
                      }],
        "metaVersion": 0,
    }
    sess = requests.session()
    sess.get(get_session_url).raise_for_status()
    data = sess.post(get_data_url, json = get_data_query).json()
    df = pd.DataFrame(data['d']['Tables'][0]['Data'])
    df.columns = bne_headers
    df['Start Time'] = df['Start Time'].apply(convert_unix_time)#(tz_string, value):
    df['End Time'] = df['End Time'].apply(convert_unix_time)#(tz_string, value):
    filename = '%s.csv'%log_name
    df.to_csv(filename, encoding='utf-8', index=False)
    return df

def update_aufre():    
    log_name = 'aufre'
    get_session_url = "https://www3.fremantleports.com.au/VTMIS/dashb.ashx?db=fmp.public&btn=ExpectedMovements"
    get_data_url = "https://www3.fremantleports.com.au/VTMIS/services/wxdata.svc/GetDataX"
    get_data_query = {
        'request': {
            'requestID': '1677543485822-10',
            'reportCode': 'FMP-WEB-0001',
            'dataSource': None,
            'filterName': None,
            'parameters': [
                {
                    '__type': 'ParameterValueDTO:#WebX.Core.DTO',
                    'sName': 'FROM_TIME',
                    'iValueType': 0,
                    'aoValues': [
                        {
                            '__type': 'ValueItemDTO:#WebX.Core.DTO',
                            'Value': '2023-02-28T00:00:00.000',
                        },
                    ],
                },
                {
                    '__type': 'ParameterValueDTO:#WebX.Core.DTO',
                    'sName': 'TO_TIME',
                    'iValueType': 0,
                    'aoValues': [
                        {
                            '__type': 'ValueItemDTO:#WebX.Core.DTO',
                            'Value': '2023-03-29T23:59:59.000',
                        },
                    ],
                },
            ],
            'metaVersion': 0,
            '_type': 'TGetDataXREQ:#WebX.Services',
            'stamp': 'CYsBAAAAAAARAGjWYkLxNhR/6IU30XmtByv2fg2BtwAFUENbctkUJcVMG9kh/8BAOSKsv7/U9YWCbNwlVkav4Fdsw93pG6S1mn5harS5cNueJgRxQo3pdNjZ4oTUYbj0Qx0ftyqJDAnyStTxYfnXjeNa2MUTZBnzjFtgKp+tslddqUU91CWWDEIm58o0MIAajZ3TigXcsIGSoom71UvTNzny7oFup3jYQjfNSOWDo3feZ3X3dlVmgRHSrMdzrXjbmsKGu6K1xBJm+ZWb81PH2dlnXomOneumW0NILT25J1FyWt2pns/Db3B9O6jam2DSv43zhwrKDGZinescd3QgNz2stB20LTpPOsirEPMK4RHEHnUTVFhatDJy+CbJwRY0VN/4NQx1z7OJ0v7C57K+2UR5MnbKMK7zVKKoPNzRGwNqfrWXHdSq6hCy8JpIWoiyk+stI9Xw29k4p+sp4j9u07f1sWu53xgy6jpse2VxbV2bDkvKCpq/x3o7RnEQITt8seA+cAZISpspz1/IMOoSm9SAfqBpIycCSmr7XFtEmG5q7WcIgz6gAkdFSyKE+lQUlaMT6SnwrJ/DwJluMNEFBFvEPIPIJp+SRoWwb9Nrrybh0xnJtHNpyWuJCXj7I4c2EgAA\vfmp.public/main-view',
        },
    }
    sess = requests.session()
    #sess.get(get_session_url, verify=False).raise_for_status()
    #data = sess.post(get_data_url, json = get_data_query, verify=False).json()
    sess.get(get_session_url).raise_for_status()
    data = sess.post(get_data_url, json = get_data_query).json()
    print(data)
    df = pd.DataFrame(data['d']['Tables'][0]['Data'])
    df.columns = fre_headers
    #df['Start Time'] = df['Start Time'].apply(convert_time)#(tz_string, value):
    df['Move Start'] = df['Move Start'].apply(convert_unix_time)#(tz_string, value):
    filename = '%s.csv'%log_name
    df.to_csv(filename, encoding='utf-8', index=False)
    return df

def update_nzakl():
    log_name = 'nzakl'
    url = 'https://www.poal.co.nz/operations/schedules/arrivals'
    sess = requests.session()
    #sess.get(url, verify=False).raise_for_status()
    #data = sess.get(url, verify=False)
    sess.get(url).raise_for_status()
    data = sess.get(url)
    df = pd.read_html(data.text)[0]
    #df['port_eta'] = df['Arrival'].str.strip().apply(convert_string_time)
    filename = '%s.csv'%log_name
    df.to_csv(filename, encoding='utf-8', index=False)
    return df

def refresh_all_ports():
    for port in port_list:
        current_filename = '%s.csv'%port
        if not os.path.isfile(current_filename):
            globals()['update_%s'%port]()
        modificationTime = os.path.getmtime(current_filename)
        age_mins = (datetime.now().timestamp() - modificationTime) / 60
        file_age = timedelta(minutes=age_mins)
        print("File age %s"%file_age)
        if(age_mins>120):
            print("File for %s is over 120 mins, refresh.."%port)
            globals()['update_%s'%port]()
        else:
            print("File for %s is under 120 mins"%port)

def get_report(filename):
    df = pd.read_excel(filename)
    df['ship_name'] = df['Vessel Name'].str.upper().apply(remove_accents)
    df['Vessel Name'] = df['Vessel Name'].apply(remove_accents)
    df['port'] = df['Discharge Port Code']
    return df


def process_port(cargo_on_water, cargo_on_water_upd, data):
    #data.to_csv('datamel.csv', encoding='utf-8', index=False)
    upd = pd.merge(cargo_on_water, data, on=['port','ship_name'], how='left')
    #upd.to_csv('upd.csv', encoding='utf-8', index=False)
    #cargo_on_water.to_csv('cargo_on_water.csv', encoding='utf-8', index=False)
    cols_to_use = cargo_on_water_upd.columns.difference(upd.columns)
    cargo_on_water_upd = pd.merge(cargo_on_water_upd, upd['port_eta'], left_index=True, right_index=True, how='outer')
    cargo_on_water_upd['port_eta_y'] = cargo_on_water_upd['port_eta_y'].fillna(cargo_on_water_upd['port_eta_x'])
    cargo_on_water_upd.drop(['port_eta_x'],inplace=True,axis=1)
    cargo_on_water_upd.rename(columns={'port_eta_y':'port_eta'},inplace=True)
    return cargo_on_water_upd

def main():
    cargo_on_water_path = r'Iveco Custom Report - Cargo on water.xlsx'
    cargo_on_water = get_report(cargo_on_water_path)
    refresh_all_ports()
    print("Cargo On Water Input")
    print(cargo_on_water)
    data_aubne = load_aubne()
    print("AUBNE")
    print(data_aubne[data_aubne['ship_name'].str.contains("HOEGH")])
    data_aufre = load_aufre()
    print("AUFRE")
    print(data_aufre[data_aufre['ship_name'].str.contains("HOEGH")])
    data_aupkl = load_aupkl()
    print("AUPKL")
    print(data_aupkl[data_aupkl['ship_name'].str.contains("HOEGH")])   
    data_aumel = load_aumel()
    print("AUMEL")
    print(data_aumel[data_aumel['ship_name'].str.contains("HOEGH")])       
    data_nzakl = load_nzakl()
    print("NZAKL")
    print(data_nzakl[data_nzakl['ship_name'].str.contains("HOEGH")])       
    cargo_on_water_upd = cargo_on_water.copy(deep=True)
    cargo_on_water_upd['port_eta'] = ''
    #cargo_on_water_upd.to_csv('check0.csv', encoding='utf-8', index=False)
    cargo_on_water_upd = process_port(cargo_on_water, cargo_on_water_upd, data_aufre)
    #cargo_on_water_upd.to_csv('check1.csv', encoding='utf-8', index=False)
    cargo_on_water_upd = process_port(cargo_on_water, cargo_on_water_upd, data_aubne)
    #cargo_on_water_upd.to_csv('check2.csv', encoding='utf-8', index=False)
    cargo_on_water_upd = process_port(cargo_on_water, cargo_on_water_upd, data_aumel)
    #cargo_on_water_upd.to_csv('check3.csv', encoding='utf-8', index=False)
    cargo_on_water_upd = process_port(cargo_on_water, cargo_on_water_upd, data_aupkl)
    #cargo_on_water_upd.to_csv('check4.csv', encoding='utf-8', index=False)
    cargo_on_water_upd = process_port(cargo_on_water, cargo_on_water_upd, data_nzakl)
    cargo_on_water_upd.to_csv('cargo_on_water.csv', encoding='utf-8', index=False)
    
if __name__ == "__main__":
    main()