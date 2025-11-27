import os
import json
import xmltodict

# Dossier source
source_dir = "sources\\data.gouv.fr_pes2\\"
# Liste pour stocker les résultats
resultats = []

# Parcourir tous les fichiers XML dans le dossier
for filename in os.listdir(source_dir):
    if filename.lower().endswith(".xml"):
        print(f"Loading {filename}")
        path = os.path.join(source_dir, filename)
        with open(path, 'r', encoding='utf-8') as xml_file:
            data = xmltodict.parse(xml_file.read(), dict_constructor=dict, \
                            force_list=('marche','contrat-concession',
                                'titulaires','donneesExecution','modifications',
                                'actesSousTraitance','modificationsActesSousTraitance'))
            
            # Accéder à la liste des marchés de façon générique
            marches = None
            # Trouver le bon chemin pour "marches/marche"
            if "marches" in data and "marche" in data["marches"]:
                marches = data["marches"]["marche"]
            # Parfois la racine a un nom, ex: <root><marches>...
            elif any(isinstance(v, dict) and "marches" in v for v in data.values()):
                for v in data.values():
                    if isinstance(v, dict) and "marches" in v and "marche" in v["marches"]:
                        marches = v["marches"]["marche"]
            # Si jamais ce n'est pas trouvé, on saute le fichier
            if marches is None:
                continue

            # S'assurer que marches est une liste
            if not isinstance(marches, list):
                marches = [marches]

            for marche in marches:
                acheteur = marche.get("acheteur", {})
                acheteur_id = acheteur.get("id")
                if acheteur_id == "12345":
                    resultats.append(marche)

print(f"Saving result")
# Sauvegarder en JSON
with open("results\\data.json", "w", encoding="utf-8") as f:
    json.dump(resultats, f, ensure_ascii=False, indent=2)
