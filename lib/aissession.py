import asyncio
import websockets
import json
from datetime import datetime, timezone
import json
import yaml

import shipdata

map_path = '/srv/fastapi/public/index.html'


class AisSession:
    def __init__(self,
                 ais_api_key='',
                 db_api_url='',
                 db_api_key='',
                 debug = False):
        self.ais_api_key = ais_api_key
        self.ships = shipdata.ShipData(db_api_url, db_api_key, map_path=map_path)
        if self.ais_api_key:
            asyncio.run(self.connect_ais_stream())
        
    async def connect_ais_stream(self):
        async for websocket in websockets.connect("wss://stream.aisstream.io/v0/stream"):
        #async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
            try:
                print("Starting...")
                subscribe_message = {"APIKey": self.ais_api_key, "BoundingBoxes": [[[-90, -180], [90, 180]]]}
                subscribe_message_json = json.dumps(subscribe_message)
                await websocket.send(subscribe_message_json)
                async for message_json in websocket:
                    message = json.loads(message_json)
                    message_type = message["MessageType"]
                    if message_type == "PositionReport":
                        #print(message['Message']['PositionReport'])
                        self.ships.process_pos_report(message['Message']['PositionReport'])
            except websockets.ConnectionClosed:
                print("Closed")
                continue 

def load_yaml_config(config_filename):
    config = None
    with open(config_filename, "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return config

def load_json_config(config_filename):
    config = None
    with open(config_filename, "r") as jsonfile:
        try:
            config = json.load(jsonfile)
        except Exception as exc:
            print(exc)
    return config

def main():
    config_filename = 'config.json'
    config = load_json_config(config_filename)
    #print(config)
    ais_api_key = config["ais_api_key"]
    db_api_key = config["db_api_key"]
    db_api_url = config["db_api_url_local"]
    aissession = AisSession(ais_api_key, db_api_url, db_api_key)

if __name__ == "__main__":
    main()