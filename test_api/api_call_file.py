import requests
import json
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
url = f"{api_host}/datasets/{dataset_id}/upload/"

headers = {
    "X-API-KEY": "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyIjoiNWYwZjA0NzZkNzk3NDZjYmU5OGNjYmMwIiwidGltZSI6MTY0ODIxNzg4Ny4wOTg0ODE3fQ.d9b1s_170PeSNAOLyqFFOGoW8irEg1nxNxn-fdGCGAckFbVcIxpaxkEm8H-BlI6nLLvWmvS_lL3nKWaHb7Cd9g"
}

sha1_hash = calculate_sha1('test_api/decp-fichier-test.json')

files_month = {
    "file": (f"decp-2024-10_02.json", open(f"test_api/decp-fichier-test.json", "rb"))
}

response = requests.post(url, headers=headers, files=files_month)

print(f"Statut de la requête : {response.status_code}")
if response.status_code == 201:
    # Récupérer la réponse en JSON
    response_data = response.json()
    
    # Sauvegarder le résultat au format JSON
    with open('result_new_file.json', 'w') as json_file:
        json.dump(response_data, json_file, indent=4)
    
    print("Résultat sauvegardé dans 'result.json'")
else:
    print("Erreur lors de la requête :", response.text)