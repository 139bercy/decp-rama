import requests
import json

# Script d'appel à l'API pour récupére les resources d'un dataset

api_host = "https://www.data.gouv.fr/api/1"

url = f"{api_host}/datasets/?q=s%20publics%20-%20Xmarch&page=1&page_size=100"

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
    with open('result_list.json', 'w') as json_file:
        json.dump(response_data, json_file, indent=4)
    
    print("Résultat sauvegardé dans 'result_list.json'")
else:
    print("Erreur lors de la requête :", response.text)