import requests
import hashlib
import json

# Script de test pour supprimer une resource
# Renseigner le dataset_id et le resource_id

dataset_id = "5cd57bf68b4c4179299eb0e9"
resource_id = ""

config_file = "config.json"
# read info from config.son
with open(config_file, "r") as f:
    config = json.load(f)
    data_gouv_api_key = config["data_gouv_api_key"]

headers = {
    "X-API-KEY": data_gouv_api_key
}

api_host = "https://www.data.gouv.fr/api/1"

# Chargement du fichier JSON
with open('results/result_ressources.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

i=0
# Extraction des titres, fichiers et IDs
for resource in data['resources']:
    print(f"Suppression de : {resource['id']},{resource['title']}")
    url = f"{api_host}/datasets/{dataset_id}/resources/{resource['id']}/"
    response = requests.delete(url,headers=headers)

    print(f"Statut de la requête : {response.status_code}")
    i += 1

print(f"{i} fichier(s) supprimé(s)")