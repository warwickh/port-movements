import easyocr
import pdf2image
import tempfile
import json
from PyPDF2 import PdfReader
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
import re

"""
Currently using 2 methods for extraction. TODO move main container info to pdfminer extraction

"""

#container_regex = r"([A-Z]{4})\s+([0-9]{7})\s+([0-9]+)\s+UNITS\s+\d+.+\d*\s+SEAL:\s*.*MTQ\s+(\D{3}\d{7})\s+VAN\s*(\d{8})(?:\s*(\d{8}))?\s*SERIAL NR\s*([A-Z,0-9]{17})(?:\s*([A-Z,0-9]{17}))?\s*MODEL\s*([A-Z,0-9]+\s{1}[A-Z,0-9]*)\s*(?:([A-Z,0-9]+\s{1}[A-Z,0-9]*))\s*HS CODE (\d+)"

#container_regex = r"([A-Z]{4})\s+([0-9]{7})\s+([0-9]+)\s+UNITS?.*?VAN.*?(\d{8}).*?(?:(\d{8}).*?)?SERIAL NR.*?([A-Z,0-9]{17}).*?(?:([A-Z,0-9]{17}).*?)?MODEL.*?(\S+\s{1}\S*).*?(?:(\S+\s{1}\S*).*?)?.*?HS\s{1}CODE\s{1}(\d{7,})"

container_regex = r"([A-Z]{4})\s+([0-9]{7})\s+([0-9]+)\s+UNITS?.*?VAN.*?(\d{8}).*?(?:(\d{8}).*?)?SERIAL NR.*?([A-Z,0-9]{17}).*?(?:([A-Z,0-9]{17}).*?)?MODEL.*?(\S+\s{1}\S*).*?(?:\s*(\S{3,}\s{1}\S*).*?)?.*?HS\s{1}CODE\s{1}(\d{7,})"

total_units_regex = r"==\s*(\d+) UNITS?"

swb_no_regex = r"SWB-No. ([A-Z,0-9]+)"

class PdfWaybill:
    def __init__(self,
                 infile_name="",
                 debug = False):
        self.containers = {}
        self.vehicles = {}
        self.waybills = {}
        self.ports = {}
        self.total_units = 0
        self.text = {}
        self.swb_no = ""
        self.loaded = False
        self.infile_name = infile_name
        if infile_name:
            if self.load_ports():
                self.reader = PdfReader(infile_name)
                self.load_text()
                self.loaded = self.load_containers()
            else:
                print("Ports not loaded correctly")
        else:
            print("Init without file")
        if self.loaded:
            print("Successfully loaded %s vehicles into %s containers"%(self.total_units, len(self.containers)))

    def load_file(self, infile_name):
        self.infile_name = infile_name
        self.reader = PdfReader(infile_name)
        self.load_text()
    
    def get_containers(self):
        if not self.loaded:
            return None
        return self.containers

    def get_vehicles(self):
        if not self.loaded:
            return None
        return self.vehicles

    def get_waybills(self):
        if not self.loaded:
            return None
        return self.waybills
       
    def load_containers(self):
        containers = {}
        vehicles = {}
        #waybills = {}
        total_units = 0
        #print(self.text)
        for page in self.text.keys():
            results = re.findall(container_regex,self.text[page])
            print("Page %s results: %s"%(page, len(results)))
            for result in results:
                cont_vehicles = {}
                #print("Result: %s"%result)
                units_in_cont = int(result[2])
                for unit in range(units_in_cont):
                    #print("processing %s %s"%(unit,result))
                    van_ind = 3+unit#+(0*units_in_cont)#2+2 or 2+1
                    vin_ind = 5+unit#+(1*units_in_cont)#2+4 or 2+2
                    mod_ind = 7+unit#+(2*units_in_cont)#2+6 or 2+3
                    #print("processing vin %s %s"%(unit,result[vin_ind]))
                    #print("vehicle %s at %s %s %s"%(unit, van_ind, vin_ind, mod_ind))
                    vehicles[result[vin_ind]] = {"vin": result[vin_ind], "vanext": result[van_ind], "model": result[mod_ind]}
                    cont_vehicles[result[vin_ind]] = {"vin": result[vin_ind], "vanext": result[van_ind], "model": result[mod_ind]}
                containers["%s%s"%(result[0], result[1])] = cont_vehicles
            #print(vehicles)
            swb_no = re.findall(swb_no_regex,self.text[page])
            if(len(swb_no))>0:
                self.swb_no = swb_no[0]
                print(self.swb_no)
            total_units = re.findall(total_units_regex,self.text[page])
            if(len(total_units))>0:
                self.total_units = total_units[0]
        self.vehicles = vehicles
        self.containers = containers
        self.waybills[self.swb_no]={}
        self.waybills[self.swb_no]["vehicles"]= self.vehicles
        self.waybills[self.swb_no]["containers"]= self.containers
        self.waybills[self.swb_no]["ports"] = self.ports
        #print(self.containers)
        #print(self.waybills)
        #print(len(self.vehicles))
        #print(self.total_units)
        return len(self.vehicles) == (int(self.total_units))

    def load_text(self):
        text = {}
        for page in range(len(self.reader.pages)):
            text[page] = self.reader.pages[page].extract_text(0).replace("\n","")
            self.save_page(page, text[page])
        self.text = text         
        #print(len(self.text))
        #print(self.text)
        self.loaded = True

    def save_page(self, page, text):
       with open("%s_%s.txt"%(self.infile_name, page), "w") as f:
        f.write(text)

    def load_ports(self):
        fp = open(self.infile_name, 'rb')
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        pages = PDFPage.get_pages(fp)
        interpreter.process_page(next(pages))
        layout = device.get_result()
        for lobj in layout:
            if isinstance(lobj, LTTextBox) and 7<=lobj.bbox[0]<=8 and 16<=lobj.bbox[1]<=17:
                for line in lobj:
                    if isinstance(line, LTTextLine):
                        if 7<=line.bbox[0]<=8 and 451<=line.bbox[1]<=452:
                            print("Origin: %s"%line.get_text().strip())
                            self.ports["origin"] = line.get_text().strip()
                        if 7<=line.bbox[0]<=8 and 427<=line.bbox[1]<=428:
                            print("Dest: %s"%line.get_text().strip())
                            self.ports["dest"] = line.get_text().strip()
        return self.ports["origin"] and self.ports["dest"]
        
def main():
    files = ["MCOP0101_651482249.pdf", "MCOP0101_651482615.pdf"]
    for file in files:
        pdfwaybill = PdfWaybill(file)
        #print(pdfwaybill.get_containers())
        #print(pdfwaybill.get_vehicles())
        #print(pdfwaybill.get_waybills())
        json_object = json.dumps(pdfwaybill.get_waybills(), indent = 4) 
        print(json_object)

if __name__ == "__main__":
   main()
    