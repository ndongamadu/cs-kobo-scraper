import requests
import pandas as pd
import json
import os

base_url = "https://kc.humanitarianresponse.info/api/v1"
forms_url = "https://kc.humanitarianresponse.info/api/v1/data"

countriesArr = pd.read_csv('countries_list_iso.csv')


def getDataById(formID):
    CS_KOBO_TOKEN = os.environ.get("CS_KOBO_TOKEN")    
    headers = {"Authorization": CS_KOBO_TOKEN}
    url = base_url +"/data/"+formID
    kobo = requests.get(url, headers=headers)
    jsonData = kobo.json()
    with open('data.json') as f:
        data = json.load(f)
    
    go = True
    dataIndex = 0
    while go:
        try:
            data["data"].append(jsonData[dataIndex])
            dataIndex +=1
        except Exception as e:
            print(e)
            go = False

    with open('new_data.json', 'w') as f:
        # f.write(kobo.json())
        json.dump(data,f)
    return 

def replaceValues(val, to_rep, rep_par):
    return str(val).replace(to_rep, rep_par)


def getRegional4WData():
    regional_4W_id= "1023157"
    getDataById(regional_4W_id)

    data_headers = ["_id", "Org/name_org", "Org/Acr_org", "Contact/name_contact", "Contact/role", "Contact/email_contact"]

    with open('new_data.json') as f:
        jsonData = json.load(f)
    
    df = pd.json_normalize(jsonData["data"],"Reporting/repeat", data_headers)
    df = df.merge(countriesArr[["NAME", "ISO3"]], right_on="NAME", left_on="Reporting/repeat/countries")

    for col in ["Reporting/repeat/activity_cat","Reporting/repeat/population"]:
        df[col] = df[col].apply(replaceValues, args=(" ", "|"))

    for col in ["Reporting/repeat/health", "Reporting/repeat/humanitarian", "Reporting/repeat/activity_cat", "Reporting/repeat/population"]:
        df[col] = df[col].apply(replaceValues, args=("_", " "))

    df.to_csv("data_regional4W.csv")
    return 

# def cleanFormData():    
#     with open('new_data.json') as f:
#         jsonData = json.load(f)
#         # jsonData = json.dumps(f, indent=4)
    
#     df = pd.json_normalize(jsonData["data"],"Reporting/repeat", data_headers)
#     df.to_csv("clean_data.csv")

#     return