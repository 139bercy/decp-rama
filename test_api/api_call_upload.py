import requests
import hashlib

# Script de test pour créer une nouvelle resource

# Fonction de calculer du hash SHA-1 d'un fichier
def calculate_sha1(file_path):
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as file:
        # Lire le fichier par blocs de 64 Ko
        for chunk in iter(lambda: file.read(64 * 1024), b''):
            sha1.update(chunk)
    return sha1.hexdigest()

api_host = "https://www.data.gouv.fr/api/1"
dataset_id = "5cd57bf68b4c4179299eb0e9"
resource_id = "eddb0aaf-e0cb-4dd2-abb4-9971fa84106c"
url = f"{api_host}/datasets/{dataset_id}/resources/{resource_id}/upload/"

config_file = "config.json"
# read info from config.son
with open(config_file, "r") as f:
    config = json.load(f)
    data_gouv_api_key = config["data_gouv_api_key"]

headers = {
    "X-API-KEY": data_gouv_api_key
}

sha1_hash = calculate_sha1('results/decp-2024-10_data_gouv.json')

files_month = {
    "file": ("decp-2024-10.json", open("results/decp-2024-10_data_gouv.json", "rb"))
}

response = requests.post(url, headers=headers, files=files_month)

print(f"Statut de la requête : {response.status_code}")
print("Réponse : ", response.json())