from traceback import format_exc
import requests
import pandas as pd
import json
import os

base_url = "https://kc.humanitarianresponse.info/api/v1"
forms_url = "https://kc.humanitarianresponse.info/api/v1/data"

countriesArr = pd.read_csv('data/countries_list_iso.csv')


def getDataById(formID, dataName):
    CS_KOBO_TOKEN = os.environ.get("CS_KOBO_TOKEN")    
    headers = {"Authorization": CS_KOBO_TOKEN}
    url = base_url +"/data/"+formID
    kobo = requests.get(url, headers=headers)
    jsonData = kobo.json()
    with open('data/data.json') as f:
        data = json.load(f)
    
    go = True
    dataIndex = 0
    while go:
        try:
            data["data"].append(jsonData[dataIndex])
            dataIndex +=1
        except Exception as e:
            go = False

    with open('data/'+dataName+'.json', 'w') as f:
        # f.write(kobo.json())
        json.dump(data,f)
    return 

def replaceValues(val, to_rep, rep_par):
    return str(val).replace(to_rep, rep_par)

def getUsefullColumns(df):
    form_cols = []
    kobo_meta_cols = ['formhub/uuid', 'start', 'end', 'deviceid', 'phonenumber',
        '_xform_id_string', '_uuid', '_attachments', '_status', '_geolocation',
       '_submission_time', '_tags', '_notes', '_submitted_by',
       '_validation_status.timestamp', '_validation_status.uid',
       '_validation_status.by_whom', '_validation_status.color',
       '_validation_status.label', '__version__','meta/instanceID','script']
    df_cols = df.columns
    for c in df_cols:
        if c not in kobo_meta_cols:
            form_cols.append(c)
    return form_cols

def getRegional4WData():
    regional_4W_id= "1023157"
    dataName = "data_regional_4w"
    getDataById(regional_4W_id,dataName)

    data_headers = ["_id", "Org/name_org", "Org/Acr_org", "Contact/name_contact", "Contact/role", "Contact/email_contact"]

    with open('data/'+dataName+'.json') as f:
        jsonData = json.load(f)
    
    df = pd.json_normalize(jsonData["data"],"Reporting/repeat", data_headers)
    df = df.merge(countriesArr[["NAME", "ISO3"]], right_on="NAME", left_on="Reporting/repeat/countries")

    for col in ["Reporting/repeat/activity_cat","Reporting/repeat/population"]:
        df[col] = df[col].apply(replaceValues, args=(" ", "|"))

    for col in ["Reporting/repeat/health", "Reporting/repeat/humanitarian", "Reporting/repeat/activity_cat", "Reporting/repeat/population"]:
        df[col] = df[col].apply(replaceValues, args=("_", " "))

    df.to_csv("data/"+dataName+".csv")
    return 

def getKenya4WData():
    kenya_4w_id= "1056607"
    dataName = "data_kenya_4w"
    partnersArr = ['_id', 'who/reporting_partner', 'partner_001/Org/name_org',
       'partner_001/Org/Acr_org', 'partner_001/Contact/name_contact',
       'partner_001/Contact/role', 'partner_001/Contact/num_contact',
       'partner_001/Contact/email_contact']
    activitiesArr = ['partner_001/Activities/activity']
    locationArr = ['partner_001/coordination/coord_nationwide','partner_001/coordination/coord_county',
       'partner_001/training/train_nationwide','partner_001/training/train_county',
       'partner_001/delivery/deliv_nationwide','partner_001/delivery/deliv_county',
       'partner_001/logistics/log_nationwide','partner_001/logistics/log_county', 
       'partner_001/data/data_nationwide','partner_001/data/data_county',
       'partner_001/rcce/rcce_nationwide','partner_001/rcce/rcce_county',
       'partner_001/regulatory/reg_nationwide','partner_001/regulatory/reg_county',
       'partner_001/monitoring_eval/mon_nationwide','partner_001/monitoring_eval/mon_county',
       'partner_001/surveillance/surv_nationwide','partner_001/surveillance/surv_county']
    actDict = {
        "coord":"coordination",
        "train": "training",
        "deliv": "delivery",
        "log":  "logistics",
        "data": "data",
        "rcce": "rcce",
        "reg":  "regulatory",
        "mon":  "monitoring_eval",
        "surv": "surveillance"
    }

    kenya_counties = "KE030 KE036 KE039 KE040 KE028 KE014 KE007 KE043 KE011 KE034 KE037 KE035 KE022 KE003 KE020 KE045 KE042 KE015 KE002 KE031 KE005 KE016 KE017 KE009 KE010 KE012 KE044 KE001 KE021 KE047 KE032 KE029 KE033 KE046 KE018 KE019 KE025 KE041 KE006 KE004 KE013 KE026 KE023 KE027 KE038 KE008 KE024"
 
    getDataById(kenya_4w_id, dataName)

    with open('data/'+dataName+'.json') as f:
        jsonData = json.load(f)
    
    df = pd.json_normalize(jsonData["data"])
    df = df[df["_validation_status.label"] != "Not Approved"]
    
    keep_cols = getUsefullColumns(df)
    df = df[keep_cols]

    # gen activities subdataset
    # df_act = df[partnersArr + activitiesArr]
    # act_name_Arr = ["act0","act1","act2","act3","act4","act5","act6"]
    # df_act[act_name_Arr] = df_act[activitiesArr[0]].str.split(' ', expand=True)
    # df_act_melted = pd.melt(df_act, id_vars=partnersArr, value_name=activitiesArr[0], value_vars=act_name_Arr)
    # df_act_melted = df_act_melted[df_act_melted[activitiesArr[0]].notnull()]
    # df_act_melted.to_csv("data/"+dataName+"_activities.csv")

    # generate cleaned dataset
    partnersData = df[partnersArr + locationArr]
    for k in actDict:
        val = actDict[k]
        partnersData[val] = partnersData["partner_001/"+val+"/"+k+"_nationwide"].astype(str) +" " + partnersData["partner_001/"+val+"/"+k+"_county"].astype(str)
    
    activity_col_name = "activity"
    county_col_name = "county_code"

    unpivottedActivities = pd.melt(partnersData, id_vars=partnersArr, var_name=activity_col_name,
                     value_name=county_col_name, value_vars=actDict.values())

    unpivottedActivities[county_col_name] = unpivottedActivities[county_col_name].apply(replaceValues, args=("yes__all_counties", kenya_counties))
    unpivottedActivities[county_col_name] = unpivottedActivities[county_col_name].apply(replaceValues, args=("no__some_counties", " "))
    #  remove white spaces
    unpivottedActivities[county_col_name] = unpivottedActivities[county_col_name].str.strip()
    print(unpivottedActivities.head())
    countyArr = []
    i = 0
    while i < 48:
        countyArr.append("county_"+str(i))
        i +=1
    

    unpivottedActivities[countyArr] = unpivottedActivities[county_col_name].str.split(' ', expand=True)

    partnersPlusActivities = partnersArr + [activity_col_name]

    unpivottedCounties = pd.melt(unpivottedActivities, 
        id_vars=partnersPlusActivities,value_name=county_col_name, value_vars=countyArr)
    
    unpivottedCounties = unpivottedCounties[unpivottedCounties[county_col_name] != "nan"]
    unpivottedCounties = unpivottedCounties[unpivottedCounties[county_col_name].notnull()]

    usefull_cols = partnersArr + [activity_col_name, county_col_name]

    unpivottedCounties = unpivottedCounties[usefull_cols]

    unpivottedCounties.to_csv("data/"+dataName+".csv")

    return 


