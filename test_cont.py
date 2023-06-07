#from tracktrace import ocean
import lib.pdfwaybill as wb
import json
import lib.hlcucontainer as hc

#files = ["MCOP0101_651482249.pdf", 
files = ["MCOP0101_651482615.pdf"]

all_containers = ["FCIU7037660","GATU8241960"]
company = 'HLCU'

for container in all_containers:
    print(container)
    #current_cs = cs.ContSession(container)
    #shipment = ocean.container.create(scac=company, container=container)
    hclu_cont = hc.HLCUContainer(container)
    #print(current_cs)
    #updates =  shipment.updates
    #for update in updates:
    #    print(update)
"""
for file in files:
    current_swb = wb.PdfWaybill(file)
    #print(current_swb.get_containers())
    #print(current_swb.get_vehicles())
    #print(current_swb.get_waybills())
    #json_object = json.dumps(current_swb.get_waybills(), indent = 4) 
    #print(json_object)
    all_containers = current_swb.get_containers().keys()
    for container in all_containers:
        #print(container)
        #if container == "GATU8241960":
        print(container)
        print(type(container))
        current_cs = cs.ContSession(container)
        updates =  current_cs.get_updates()
        for update in updates:
            print(update)
"""