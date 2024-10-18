import requests
import json

# Script d'appel à l'API pour récupére les resources d'un dataset

api_host = "https://www.data.gouv.fr/api/1"
dataset_id = "5bd0b6fd8b4c413d0801dc57"
url = f"{api_host}/datasets/?q=depuis-2024&page=1&page_size=100"

headers = {
    "X-API-KEY": "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyIjoiNWYwZjA0NzZkNzk3NDZjYmU5OGNjYmMwIiwidGltZSI6MTY0ODIxNzg4Ny4wOTg0ODE3fQ.d9b1s_170PeSNAOLyqFFOGoW8irEg1nxNxn-fdGCGAckFbVcIxpaxkEm8H-BlI6nLLvWmvS_lL3nKWaHb7Cd9g"
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