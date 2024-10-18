import requests
import hashlib

# Script de test pour supprimer une resource
# Renseigner le dataset_id et le resource_id

dataset_id = "5cd57bf68b4c4179299eb0e9"
resource_id = "19e5a3b2-7b3a-49c1-afaa-d6d34fca8d4d"

headers = {
    "X-API-KEY": "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyIjoiNWYwZjA0NzZkNzk3NDZjYmU5OGNjYmMwIiwidGltZSI6MTY0ODIxNzg4Ny4wOTg0ODE3fQ.d9b1s_170PeSNAOLyqFFOGoW8irEg1nxNxn-fdGCGAckFbVcIxpaxkEm8H-BlI6nLLvWmvS_lL3nKWaHb7Cd9g"
}

api_host = "https://www.data.gouv.fr/api/1"
url = f"{api_host}/datasets/{dataset_id}/resources/{resource_id}/"

response = requests.delete(url,headers=headers)

print(f"Statut de la requête : {response.status_code}")
#print("Réponse : ", response.json())