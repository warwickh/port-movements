import asyncio
import websockets
import json
from datetime import datetime, timezone
import json

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

async def connect_ais_stream():
    mmsi_data={'257711000': 'HOEGH ASIA', '258720000': 'HOEGH BANGKOK', '257674000': 'HOEGH BEIJING', '258106000': 'HOEGH BERLIN', '257824000': 'HOEGH CHIBA', '257368000': 'HOEGH COPENHAGEN', '257869000': 'HOEGH DETROIT', '258977000': 'HOEGH JACKSONVILLE', '258975000': 'HOEGH JEDDAH', '258981000': 'HOEGH LONDON', '259709000': 'HOEGH MANILA', '257560000': 'HOEGH NEW YORK', '259739000': 'HOEGH OSLO', '257496000': 'HOEGH SEOUL', '258758000': 'HOEGH SHANGHAI', '257366000': 'HOEGH ST.PETERSBURG', '257864000': 'HOEGH TARGET', '257408000': 'HOEGH TOKYO', '258628000': 'HOEGH TRACER', '258882000': 'HOEGH TRADER', '257712000': 'HOEGH TRANSPORTER', '258872000': 'HOEGH TRAPPER', '259075000': 'HOEGH TRAVELLER', '257713000': 'HOEGH TRIDENT', '258389000': 'HOEGH TRIGGER', '257714000': 'HOEGH TROOPER','259274000': 'HOEGH TROTTER', '258774000': 'HOEGH TROVE'}
     
    async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
        subscribe_message = {"APIKey": "7d11430df0181f6f32e3f8ce9ec462815cc3e563", "BoundingBoxes": [[[-180, -90], [180, 90]]]}

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
                    print(f"[{datetime.now(timezone.utc)}] ShipId: {ais_message['UserID']} Latitude: {ais_message['Latitude']} Longitude: {ais_message['Longitude']}")
                    print(mmsi_data[ais_message['UserID']])

if __name__ == "__main__":
    #mmsi_data = get_ship_data()
    asyncio.run(connect_ais_stream())