import requests
import hashlib

# Script de test pour supprimer une resource
# Renseigner le dataset_id et le resource_id

dataset_id = "5cd57bf68b4c4179299eb0e9"
resource_id = "aeaf9e4b-d808-4ad9-b477-6f7ad28fc03d"

config_file = "config.json"
# read info from config.son
with open(config_file, "r") as f:
    config = json.load(f)
    data_gouv_api_key = config["data_gouv_api_key"]

headers = {
    "X-API-KEY": data_gouv_api_key
}

api_host = "https://www.data.gouv.fr/api/1"
url = f"{api_host}/datasets/{dataset_id}/resources/{resource_id}/"

response = requests.delete(url,headers=headers)

print(f"Statut de la requête : {response.status_code}")
#print("Réponse : ", response.json())