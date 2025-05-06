import os
import xmltodict
from xml.dom.minidom import parseString

# Ce script prend en entrée un répertoire source avec les fichiers téléchargé depuis une source et conserve uniquement les fichiers ayant un id = a la valeur VALEUR_ID
source_dir = "sources\\data.gouv.fr_pes"
VALEUR_ID = "2024O5052A"

for filename in os.listdir(source_dir):
    if not filename.lower().endswith(".xml"):
        continue
    print(f"Loading {filename}")                          
    path = os.path.join(source_dir, filename)
    with open(path, 'r', encoding='utf-8') as xml_file:
        xml_content = xml_file.read()
    
    try:
        obj = xmltodict.parse(xml_content)
    except Exception as e:
        print(f"Erreur de parsing dans {filename} : {e}")
        continue

    marches = None
    racine = None  # Pour reconstruire la racine si besoin
    racine_dict = None
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

    if not isinstance(marches, list):
        marches = [marches]

    selected_marches = []
    for marche in marches:
        #acheteur = marche.get("acheteur", {})
        #acheteur_id = acheteur.get("id")
        #if acheteur_id == "21690123100011":
        #    selected_marches.append(marche)
        id = marche.get("id")
        if id == VALEUR_ID:
            selected_marches.append(marche)

    if not selected_marches:
        # Aucun marché correspondant, on supprime le fichier
        os.remove(path)
        print(f"{filename} supprimé (aucun marché correspondant).")
        continue

    # Reconstituer l'objet pour xmltodict.unparse
    if racine == "marches":
        output_obj = {"marches": {"marche": selected_marches}}
    else:
        racine_dict["marches"]["marche"] = selected_marches
        output_obj = {racine: racine_dict}

    xml_str = xmltodict.unparse(output_obj, pretty=True, encoding="utf-8")
    dom = parseString(xml_str)
    indented = dom.toprettyxml(indent="  ")

    # On écrase le fichier source
    with open(path, "w", encoding="utf-8") as xf:
        xf.write(indented)
