import os
import xmltodict
from xml.dom.minidom import parseString

source_dir = "sources\\data.gouv.fr_pes2"

for filename in os.listdir(source_dir):
    if not filename.lower().endswith(".xml"):
        continue
    print(f"Loading {filename}")
    path = os.path.join(source_dir, filename)
    with open(path, 'r', encoding='utf-8') as xml_file:
        try:
            obj = xmltodict.parse(xml_file.read())
        except Exception as e:
            print(f"Erreur de parsing dans {filename} : {e}")
            continue

        # Chercher la liste des marchés selon structure
        marches = None
        racine = None  # Pour reconstruire la racine si besoin
        if "marches" in obj and "marche" in obj["marches"]:
            marches = obj["marches"]["marche"]
            racine = "marches"
        else:
            for k, v in obj.items():
                if isinstance(v, dict) and "marches" in v and "marche" in v["marches"]:
                    marches = v["marches"]["marche"]
                    racine = k
                    racine_dict = v
                    break

        if marches is None:
            continue

        # S'assurer que marches est une liste
        if not isinstance(marches, list):
            marches = [marches]

        # Sélectionner les bons marchés
        selected_marches = []
        for marche in marches:
            acheteur = marche.get("acheteur", {})
            acheteur_id = acheteur.get("id")
            if acheteur_id == "21690123100011":
                selected_marches.append(marche)

        if not selected_marches:
            # Aucun marché correspondant, on vide le fichier
            with open(path, "w", encoding="utf-8") as xf:
                xf.write("")
            continue

        # Reconstituer l'objet pour xmltodict.unparse
        if racine == "marches":
            output_obj = {"marches": {"marche": selected_marches}}
        else:
            # Il se peut par exemple que racine soit "root"
            racine_dict["marches"]["marche"] = selected_marches
            output_obj = {racine: racine_dict}

        # Générer XML
        xml_str = xmltodict.unparse(output_obj, pretty=True, encoding="utf-8")
        # Beautifier
        dom = parseString(xml_str)
        indented = dom.toprettyxml(indent="  ")

        # On écrase le fichier source
        with open(path, "w", encoding="utf-8") as xf:
            xf.write(indented)
