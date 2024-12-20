import requests
import json

# Script d'appel à l'API pour récupére les resources d'un dataset

api_host = "https://www.data.gouv.fr/api/1"
dataset_id = "5cd57bf68b4c4179299eb0e9" #"5bd0b6fd8b4c413d0801dc57"
url = f"{api_host}/datasets/{dataset_id}/"

config_file = "config.json"
# read info from config.son
with open(config_file, "r") as f:
    config = json.load(f)
    data_gouv_api_key = config["data_gouv_api_key"]

headers = {
    "X-API-KEY": data_gouv_api_key
}

response = requests.get(url, headers=headers)

print(f"Statut de la requête : {response.status_code}")
if response.status_code == 200:
    # Récupérer la réponse en JSON
    response_data = response.json()
    
    # Sauvegarder le résultat au format JSON
    with open('result.json', 'w') as json_file:
        json.dump(response_data, json_file, indent=4)
    
    print("Résultat sauvegardé dans 'result.json'")
else:
    print("Erreur lors de la requête :", response.text)