#!/usr/bin/env python3

"""
Identify trans shipments dest port <> dischsarge port

Store original source port

Hande estimation of trans shipment eta

Update eta based on port data

"""

import urllib
import sqlalchemy as db
import pandas as pd
import yaml
import unidecode

class DbSession:
    def __init__(self,
                 db_server = None,
                 database = None,
                 debug = False):
        self.db_server = db_server
        self.database = database
        self.conn = None
        self.connect()

    def connect(self):
        self.params = "DRIVER={SQL Server Native Client 11.0};SERVER=%s;DATABASE=%s;Trusted_Connection=yes;"%(self.db_server, self.database)
        self.engine = db.create_engine("mssql+pyodbc:///?odbc_connect=%s" % self.params)
        self.conn = self.engine.connect()

    def get_table(self, table_name):
        return pd.read_sql(db.text('SELECT * FROM %s'%table_name), con = self.conn)
        
    def get_query(self, query):
        return pd.read_sql(db.text(query), con = self.conn)
    
    def remove_accents(self,a):
        return unidecode.unidecode(a)

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
    db_server = config["db_server"]
    database = config["database"]
    db_session = DbSession(db_server, database)
    print(db_session.get_table("T_ANZ_DATAIF3"))
    print(db_session.get_table("T_Cargo_ONWATER"))
    print(db_session.get_table("T_Cargo_Booked_Not_Shipped"))
    #print(db_session.get_query('SELECT "Discharge Port Code","Destination Port Code" FROM T_Cargo_ONWATER where "Discharge Port Code"<>"Destination Port Code"'))
    print(db_session.get_query('SELECT "Vessel Name","B/L No","Origin Port Code","Discharge Port Code","Discharge Port Arrival Date","Destination Port Code" From T_Cargo_ONWATER'))
    onwater_short = db_session.get_query('SELECT "Vessel Name","B/L No","Origin Port Code","Discharge Port Code","Discharge Port Arrival Date","Destination Port Code" From T_Cargo_ONWATER')
    onwater_short["Vessel Name"] = onwater_short["Vessel Name"].apply(db_session.remove_accents).str.strip().str.upper()
    print(onwater_short)
    #bl = pd.concat(onwater_short["Vessel Name"],onwater_short["B/L No"]).unique()
    bl = onwater_short.groupby(["Vessel Name","B/L No","Discharge Port Code","Discharge Port Arrival Date","Destination Port Code"]).count().reset_index()
    print(bl)
    
if __name__ == "__main__":
    main()