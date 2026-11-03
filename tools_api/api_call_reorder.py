import requests
import hashlib
import logging
import json

# Script de test pour reordonner les resources un dataset 
# Renseigner le dataset_id et la liste des resource_id
# Note: utiliser le script api_call_get to get the resources list

dataset_id = "5cd57bf68b4c4179299eb0e9"

config_file = "config.json"
# read info from config.son
with open(config_file, "r") as f:
    config = json.load(f)
    data_gouv_api_key = config["data_gouv_api_key"]

headers = {
    "X-API-KEY": data_gouv_api_key
}

with open('data/data_gouv_resources_list.json', "r") as f:
    data = json.load(f)

api_host = "https://www.data.gouv.fr/api/1"
url = f"{api_host}/datasets/{dataset_id}/resources/"

response = requests.put(url,headers=headers,json=data)

print(f"Statut de la requête : {response.status_code}")
#print("Réponse : ", response.json())