import requests
import hashlib
import json

# Script de test pour créer une nouvelle resource

# Fonction de calculer du hash SHA-1 d'un fichier
def calculate_sha1(file_path):
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as file:
        # Lecture du fichier par blocs de 64 Ko
        for chunk in iter(lambda: file.read(64 * 1024), b''):
            sha1.update(chunk)
    return sha1.hexdigest()

api_host = "https://www.data.gouv.fr/api/1"
dataset_id = "5cd57bf68b4c4179299eb0e9"
url = f"{api_host}/datasets/{dataset_id}/resources/"
nom_fichier = "results/LAST_REAL_DATA/decp-2024_data_gouv.json"

config_file = "config.json"
# read info from config.son
with open(config_file, "r") as f:
    config = json.load(f)
    data_gouv_api_key = config["data_gouv_api_key"]

headers = {
    "X-API-KEY": data_gouv_api_key
}

sha1_hash = calculate_sha1(nom_fichier)

data = {
    "filetype": "remote",
    "format": "json",
    "title": "decp-2024.json",
    "description": "Fichier cumulatif des données essentielles de la commande publique pour l'année 2024",
    "type": "main",
    "mime": "application/json",
    "url": "https://www.data.gouv.fr/"
}


response = requests.post(url, headers=headers, json=data)

print(f"Statut de la requête : {response.status_code}")
print("Réponse : ", response.json())