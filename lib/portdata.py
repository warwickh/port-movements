import json
import requests
import ast

class PortData:
    def __init__(self,
                 db_api_url='',
                 db_api_key='',
                 debug = False):
        self.port_data_file = 'ports.json'
        self.port_data = None
        self.db_api_key = db_api_key
        self.db_api_url = db_api_url
        self.port_data = self.load_ports_db()
        
    def load_ports(self):
        with open(self.port_data_file, encoding="utf8") as f:
            data = json.load(f)
            return data

    def load_ports_db(self):
        resp = self.get_data('port/')
        data = ast.literal_eval(resp.replace(':false', ':False').replace(':true', ':True'))
        #print(data)
        return data

    def get_ports(self):
        return self.port_data
        
    def get_alias(self, port):
        return ""

    def send_to_db(self):
        for port_code in self.port_data.keys():
            port = self.port_data[port_code]
            new_port = {}
            new_port['port_code'] = port_code
            new_port['name'] = port['name']
            new_port['city'] = port['city']
            
            new_port['country'] = port['country']
            try:
                new_port['timezone'] = port['timezone']
            except:
                new_port['timezone'] = ''
            try:
                new_port['code'] = int(port['code'])
                new_port['province'] = port['province']
            except:
                new_port['code'] = 0
                new_port['province'] = 0            
            new_port['alias'] = self.get_alias(port)
            try:
                new_port['lon'] = port['coordinates'][0]
                new_port['lat'] = port['coordinates'][1]
                #print(port_code)
                #print(self.port_data[port_code])
                #print(port)
                #print(new_port)
                self.post_data('port/', new_port)
            except:
                pass

    def get_data(self, get_url):
        url = "%s/%s"%(self.db_api_url,get_url)
        response = requests.get(url)
        print(response)
        #print(response.text)
        return response.text
        
    def post_data(self, post_url, message):
        url = "%s/%s"%(self.db_api_url,post_url)
        #print(url)
        headers = {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer %s'%self.db_api_key
        }
        response = requests.post(url, headers=headers, json=message)
        print(response)
        print(response.text)
        return (response.status_code == 200)

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
    db_api_key = config["db_api_key"]
    db_api_url = config["db_api_url"]
    port_data = PortData(db_api_url, db_api_key)
    port_data.send_to_db()

if __name__ == "__main__":
    main()