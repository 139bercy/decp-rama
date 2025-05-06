import json

file1 = "results\\decp-2024.json"
file2 = "results\\ref\\decp-2024.json"

# Chargement des fichiers
with open(file1, "r", encoding="utf-8") as f:
    data1 = json.load(f)

with open(file2, "r", encoding="utf-8") as f:
    data2 = json.load(f)

# Extraction des IDs
ids1 = set(m['id'] for m in data1['marches'])
ids2 = set(m['id'] for m in data2['marches'])

# Calcul des exclusifs
ids_unique_to_file1 = sorted(list(ids1 - ids2))
ids_unique_to_file2 = sorted(list(ids2 - ids1))

# Affichage des résultats
print(f"IDs présents uniquement dans {file1} : {ids_unique_to_file1}")
print(f"IDs présents uniquement dans {file2} : {ids_unique_to_file2}")

# Optionnel : sauvegarde dans un fichier texte
with open("ids_uniques_fichier1.txt", "w", encoding="utf-8") as out1:
    for i in ids_unique_to_file1:
        out1.write(str(i) + "\n")

with open("ids_uniques_fichier2.txt", "w", encoding="utf-8") as out2:
    for i in ids_unique_to_file2:
        out2.write(str(i) + "\n")
