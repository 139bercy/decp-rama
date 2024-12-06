import requests
import hashlib
import json

# Script de test pour créer une nouvelle resource

# Fonction de calculer du hash SHA-1 d'un fichier
def calculate_sha1(file_path):
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as file:
        # Lire le fichier par blocs de 64 Ko
        for chunk in iter(lambda: file.read(64 * 1024), b''):
            sha1.update(chunk)
    return sha1.hexdigest()

#resource_id = "4fafdaff-b697-4494-9523-e9f56916fea8"
#nom_fichier = "results/LAST_REAL_DATA/decp-2024_data_gouv.json"
#renommage_fichier = "decp-2024.json"

resource_id = "398e075e-5dc2-4797-86d7-21d04e39111f"
nom_fichier = "results/decp-2024-11_data_gouv.json"
renommage_fichier = "decp-2024-11.json"

api_host = "https://www.data.gouv.fr/api/1"
dataset_id = "5cd57bf68b4c4179299eb0e9"
url = f"{api_host}/datasets/{dataset_id}/resources/{resource_id}/upload/"

config_file = "config.json"
# read info from config.son
with open(config_file, "r") as f:
    config = json.load(f)
    data_gouv_api_key = config["data_gouv_api_key"]

headers = {
    "X-API-KEY": data_gouv_api_key
}

sha1_hash = calculate_sha1(nom_fichier)

# Faire dans le script d'upload
file_data = {
    "file": (renommage_fichier, open(nom_fichier, "rb"))
}

response = requests.post(url, headers=headers, files=file_data)

print(f"Statut de la requête : {response.status_code}")
print("Réponse : ", response.json())