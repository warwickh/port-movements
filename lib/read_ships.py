import json
  
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
