import json

# Chargement du fichier JSON
with open('results/result_ressources.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extraction des titres, fichiers et IDs
for resource in data['resources']:
    print(f"{resource['id']},{resource['title']}")