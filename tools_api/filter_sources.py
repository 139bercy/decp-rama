import os
import csv
import xmltodict

source_dir = "sources\\data.gouv.fr_pes\\"
selected_data = []

# Priorité pour colonnes spécifiques
first_cols = [
    "id",
    "acheteur/id",
    "titulaires/titulaire/id[0]",
    "dateNotification",
    "montant"
]
all_other_cols = set()

def get_leaf_value(obj, path):
    """Accède à une feuille d'après un chemin, ex: 'titulaires/titulaire/id[0]'."""
    parts = path.split("/")
    cur = obj
    for i, part in enumerate(parts):
        # Gestion des indices [N]
        if "[" in part and part.endswith("]"):
            field, idx = part[:-1].split("[")
            idx = int(idx)
            cur = cur.get(field, None)
            if isinstance(cur, list):
                cur = cur[idx] if idx < len(cur) else None
            else:
                # Le champ n'est pas une liste, peut être None
                cur = cur if idx == 0 else None
        else:
            if isinstance(cur, dict):
                cur = cur.get(part, None)
            else:
                cur = None
        if cur is None:
            break
    # Si cur est encore dict ou list, ce n'est pas une feuille
    if isinstance(cur, (dict, list)):
        return None
    return cur

# Parcours des fichiers XML
for filename in os.listdir(source_dir):
    if not filename.lower().endswith(".xml"):
        continue
    print(f"Loading {filename}")
    path = os.path.join(source_dir, filename)
    with open(path, "r", encoding="utf-8") as infile:
        try:
            d = xmltodict.parse(infile.read())
        except Exception as e:
            print(f"Erreur de parsing dans {filename}: {e}")
            continue

        # Retrouver les marchés
        marches = None
        if "marches" in d and "marche" in d["marches"]:
            marches = d["marches"]["marche"]
        else:
            for v in d.values():
                if isinstance(v, dict) and "marches" in v and "marche" in v["marches"]:
                    marches = v["marches"]["marche"]

        if not marches:
            continue

        # Toujours une liste
        if not isinstance(marches, list):
            marches = [marches]

        for marche in marches:
            acheteur = marche.get("acheteur", {})
            acheteur_id = acheteur.get("id")
            if acheteur_id == "21690123100011":
                row = {}
                # D'abord les colonnes prioritaires
                for col in first_cols:
                    row[col] = get_leaf_value(marche, col) or ""
                # Récupérer toutes autres feuilles présentes
                def flatten_leaves(dico, prefix=""):
                    for k, v in dico.items():
                        if isinstance(v, dict):
                            yield from flatten_leaves(v, f"{prefix}{k}/")
                        elif isinstance(v, list):
                            for i, item in enumerate(v):
                                if isinstance(item, dict):
                                    yield from flatten_leaves(item, f"{prefix}{k}[{i}]/")
                                else:
                                    yield f"{prefix}{k}[{i}]", item
                        else:
                            yield f"{prefix}{k}", v
                for k, v in flatten_leaves(marche):
                    if k not in first_cols:  # Eviter redondance
                        row[k] = v
                        all_other_cols.add(k)
                selected_data.append(row)

# Construction du header CSV
other_cols_sorted = sorted([c for c in all_other_cols if c not in first_cols])
header = first_cols + other_cols_sorted

print(f"Saving ")
# Ecriture CSV
with open("results\\data.csv", "w", encoding="utf-8", newline='') as fout:
    writer = csv.DictWriter(fout, fieldnames=header, extrasaction="ignore")
    writer.writeheader()
    for row in selected_data:
        writer.writerow(row)
