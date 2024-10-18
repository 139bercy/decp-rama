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
resource_id = "59ba0edb-cf94-4bf1-a546-61f561553917"
url = f"{api_host}/datasets/{dataset_id}/resources/{resource_id}/upload/"

headers = {
    "X-API-KEY": "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyIjoiNWYwZjA0NzZkNzk3NDZjYmU5OGNjYmMwIiwidGltZSI6MTY0ODIxNzg4Ny4wOTg0ODE3fQ.d9b1s_170PeSNAOLyqFFOGoW8irEg1nxNxn-fdGCGAckFbVcIxpaxkEm8H-BlI6nLLvWmvS_lL3nKWaHb7Cd9g"
}

sha1_hash = calculate_sha1('test_api/decp-fichier-test.json')

files_month = {
    "file": (f"decp-2022.json", open(f"results/decp-2022.json", "rb"))
}

response = requests.post(url, headers=headers, files=files_month)

print(f"Statut de la requête : {response.status_code}")
print("Réponse : ", response.json())