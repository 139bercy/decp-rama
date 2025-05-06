import os
import xmltodict
from xml.dom.minidom import parseString

source_dir = "sources\\data.gouv.fr_pes2\\"
selected_marches = []

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
        # Le dict peut avoir la racine "marches"
        if "marches" in obj and "marche" in obj["marches"]:
            marches = obj["marches"]["marche"]
        # Sinon la racine peut être autre, mais contenir "marches"
        else:
            for v in obj.values():
                if isinstance(v, dict) and "marches" in v and "marche" in v["marches"]:
                    marches = v["marches"]["marche"]

        if not marches:
            continue

        # Garantir une liste
        if not isinstance(marches, list):
            marches = [marches]

        for marche in marches:
            acheteur = marche.get("acheteur", {})
            acheteur_id = acheteur.get("id")
            if acheteur_id == "21690123100011":
                # Re-transformer le dict marche en XML string (sans déclaration xml)
                xmlstr = xmltodict.unparse({"marche": marche}, pretty=True, full_document=False)
                selected_marches.append(xmlstr)

print(f"Saving result")
# Sauvegarder le XML concaténé dans <marches>...</marches>
with open("results\\data.xml", "w", encoding="utf-8") as fout:
    fout.write('<marches>\n')
    for marche_xml in selected_marches:
        # Indenter joliment chaque <marche>
        dom = parseString(marche_xml)
        indented = dom.toprettyxml(indent="  ").replace('<?xml version="1.0" ?>\n', '')
        fout.write(indented)
    fout.write('</marches>\n')
