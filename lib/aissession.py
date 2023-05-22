import asyncio
import websockets
import json
from datetime import datetime, timezone
import json
import yaml

import shipdata
   
class AisSession:
    def __init__(self,
                 ais_api_key='',
                 debug = False):
        self.ais_api_key = ais_api_key
        self.ships = shipdata.ShipData()
        if self.ais_api_key:
            asyncio.run(self.connect_ais_stream())
        
    async def connect_ais_stream(self):
        async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
            subscribe_message = {"APIKey": self.ais_api_key, "BoundingBoxes": [[[-180, -90], [180, 90]]]}
            subscribe_message_json = json.dumps(subscribe_message)
            await websocket.send(subscribe_message_json)

            async for message_json in websocket:
                message = json.loads(message_json)
                message_type = message["MessageType"]
                if message_type == "PositionReport":
                    ais_message = message['Message']['PositionReport']
                    self.ships.update_location_by_mmsi(ais_message['UserID'], ais_message['Latitude'], ais_message['Longitude'])

def load_config(config_filename):
    config = None
    with open(config_filename, "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return config

def main():
    config_filename = 'config.yml'
    config = load_config(config_filename)
    ais_api_key = config["ais_api_key"]
    aissession = AisSession(ais_api_key)

if __name__ == "__main__":
    main()