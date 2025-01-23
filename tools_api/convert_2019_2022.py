import json
import unicodedata

MARCHE = "Marché"
SANS_OBJET = ["Sans objet"]
IN_FORME_PRIX = ['Ferme','Ferme et actualisable','Révisable']
OUT_FORME_PRIX = ['Définitif ferme','Définitif actualisable','Définitif révisable']

def without_accents(chaine):
    # Normaliser la chaîne et supprimer les accents
    return ''.join(c for c in unicodedata.normalize('NFD', chaine) if unicodedata.category(c) != 'Mn')

nature_marches = [MARCHE, "Marché de partenariat", "Accord-cadre", "Marché subséquent"]
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


def value(data:dict,nodes:list,default_value:str|int=None):
    value = data
    for node in nodes:
        if value is not None and node in value:
            value = value[node]
        else:
            return default_value
    return value


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


def extract_nature(marche:dict) -> tuple[str,str,str]:
    nature = value(marche,['nature'],MARCHE)
    technique = "NC"
    modalite_execution = "NC"

    if nature == 'Accord-cadre':
        technique = nature
        nature = MARCHE
    elif nature == 'Marchés subséquents':
        modalite_execution = nature
        nature = MARCHE

    return nature,technique,modalite_execution


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
    
    nature,technique,modalite_execution = extract_nature(marche)
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
        'dateNotification': value(marche,['dateNotification']),
        'considerationsSociales': {
            "considerationSociale": ["NC"]
        },
        'considerationsEnvironnementales': {
            "considerationEnvironnementale": ["NC"]
        },
        'marcheInnovant': value(marche,['marcheInnovant'],"NC"),
        'origineUE': value(marche,['origineUE'],"NC"),
        'origineFrance': value(marche,['origineFrance'],"NC"),
        'ccag': value(marche,['ccag'],"NC"),
        'offresRecues': value(marche,['offresRecues'],"NC"),
        'montant': int(value(marche,['montant'])) if value(marche,['montant']) is not None else None,
        'formePrix': "NC",
        'typePrix': type_prix,
        'attributionAvance': value(marche,['attributionAvance'],"NC"),
        'tauxAvance': value(marche,['tauxAvance'],"NC"),
        'titulaires': value_list(marche['titulaires'],['id','typeIdentifiant'],'titulaire') if 'titulaires' in marche else None,
        'typeGroupementOperateurs': value(marche,['typeGroupementOperateurs']),
        'sousTraitanceDeclaree': value(marche,['sousTraitanceDeclaree'],"NC"),
        'datePublicationDonnees': value(marche,['datePublicationDonnees']),
        'modifications': value_list_list(marche,'modifications',['id','dureeMois','montant','titulaires','dateNotificationModification','dateSignatureModification'],'modification','titulaires',['id','typeIdentifiant'],'titulaire')
    }
    rename_node(marche,'modifications','modification','dateSignatureModification','dateNotificationModification')
    remove_empty_list_nodes(marche)

    return marche


def convert_concession(marche):
    print("Concession ",value(marche,['id']))
    marche = {
        'id': value(marche,['id']),
        'autoriteConcedante': value_list([marche['autoriteConcedante']],['id'],'autoriteConcedante') if 'autoriteConcedante' in marche else None,
        'nature': value(marche,['nature']),
        'objet': value(marche,['objet']),
        'procedure': value(marche,['procedure']),
        'dureeMois': value(marche,['dureeMois']),
        'dateDebutExecution': value(marche,['dateDebutExecution']),
        'dateSignature': value(marche,['dateSignature']),
        'considerationsSociales': {
            "considerationSociale": ["NC"]
        },
        'considerationsEnvironnementales': {
            "considerationEnvironnementale": ["NC"]
        },
        'concessionnaires': value_list(marche['concessionnaires'],['id','typeIdentifiant'],'concessionnaire') if 'concessionnaires' in marche else None,
        'valeurGlobale': value(marche,['valeurGlobale']),
        'montantSubventionPublique': value(marche,['montantSubventionPublique']),
        'datePublicationDonnees': value(marche,['datePublicationDonnees']),
        'modifications': value_list_list(marche,'modifications',['id','dureeMois','valeurGlobale','dateSignatureModification','datePublicationDonneesModification'],'modification'),
        'donneesExecution': value_list_list(marche,'donneesExecution',['depensesInvestissement','tarifs','datePublicationDonneesExecution'],'donneeExecution','tarifs',['intituleTarif','tarif'],'tarif'),
    }
    remove_empty_list_nodes(marche)

    return marche


# Chargement du fichier JSON
with open('results/decp-2019.json', 'r', encoding='utf-8') as f:
#with open('results/samples-2019-marches.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

file_path = 'results/sample-2019-converted-to-2022.json'
with open(file_path, 'w') as file:
    file.write("{ \"marches\": [\n")

for marche in data['marches']:
    if ("nature" in marche and marche["nature"] is not None and without_accents(marche["nature"].lower()) in nature_marches_min) or \
        ("_type" in marche and marche["_type"] is not None and marche["_type"] == MARCHE):
        # Cas d'un marché
        marche = convert_marche(marche)
    else:
        # Cas d'une concession
        marche = convert_concession(marche)
    with open(file_path, 'a') as file:
        json.dump(marche, file, indent=2)
        file.write(",\n") # Ajout d'une virgule pour séparer les éléments

with open(file_path, 'rb+') as file:
    file.seek(-2, 2)  # Retour arrière pour enlever la virgule finale
    file.truncate()   # Tronquer le fichier pour enlever cette partie
    file.write(b"\n  ]\n}")

print("End")
