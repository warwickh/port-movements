from lib import aumelsession, aufresession, aubnesession, aupklsession,nzaklsession,dbsession
import json
import pandas as pd

def convert_config(config_filename):
    config = None
    with open(config_filename, "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    with open('config.json', 'w') as json_file:
        json. dump(config, json_file)
    return config                   

def load_config(config_filename):
    with open(config_filename, 'r') as f:
        config = json.load(f)
    return config

                    
def main():
    debug=False
    config_filename = 'config.json'
    config = load_config(config_filename)
    db_server = config["db_server"]
    database = config["database"]
    aumel = aumelsession.AuMelSession(debug=debug)
    aufre = aufresession.AuFreSession(debug=debug)
    aupkl = aupklsession.AuPklSession(debug=debug)
    nzakl = nzaklsession.NzAklSession(debug=debug)
    aubne = aubnesession.AuBneSession(debug=debug)
    db_session = dbsession.DbSession(db_server, database)
    
    #print(db_session.get_table("T_ANZ_DATAIF3"))
    #print(db_session.get_table("T_Cargo_ONWATER"))
    #print(db_session.get_table("T_Cargo_Booked_Not_Shipped"))
    #print(db_session.get_query('SELECT "Discharge Port Code","Destination Port Code" FROM T_Cargo_ONWATER where "Discharge Port Code"<>"Destination Port Code"'))
    #print(db_session.get_query('SELECT "Vessel Name","B/L No","Origin Port Code","Discharge Port Code","Discharge Port Arrival Date","Destination Port Code" From T_Cargo_ONWATER'))
    onwater_short = db_session.get_query('SELECT "Vessel Name","B/L No","Origin Port Code","Discharge Port Code","Discharge Port Arrival Date","Destination Port Code" From T_Cargo_ONWATER')
    onwater_short["Vessel Name"] = onwater_short["Vessel Name"].apply(db_session.remove_accents).str.strip().str.upper()
    #print(onwater_short)
    #bl = pd.concat(onwater_short["Vessel Name"],onwater_short["B/L No"]).unique()
    #bl = onwater_short.groupby(["Vessel Name","B/L No","Discharge Port Code","Discharge Port Arrival Date","Destination Port Code"]).count().reset_index()
    #bl.columns = bl.columns.str.upper()
    bl = db_session.get_table("T_Cargo_ONWATER")
    bl["Vessel Name"] = bl["Vessel Name"].apply(db_session.remove_accents).str.strip().str.upper()
    
    updates = pd.DataFrame()
    frames=[]
    frames.append(pd.merge(bl, aumel.get_eta(), left_on=['Vessel Name','Discharge Port Code'], right_on=['SHIP_NAME','PORT']))
    frames.append(pd.merge(bl, aufre.get_eta(), left_on=['Vessel Name','Discharge Port Code'], right_on=['SHIP_NAME','PORT']))
    frames.append(pd.merge(bl, aupkl.get_eta(), left_on=['Vessel Name','Discharge Port Code'], right_on=['SHIP_NAME','PORT']))
    frames.append(pd.merge(bl, aubne.get_eta(), left_on=['Vessel Name','Discharge Port Code'], right_on=['SHIP_NAME','PORT']))
    frames.append(pd.merge(bl, nzakl.get_eta(), left_on=['Vessel Name','Discharge Port Code'], right_on=['SHIP_NAME','PORT']))
    updates = pd.concat(frames)
    print(updates)
    cow_upd = pd.merge(bl, updates, how='outer')
    print(cow_upd)
    print(bl)
    cow_upd.to_csv('cow.csv')
    bl.to_csv('bl.csv')
    
if __name__ == "__main__":
    main()