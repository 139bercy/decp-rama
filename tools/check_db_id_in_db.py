import json

# Ouvrir le fichier JSON
with open("results/decp-2025.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Vérifier que la clé 'marches' existe
if "marches" in data:
    print("Valeurs de db_id :")
    nb = 0
    for marche in data["marches"]:
        db_id = marche.get("db_id")
        print(db_id)
        if db_id == 0:
            nb += 1
            print(f"id:{marche.get("id")} id:{marche.get("acheteur")}")
    print(f"{nb} valeurs nulles")
else:
    print("Le fichier ne contient pas de clé 'marches'.")
