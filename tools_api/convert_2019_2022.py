import json
import unicodedata


def without_accents(chaine):
    # Normaliser la chaîne et supprimer les accents
    return ''.join(c for c in unicodedata.normalize('NFD', chaine) if unicodedata.category(c) != 'Mn')

nature_marches = ["Marché", "Marché de partenariat", "Accord-cadre", "Marché subséquent"]
nature_marches_min = [without_accents(valeur.lower()) for valeur in nature_marches]

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


def value(data:dict,nodes:list):
    value = data
    for node in nodes:
        if node in value:
            value = value[node]
        else:
            return None
    return value

def value_list(data:list,attributes:list,sub_node:str):
    result = []
    for element in data:
        new_element = {sub_node: {}}
        for attribute in attributes:
            new_element[sub_node][attribute] = value(element,[attribute])
        result.append(new_element)
    return result

def value_list_list(data,node,attributes:list,sub_node,included_node:str,included_attributes:list,included_sub_node:str):
    result = None
    if node in data:
        result = []
        for element in data[node]:
            new_element = {sub_node: {}}
            for attribute in attributes:
                if attribute == included_node and attribute in element:
                    if included_sub_node in element[attribute]:
                        new_element[sub_node][attribute] = value_list(element[attribute][included_sub_node] if isinstance(element[attribute][included_sub_node],list) else [element[attribute][included_sub_node]],included_attributes,included_sub_node)
                    else:
                        new_element[sub_node][attribute] = value_list([element[attribute]],included_attributes,included_sub_node)
                else:
                    new_element[sub_node][attribute] = value(element,[attribute])
            result.append(new_element)
    return result

def convert_marche(marche:dict) -> dict:
    marche = {
        'id': value(marche,['id']),
        'acheteur': { 'id': value(marche,['acheteur.id']) },
        'nature': value(marche,['nature']),
        'objet': value(marche,['objet']),
        'technique': None,
        'modaliteExecution': None,
        'idAccordCadre': None,
        'codeCPV': value(marche,['codeCPV']),
        'procedure': value(marche,['procedure']),
        'lieuExecution' : {
            'code': value(marche,['lieuExecution','code']),
            'typeCode': value(marche,['lieuExecution','typeCode'])
        },
        'dureeMois': value(marche,['dureeMois']),
        'dateNotification': value(marche,['dateNotification']),
        'considerationsSociales': value(marche,['considerationsSociales']),
        'considerationsEnvironnementales': value(marche,['considerationsEnvironnementales']),
        'marcheInnovant': value(marche,['marcheInnovant']),
        'origineUE': value(marche,['origineUE']),
        'origineFrance': value(marche,['origineFrance']),
        'ccag': value(marche,['ccag']),
        'offresRecues': value(marche,['offresRecues']),
        'montant': value(marche,['montant']),
        'formePrix': value(marche,['formePrix']),
        'typePrix': value(marche,['typePrix']),
        'attributionAvance': value(marche,['attributionAvance']),
        'tauxAvance': value(marche,['tauxAvance']),
        'titulaires': value_list(marche['titulaires'],['id','typeIdentifiant'],'titulaire'),
        'typeGroupementOperateurs': value(marche,['typeGroupementOperateurs']),
        'sousTraitanceDeclaree': value(marche,['sousTraitanceDeclaree']),
        'datePublicationDonnees': value(marche,['datePublicationDonnees']),
        'modifications': value_list_list(marche,'modifications',['id','dureeMois','montant','titulaires','dateNotificationModification','datePublicationDonneesModification'],'modification','titulaires',['id','typeIdentifiant'],'titulaire')
    }
    # TODO remove empty node "modification" (when modification : None or modification : {} )
    return marche


def convert_concession(marche):
    return marche

# Chargement du fichier JSON
#with open('results/decp-2019.json', 'r', encoding='utf-8') as f:
with open('results/sample-2019.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

new_list = []
for marche in data['marches']:
    if without_accents(marche["nature"].lower()) in nature_marches_min:
        # Cas d'un marché
        marche = convert_marche(marche)
    else:
        # Cas d'une concession
        marche = convert_concession(marche)
    new_list.append(marche)

with open('results/sample-2019-cobverted-to-2022.json', 'w+', encoding='utf-8') as f:
    json.dump(new_list, f, indent=2, ensure_ascii=False)

print("End")
