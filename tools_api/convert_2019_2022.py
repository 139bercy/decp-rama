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
        'titulaires': {
            'id': value(marche,['titulaires','id']),
            'typeIdentifiant': value(marche,['titulaires','typeIdentifiant'])
        },
        'typeGroupementOperateurs': value(marche,['typeGroupementOperateurs']),
        'sousTraitanceDeclaree': value(marche,['sousTraitanceDeclaree']),
        'datePublicationDonnees': value(marche,['datePublicationDonnees']),
        'actesSousTraitance': {
            'id': value(marche,['actesSousTraitance','id']),
            'sousTraitant': {
                'id':  None,
                'typeIdentifiant':  None,
                'dureeMois':  None,
                'dateNotification':  None,
                'montant':  None,
                'variationPrix': None,
                'datePublicationDonnees': None
            }
        },
        'modifications': {
            'id': value(marche,['modifications','id']),
            'dureeMois': value(marche,['modifications','dureeMois']),
            'montant': value(marche,['modifications','montant']),
            'titulaires': {
                'id':  value(marche,['modifications','titulaires','id']),
                'typeIdentifiant':  value(marche,['modifications','titulaires','typeIdentifiant'])
            },
            'dateNotificationModification': None,
            'datePublicationDonneesModification': value(marche,['modifications','datePublicationDonneesModification'])
        },
        'modificationsActesSousTraitance': {
            'id': None,
            'dureeMois': None,
            'dateNotificationModificationSousTraitance': None,
            'montant': None,
            'datePublicationDonnees': None
        }
    }
    return marche


def convert_concession(marche):
    return marche
    

# Chargement du fichier JSON
with open('results/decp-2019.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for marche in data['marches']:
    if without_accents(marche["nature"].lower()) in nature_marches_min:
        # Cas d'un marché
        marche = convert_marche(marche)
    else:
        # Cas d'une concession
        marche = convert_concession(marche)

print("End")
