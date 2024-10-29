import requests
import hashlib

# Script de test pour supprimer une resource
# Renseigner le dataset_id et le resource_id

dataset_id = "5cd57bf68b4c4179299eb0e9"
resource_id = "64297eac-8cd3-492a-bdeb-2ae6417ca7a8"

headers = {
    "X-API-KEY": "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyIjoiNWYwZjA0NzZkNzk3NDZjYmU5OGNjYmMwIiwidGltZSI6MTY0ODIxNzg4Ny4wOTg0ODE3fQ.d9b1s_170PeSNAOLyqFFOGoW8irEg1nxNxn-fdGCGAckFbVcIxpaxkEm8H-BlI6nLLvWmvS_lL3nKWaHb7Cd9g"
}

api_host = "https://www.data.gouv.fr/api/1"
url = f"{api_host}/datasets/{dataset_id}/resources/{resource_id}/"

response = requests.delete(url,headers=headers)

print(f"Statut de la requête : {response.status_code}")
#print("Réponse : ", response.json())