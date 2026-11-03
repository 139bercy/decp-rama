import json
import unicodedata
from datetime import datetime
import pandas as pd

NC = "NC"
MARCHE = "Marché"
CONCESSION = "Concession"
ACCORD_CADRE = "Accord-cadre"
SANS_OBJET = ["Sans objet"]
IN_FORME_PRIX = ['Ferme','Ferme et actualisable','Révisable']
OUT_FORME_PRIX = ['Définitif ferme','Définitif actualisable','Définitif révisable']

def without_accents(chaine):
    # Normaliser la chaîne et supprimer les accents
    return ''.join(c for c in unicodedata.normalize('NFD', chaine) if unicodedata.category(c) != 'Mn')

nature_marches = [MARCHE, "Marché de partenariat", ACCORD_CADRE, "Marché subséquent"]
nature_marches_min = [without_accents(valeur.lower()) for valeur in nature_marches]

nature_concessions = ["Concession de travaux", "Concession de service", "Concession de service public", "Délégation de service public"]
nature_concessions_min = [without_accents(valeur.lower()) for valeur in nature_concessions]

same_fields = ["id", "objet", "codeCPV", "procedure", "dureeMois", "dateNotification","montant","datePublicationDonnees",""] 
delete_nodes = {
    'acheteur':
        {'nom': None },
    'lieuExecution':
        {'nom': None },
    'titulaires':
        {'denominationSociale': None },
    'modifications':
        {'objetModification': None,
        'titulaires':   {'denominationSociale': None},
        'dateSignatureModification': None 
        },
    'autoriteConcedante':
        {'nom': None },
    'donneesExecution':
        {'tarifs':   {'denominationSociale': None},
        }
}

# utilisation: json_modifie = delete_nodes(json_dorigine, json_reference)
def delete_nodes(json_dorigine, json_reference):
    for cle, valeur in list(json_reference.items()):  # Utiliser une list pour éviter un RuntimeError lors de la modification du dict
        if isinstance(valeur, dict):  # Si c'est un dictionnaire, appeler récursivement
            if cle in json_dorigine and isinstance(json_dorigine[cle], dict):
                delete_nodes(json_dorigine[cle], valeur)
        elif valeur is None and cle in json_dorigine:  # Si la valeur est None, supprimer la clé
            del json_dorigine[cle]

    return json_dorigine


def value(data:dict,nodes:list,default_value:str|int=None):
    value = data
    for node in nodes:
        if value is not None and node in value:
            value = value[node]
        else:
            return default_value
    return value


def value_date(data:dict, nodes:list, default_value:str="2024-01-01"):
    """
    Récupère une valeur de date depuis un dictionnaire et la parse selon différents formats.
    
    Formats supportés:
    - "2026-09-16"
    - "2021-09-16 00:00:00"
    - "24/12/2024"
    - "September, 16 2021 00:00:00"
    
    Args:
        data: dictionnaire source
        nodes: liste des clés à parcourir
        default_value: date par défaut si aucun format n'est reconnu (défaut: "2024-01-01")
    
    Returns:
        str: date au format "YYYY-MM-DD"
    """
    date_value = data
    for node in nodes:
        if date_value is not None and node in date_value:
            date_value = date_value[node]
        else:
            return default_value
    
    if date_value is None or date_value == "":
        return default_value
    
    # Liste des formats à essayer
    date_formats = [
        "%Y-%m-%d",                    # "2026-09-16"
        "%Y-%m-%d %H:%M:%S",          # "2021-09-16 00:00:00"
        "%d/%m/%Y",                    # "24/12/2024"
        "%y-%m-%d",                    # "24/12/2024"
        "%B, %d %Y %H:%M:%S",         # "September, 16 2021 00:00:00"
    ]
    
    # Essayer chaque format
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(str(date_value), fmt)
            return parsed_date.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    
    # Si aucun format ne fonctionne, essayer avec pandas (plus flexible)
    try:
        parsed_date = pd.to_datetime(str(date_value))
        return parsed_date.strftime("%Y-%m-%d")
    except:
        # Si tout échoue, retourner la valeur par défaut
        return default_value


def value_list(data:list,attributes:list,sub_node:str):
    result = []
    if data is not None:
        for element in data:
            if element is not None:
                new_element = {sub_node: {}}
                for attribute in attributes:
                    if attribute == 'typeIdentifiant':
                        new_element[sub_node][attribute] = convert_type_identifiant(element)    
                    else:
                        new_element[sub_node][attribute] = value(element,[attribute])
                result.append(new_element)
    return result

def value_list_list(data,node,attributes:list,sub_node,included_node:str=None,included_attributes:list=None,included_sub_node:str=None):
    result = None
    if node in data:
        result = []
        index = 1
        for element in data[node]:
            new_element = {sub_node: {}}
            for attribute in attributes:
                if attribute == included_node and attribute in element:# and element[attribute] is not None:
                    if element[attribute] is not None:
                        if included_sub_node in element[attribute]:
                            new_element[sub_node][attribute] = value_list(element[attribute][included_sub_node] if isinstance(element[attribute][included_sub_node],list) else [element[attribute][included_sub_node]],included_attributes,included_sub_node)
                        else:
                            new_element[sub_node][attribute] = value_list([element[attribute]],included_attributes,included_sub_node)
                else:
                    val = value(element,[attribute])
                    if val is not None:
                        new_element[sub_node][attribute] = value(element,[attribute])
                        if new_element[sub_node][attribute] is not None and attribute == 'dureeMois':
                            new_element[sub_node][attribute] = int(new_element[sub_node][attribute])
                        if new_element[sub_node][attribute] is not None and attribute == 'montant':
                            new_element[sub_node][attribute] = float(new_element[sub_node][attribute])
                    elif attribute == 'id':
                        new_element[sub_node][attribute] = index
            result.append(new_element)
            index += 1
    return result


def rename_node(marche,node_list:str,node:str,old_name:str,new_name:str):
    if node_list in marche and isinstance(marche[node_list], list):
        for element in marche[node_list]:
            if node in element and old_name in element[node]:
                element[node][new_name] = element[node].pop(old_name)


def remove_empty_list_nodes(data):
    if isinstance(data, list):
        for item in data:
            remove_empty_list_nodes(item)
    elif isinstance(data, dict):
        keys_to_delete = []
        
        for key, value in data.items():
            if isinstance(value, list) and not value:
                keys_to_delete.append(key)
            else:
                remove_empty_list_nodes(value)
        
        for key in keys_to_delete:
            del data[key]


def extract_nature_marche(marche:dict) -> tuple[str,str,str]:
    nature = value(marche,['nature'],None)
    if nature is None:
        nature = value(marche,['_type'],MARCHE)
    technique = NC
    modalite_execution = NC
    if without_accents(nature.lower()) in nature_marches_min:
        index = nature_marches_min.index(without_accents(nature.lower()))
    else:
        index = 0
    nature = nature_marches[index]  
    
    if nature == ACCORD_CADRE:
        technique = nature
        nature = MARCHE
    elif nature == 'Marché subséquent':
        modalite_execution = nature
        nature = MARCHE

    return nature,technique,modalite_execution

def extract_nature_concession(concession:dict) -> str:
    nature = value(concession,['nature'],CONCESSION)
    if nature is None:
        nature = value(concession,['_type'],CONCESSION)

    index = nature_concessions_min.index(without_accents(nature.lower()))
    nature = nature_concessions[index]    

    return nature

def convert_type_prix(marche,node_name) -> str:
    type_prix = value(marche,node_name)
    if type_prix is not None and type_prix in IN_FORME_PRIX:
        index = IN_FORME_PRIX.index(type_prix)
        return OUT_FORME_PRIX[index]    
    else:
        return node_name


def convert_type_identifiant(marche) -> str:
    type_identifiant = value(marche,['typeIdentifiant'])
    if type_identifiant == 'UE':
        type_identifiant = 'TVA'
    return type_identifiant


def convert_marche(marche:dict) -> dict:
    print("Marche ",value(marche,['id']))
    
    nature,technique,modalite_execution = extract_nature_marche(marche)
    type_prix = convert_type_prix(marche,['formePrix'])
    id_marche = value(marche,['id'])

    marche = {
        'id': id_marche,
        'acheteur': { 'id': value(marche,['acheteur.id']) },
        'nature': nature,
        'objet': value(marche,['objet']),
        'techniques': {
            "technique": [technique]
        },
        'modalitesExecution': {
            "modaliteExecution": [modalite_execution]
        },
        #'idAccordCadre': None,
        'codeCPV': value(marche,['codeCPV']),
        'procedure': value(marche,['procedure']),
        'lieuExecution' : {
            'code': value(marche,['lieuExecution','code']),
            'typeCode': value(marche,['lieuExecution','typeCode'])
        },
        'dureeMois': int(value(marche,['dureeMois'])),
        'dateNotification': value_date(marche,['dateNotification']),
        'considerationsSociales': {
            "considerationSociale": [NC]
        },
        'considerationsEnvironnementales': {
            "considerationEnvironnementale": [NC]
        },
        'marcheInnovant': value(marche,['marcheInnovant'],NC),
        'origineUE': value(marche,['origineUE'],NC),
        'origineFrance': value(marche,['origineFrance'],NC),
        'ccag': value(marche,['ccag'],NC),
        'offresRecues': value(marche,['offresRecues'],NC),
        'montant': int(value(marche,['montant'])) if value(marche,['montant']) is not None else None,
        'formePrix': "NC",
        'typePrix': type_prix,
        'attributionAvance': value(marche,['attributionAvance'],NC),
        'tauxAvance': value(marche,['tauxAvance'],NC),
        'titulaires': value_list(marche['titulaires'],['id','typeIdentifiant'],'titulaire') if 'titulaires' in marche else None,
        'typeGroupementOperateurs': value(marche,['typeGroupementOperateurs']),
        'sousTraitanceDeclaree': value(marche,['sousTraitanceDeclaree'],NC),
        'datePublicationDonnees': value_date(marche,['datePublicationDonnees']),
        '_type': MARCHE,
        'source': value(marche,['source'],NC),
        'modifications': value_list_list(marche,'modifications',['id','dureeMois','montant','titulaires','dateNotificationModification','dateSignatureModification'],'modification','titulaires',['id','typeIdentifiant'],'titulaire')
    }
    rename_node(marche,'modifications','modification','dateSignatureModification','dateNotificationModification')
    remove_empty_list_nodes(marche)

    return marche


def convert_concession(marche):
    print("Concession ",value(marche,['id']))
    nature = extract_nature_concession(marche)
    marche = {
        'id': str(value(marche,['id'])),
        'autoriteConcedante': {
            "id": marche['autoriteConcedante']['id'] if 'autoriteConcedante' in marche else None,
        },  
        'nature': nature,
        'objet': value(marche,['objet']),
        'procedure': value(marche,['procedure']),
        'dureeMois': value(marche,['dureeMois']),
        'dateDebutExecution': value_date(marche,['dateDebutExecution']),
        'dateSignature': value_date(marche,['dateSignature']),
        'considerationsSociales': {
            "considerationSociale": [NC]
        },
        'considerationsEnvironnementales': {
            "considerationEnvironnementale": [NC]
        },
        'concessionnaires': value_list(marche['concessionnaires'],['id','typeIdentifiant'],'concessionnaire') if 'concessionnaires' in marche else None,
        'valeurGlobale': value(marche,['valeurGlobale']),
        'montantSubventionPublique': value(marche,['montantSubventionPublique']),
        'datePublicationDonnees': value_date(marche,['datePublicationDonnees']),
        'modifications': value_list_list(marche,'modifications',['id','dureeMois','valeurGlobale','dateSignatureModification','datePublicationDonneesModification'],'modification'),
        'donneesExecution': value_list_list(marche,'donneesExecution',['depensesInvestissement','tarifs','datePublicationDonneesExecution'],'donneeExecution','tarifs',['intituleTarif','tarif'],'tarif'),
        '_type': CONCESSION,
        'source': value(marche,['source'],NC)
    }
    remove_empty_list_nodes(marche)

    return marche


# Chargement du fichier JSON
with open('data/decp-2019.json', 'r', encoding='utf-8') as f:
#with open('data/samples-2019-marches.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

file_path = 'data/2019-converted-to-2022.json'
with open(file_path, 'w', encoding='utf-8') as file:
    file.write("{ \"marches\": \n\t{\"marche\":[\n")

concessions = []
comma = False
for marche in data['marches']:
    if ("nature" in marche and marche["nature"] is not None and without_accents(marche["nature"].lower()) in nature_marches_min) or \
        ("_type" in marche and marche["_type"] is not None and marche["_type"] == MARCHE) or \
        "titulaires" in marche:
        # Cas d'un marché
        #marche = convert_marche(marche)
        continue
    else:
        # Cas d'une concession
        concessions.append(convert_concession(marche))
        continue
    if marche is None:
        continue
    with open(file_path, 'a', encoding='utf-8') as file:
        if comma:
            file.write(",\n") # Ajout d'une virgule pour séparer les éléments
        else:
            comma = True
        json.dump(marche, file, indent=2, ensure_ascii=False)

if not concessions == []:
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write("\n  ]\n, \"contrat-concession\": [\n")
    
    comma = False
    for concession in concessions:
        with open(file_path, 'a', encoding='utf-8') as file:
            if comma:
                file.write(",\n") # Ajout d'une virgule pour séparer les éléments
            else:
                comma = True
            json.dump(concession, file, indent=2, ensure_ascii=False)

with open(file_path, 'a', encoding='utf-8') as file:
    file.write("\n  ]\n}}")

print("End")
