import asyncio
import websockets
import json
from datetime import datetime, timezone
import json
import yaml

def get_ship_data():  
    with open('ships.json') as f:
        data = json.load(f)
        mmsi_data = {}
        #print(data)
        for i in data['data']:
            if "HOEGH" in i['SHIPNAME'].upper():
                #print("%s %s"%(i['SHIPNAME'], i['MMSI']))
                mmsi = i['MMSI']
                shipname = i['SHIPNAME']
                mmsi_data[mmsi] = shipname
    print(mmsi_data)
    return mmsi_data

def load_config(config_filename):
    config = None
    with open(config_filename, "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return config

async def connect_ais_stream(ais_api_key):
    mmsi_data={'257711000': 'HOEGH ASIA', '258720000': 'HOEGH BANGKOK', '257674000': 'HOEGH BEIJING', '258106000': 'HOEGH BERLIN', '257824000': 'HOEGH CHIBA', '257368000': 'HOEGH COPENHAGEN', '257869000': 'HOEGH DETROIT', '258977000': 'HOEGH JACKSONVILLE', '258975000': 'HOEGH JEDDAH', '258981000': 'HOEGH LONDON', '259709000': 'HOEGH MANILA', '257560000': 'HOEGH NEW YORK', '259739000': 'HOEGH OSLO', '257496000': 'HOEGH SEOUL', '258758000': 'HOEGH SHANGHAI', '257366000': 'HOEGH ST.PETERSBURG', '257864000': 'HOEGH TARGET', '257408000': 'HOEGH TOKYO', '258628000': 'HOEGH TRACER', '258882000': 'HOEGH TRADER', '257712000': 'HOEGH TRANSPORTER', '258872000': 'HOEGH TRAPPER', '259075000': 'HOEGH TRAVELLER', '257713000': 'HOEGH TRIDENT', '258389000': 'HOEGH TRIGGER', '257714000': 'HOEGH TROOPER','259274000': 'HOEGH TROTTER', '258774000': 'HOEGH TROVE'}
    port_data={'AUPKL': {'Latitude': '-34.46346', 'Longitude': '150.901482691176'}, 'AUMEL': {'Latitude': '-37.81325655', 'Longitude': '144.924152576608'}, 'AUBNE': {'Latitude': '-27.385741', 'Longitude': '153.17374430786'}, 'NZAKL': {'Latitude': '-36.9323169', 'Longitude': '174.784926235455'}, 'AUFRE': {'Latitude': '-32.0307289', 'Longitude': '115.7480727'}
    async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
        subscribe_message = {"APIKey": ais_api_key, "BoundingBoxes": [[[-180, -90], [180, 90]]]}

        subscribe_message_json = json.dumps(subscribe_message)
        await websocket.send(subscribe_message_json)

        async for message_json in websocket:
            message = json.loads(message_json)
            message_type = message["MessageType"]

            if message_type == "PositionReport":
                ais_message = message['Message']['PositionReport']
                #print(type(ais_message['UserID']))
                #if 260000000>ais_message['UserID']>258000000:
                if str(ais_message['UserID']) in mmsi_data.keys():
                    # the message parameter contains a key of the message type which contains the message itself
                    print(ais_message)
                    print(f"[{datetime.now(timezone.utc)}] ShipName: {mmsi_data[str(ais_message['UserID'])]} ShipId: {ais_message['UserID']} Latitude: {ais_message['Latitude']} Longitude: {ais_message['Longitude']}")
                    #print(type(ais_message['UserID']))
                    #print(mmsi_data[str(ais_message['UserID'])])

if __name__ == "__main__":
    #mmsi_data = get_ship_data()
    config_filename = 'config.yml'
    config = load_config(config_filename)
    ais_api_key = config["ais_api_key"]
    asyncio.run(connect_ais_stream(ais_api_key))