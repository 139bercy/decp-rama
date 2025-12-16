import datetime
import json
import locale
import logging
import requests

# Script de mise à jour des descriptions sur data.gouv
suffixes = ['2024-01','2024-02','2024-03','2024-04','2024-05','2024-06','2024-07','2024-08','2024-09','2024-10','2024-11','2024-12','2025-01','2025-02','2025-03','2025-04','2025-05','2025-06','2025-07','2025-08','2025-09','2025-10','2025-11']
suffixes = ["global"]

locale.setlocale(locale.LC_TIME,"fr_FR.UTF-8")
config_file = "config.json"
# read info from config.son
with open(config_file, "r") as f:
    config = json.load(f)
    data_gouv_api_key = config["data_gouv_api_key"]

api_host = "https://www.data.gouv.fr/api/1"
dataset_id = "5cd57bf68b4c4179299eb0e9"
headers = {
    "X-API-KEY": data_gouv_api_key
}

def get_ressource_id(suffix:str) -> str:
    resource_id = None

    resource_file = f"decp-{suffix}.json"
    url = f"{api_host}/datasets/{dataset_id}/"
    response = requests.get(url, headers)

    if response.status_code == 200:
        # Récupérer la réponse en JSON
        response_json = response.json()
      
        resources = response_json['resources']
        for resource in resources:
            if resource['title'] == resource_file:
                resource_id = resource['id']
                
    return resource_id

def update_description(ressource_id, suffix):
    #mois_annee = get_mois_annee(suffix)
    #description = f"Fichier cumulatif des données essentielles de la commande publique pour {mois_annee}"
    description = "Fichier des données essentielles de la commande publique au format 2022 pour toutes les années après dédoublonnage"
    data = {
        "format": "json",
        "title": f"decp-{suffix}.json",
        "description": f"{description} ",
        "type": "main",
        "mime": "application/json",
        "url": f"https://www.data.gouv.fr/api/1/datasets/r/{ressource_id}"
    }
    url_update = f"{api_host}/datasets/{dataset_id}/resources/{ressource_id}/"
    response = requests.put(url_update, headers=headers, json=data)

    print(f"Statut de la requête : {response.status_code}")
    print("Réponse : ", response.json())

def get_mois_annee(suffix):
    year,month = suffix.split("-")
    date_obj = datetime.datetime(int(year),int(month),1)
    return date_obj.strftime("%B %Y")

if __name__ == "__main__":

    for suffix in suffixes:
        logging.info(f"Updating description for file decp-{suffix}.json")
        ressource_id = get_ressource_id(suffix)
        print(ressource_id)
        update_description(ressource_id,suffix)
