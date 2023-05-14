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

server = 'ivaudan50ssia03.ivecoaustralia.ivecoapac.iveco.com' # to specify an alternate port
database = 'Sales_Logistics' 

params = urllib.parse.quote_plus("DRIVER={SQL Server Native Client 11.0};SERVER=ivaudan50ssia03.ivecoaustralia.ivecoapac.iveco.com;DATABASE=Sales_Logistics;Trusted_Connection=yes;")

#print(params)

engine = db.create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)

with engine.connect() as conn:
    df_dataif3 = pd.read_sql(db.text('SELECT * FROM T_ANZ_DATAIF3'), con = conn)
    df_cow = pd.read_sql(db.text('SELECT * FROM T_Cargo_ONWATER'), con = conn)
    df_bns = pd.read_sql(db.text('SELECT * FROM T_Cargo_Booked_Not_Shipped'), con = conn)
    df_trans = pd.read_sql(db.text('SELECT "Discharge Port Code","Destination Port Code" FROM T_Cargo_ONWATER where "Discharge Port Code"<>"Destination Port Code"'), con = conn)

print(df_dataif3)
print(df_cow)
print(df_bns)
print(df_trans)
