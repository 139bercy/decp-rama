import requests
import hashlib
import json
import wget

# Script de test pour downloade les ressources d' un dataset

api_host = "https://www.data.gouv.fr/api/1"
dataset_id = "5cd57bf68b4c4179299eb0e9"

config_file = "config.json"
# read info from config.son
with open(config_file, "r") as f:
    config = json.load(f)
    data_gouv_api_key = config["data_gouv_api_key"]

headers = {
    "X-API-KEY": data_gouv_api_key
}

# Chargement du fichier JSON
with open('results/result_ressources.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

i=0
# Extraction des titres, fichiers et IDs
for resource in data['resources']:
    print(f"{resource['title']} {resource["url"]}")
    try:
        wget.download(resource["url"],
            f"resources/{i}-{resource['title']}")
    except Exception as err:
        with open(f"resources/{i}-{resource['title']}-ERREUR-{err.code}.txt", 'w') as json_file:
            json_file.write(str(err))
        print(f"Erreur de téléchargement du fichier {resource['title']} {resource["url"]} {err}")

    i += 1

print(f"Nb total : {i}")