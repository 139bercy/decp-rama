import json
import unicodedata
import pandas as pd
import numpy as np

NC = "NC"
MARCHE = "Marché"
CONCESSION = "Concession"
ACCORD_CADRE = "Accord-cadre"
SANS_OBJET = ["Sans objet"]
IN_FORME_PRIX = ['Ferme','Ferme et actualisable','Révisable']
OUT_FORME_PRIX = ['Définitif ferme','Définitif actualisable','Définitif révisable']
duplicate_marche_key =  ["id", "acheteur", "titulaires", "dateNotification", "montant"] 
duplicate_concession_key =  [ "id", "autoriteConcedante", "concessionnaires", "dateDebutExecution", "valeurGlobale"]

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

def _add_meta_modifications(df_marches,df_concessions,process_dates:bool=True):
    
    def _tri_titulaires(titulaires):
        """Cette fonction trie les titulaires par id afin d'éviter les erreurs de calcul de doublons lorsque l'ordre dans les données en entrée change."""
        return sorted(titulaires, key=lambda x: x['titulaire']['id']) if isinstance(titulaires, list) else titulaires

    def _tri_concessionnaires(concessionnaires):
        """Cette fonction trie les concessionnaires par id afin d'éviter les erreurs de calcul de doublons lorsque l'ordre dans les données en entrée change."""
        return sorted(concessionnaires, key=lambda x: x['concessionnaire']['id']) if isinstance(concessionnaires, list) else concessionnaires

    if not df_marches.empty:
        df_marches['titulaires'] = df_marches['titulaires'].apply(_tri_titulaires)

    if not df_concessions.empty:
        df_concessions['concessionnaires'] = df_concessions['concessionnaires'].apply(_tri_concessionnaires)

def dedoublonnage(df: pd.DataFrame,add_report=True) -> pd.DataFrame:
    nb_duplicated_marches = 0
    nb_duplicated_concessions = 0

    # On complete la colonne backup montant pour les marches ajoutés depuisl'export qui ne sont pas passé par fix
    if "montant" in df.columns and 'backup__montant' in df.columns \
        and df.loc[df['_type'] == 'Marché', 'backup__montant'].isna().any():
        df.loc[(df['backup__montant'].isna()) & (df['_type'] == 'Marché'), 'backup__montant'] = df['montant']
        df.loc[df['_type'] == 'Marché', 'montant'] = df.loc[df['_type'] == 'Marché', 'montant'].apply(lambda x: int(x) if pd.notna(x) else np.nan)

    if "modifications" in df.columns: # Règles de dédoublonnages diffèrentes. On part du principe qu'en cas 
        # de modifications, la colonne "modifications" est créée ou modifiée
        df_modif = df[df.modifications.apply(lambda x: 0 if x == '' or
                                                    str(x) in ['nan', 'None'] else len(x))>0]     #lignes avec modifs     
        df_nomodif = df[df.modifications.apply(lambda x: 0 if x == '' or
                                                    str(x) in ['nan', 'None'] else len(x))==0]  #lignes sans aucune modif
    else:
        df_modif = pd.DataFrame() 
        df_nomodif = df

    #Critères de dédoublonnage
    feature_doublons_marche = ["id", "acheteur", "titulaires", "dateNotification", "montant"] 
    feature_doublons_concession = [ "id", "autoriteConcedante", "concessionnaires", "dateDebutExecution", "valeurGlobale"]

    #Séparation des marches et des concessions, suppression des doublons
    df_nomodif_str = df_nomodif.astype(str)
    df_nomodif_marche = df_nomodif_str[df_nomodif_str['_type'].str.contains("Marché")]
    index_to_keep_nomodif = df_nomodif_marche.drop_duplicates(subset=feature_doublons_marche).index.tolist()

    # Mémoriser la nombre de marchés en double
    nb_duplicated_marches_no_modif = len(df_nomodif_marche)-len(index_to_keep_nomodif)


    df_nomodif_concession = df_nomodif_str[~df_nomodif_str['_type'].str.contains("Marché")]
    index_to_keep_nomodif += df_nomodif_concession.drop_duplicates(subset=feature_doublons_concession).index.tolist()

    # Mémoriser la nombre de concessions après dédoublonnage
    nb_duplicated_concessions_no_modif = len(df_nomodif_concession) - ( len(index_to_keep_nomodif) - (len(df_nomodif_marche) - nb_duplicated_marches_no_modif) )

    #Séparation des marches et des concessions, tri selon la date et suppression ses doublons
    if not df_modif.empty:
        df_modif_str  = df_modif.astype(str)     #en str pour réaliser le dédoublonnage
        df_modif_str.sort_values(by=["datePublicationDonnees"], inplace=True)   #Tri
        
        df_modif_marche = df_modif_str[df_modif_str['_type'].str.contains("Marché")]
        index_to_keep_modif = df_modif_marche.drop_duplicates(subset=feature_doublons_marche,keep='last').index.tolist()  #'last', permet de garder la ligne avec la date est la plus récente

        # Mémoriser la nombre de marchés après dédoublonnage
        nb_duplicated_marches = len(df_modif_marche)-len(index_to_keep_modif)

        df_modif_concession = df_modif_str[~df_modif_str['_type'].str.contains("Marché")]
        index_to_keep_modif += df_modif_concession.drop_duplicates(subset=feature_doublons_concession,keep='last').index.tolist()  #on ne garde que que les indexs pour récupérer les lignes qui sont dans df_modif (dont le type est dict)

        # Mémoriser la nombre de concessions après dédoublonnage
        nb_duplicated_concessions = len(df_modif_concession) - ( len(index_to_keep_modif) - ( len(df_modif_marche) - nb_duplicated_marches ) )

        df = pd.concat([df_nomodif.loc[index_to_keep_nomodif, :], df_modif.loc[index_to_keep_modif, :]])

    else:
        df = df_nomodif.loc[index_to_keep_nomodif, :]
    df = df.reset_index(drop=True)
    
    return df


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

def value_str(data:dict,nodes:list,default_value:str|int=None):
    value = data
    for node in nodes:
        if value is not None and node in value:
            value = str(value[node])
        else:
            return default_value
    return value


def value_list(data:list,attributes:list,sub_node:str,default_value:str=None):
    result = []
    if data is not None:
        for element in data:
            if element is not None:
                new_element = {sub_node: {}}
                for attribute in attributes:
                    if attribute == 'typeIdentifiant':
                        new_element[sub_node][attribute] = convert_type_identifiant(element)    
                    else:
                        new_element[sub_node][attribute] = value(element,[attribute],default_value=default_value)
                result.append(new_element)
    return result

def value_list_str(data:list,attributes:list,sub_node:str,default_value:str=None):
    result = []
    if data is not None:
        for element in data:
            if element is not None:
                new_element = {sub_node: {}}
                for attribute in attributes:
                    if attribute == 'typeIdentifiant':
                        new_element[sub_node][attribute] = convert_type_identifiant(element)    
                    else:
                        new_element[sub_node][attribute] = value_str(element,[attribute],default_value=default_value)
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
    nature = value(marche,['nature'],MARCHE)
    if nature is None:
        nature = value(marche,['_type'],MARCHE)
    technique = NC
    modalite_execution = NC
    if without_accents(nature.lower()) in nature_marches_min:
        index = nature_marches_min.index(without_accents(nature.lower()))
    else:
        index = 0
    nature = nature_marches[index]    

    if nature.lower() == ACCORD_CADRE.lower():
        technique = nature
        nature = MARCHE
    elif nature.lower() == 'marchés subséquents':
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
        'dateNotification': value(marche,['dateNotification']),
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
        'titulaires': value_list_str(marche['titulaires'],['id','typeIdentifiant'],'titulaire',"") if 'titulaires' in marche else None,
        'typeGroupementOperateurs': value(marche,['typeGroupementOperateurs']),
        'sousTraitanceDeclaree': value(marche,['sousTraitanceDeclaree'],NC),
        'datePublicationDonnees': value(marche,['datePublicationDonnees']),
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
        'id': value(marche,['id']),
        'autoriteConcedante': value_list([marche['autoriteConcedante']],['id'],'autoriteConcedante') if 'autoriteConcedante' in marche else None,
        'nature': nature,
        'objet': value(marche,['objet']),
        'procedure': value(marche,['procedure']),
        'dureeMois': value(marche,['dureeMois']),
        'dateDebutExecution': value(marche,['dateDebutExecution']),
        'dateSignature': value(marche,['dateSignature']),
        'considerationsSociales': {
            "considerationSociale": [NC]
        },
        'considerationsEnvironnementales': {
            "considerationEnvironnementale": [NC]
        },
        'concessionnaires': value_list(marche['concessionnaires'],['id','typeIdentifiant'],'concessionnaire') if 'concessionnaires' in marche else None,
        'valeurGlobale': value(marche,['valeurGlobale']),
        'montantSubventionPublique': value(marche,['montantSubventionPublique']),
        'datePublicationDonnees': value(marche,['datePublicationDonnees']),
        'modifications': value_list_list(marche,'modifications',['id','dureeMois','valeurGlobale','dateSignatureModification','datePublicationDonneesModification'],'modification'),
        'donneesExecution': value_list_list(marche,'donneesExecution',['depensesInvestissement','tarifs','datePublicationDonneesExecution'],'donneeExecution','tarifs',['intituleTarif','tarif'],'tarif'),
        '_type': CONCESSION,
        'source': value(marche,['source'],NC)
    }
    remove_empty_list_nodes(marche)

    return marche


# Chargement du fichier JSON
with open('results/decp-2019.json', 'r', encoding='utf-8') as f:
#with open('results/samples-2019-marches.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

file_path = 'results/sample-2019-converted-to-2022_full.json'
with open(file_path, 'w', encoding='utf-8') as file:
    file.write("{ \"marches\": [\n")

marches=[]
concessions = []

for marche in data['marches']:
    if ("nature" in marche and marche["nature"] is not None and without_accents(marche["nature"].lower()) in nature_marches_min) or \
        ("_type" in marche and marche["_type"] is not None and marche["_type"] == MARCHE) or \
        "titulaires" in marche:
        # Cas d'un marché
        marches += [convert_marche(marche)]
    else:
        # Cas d'une concession
        concessions += [convert_concession(marche)]

print(f"marchés : {len(marches)}")
print(f"concessions : {len(concessions)}")

# Build DataFrame to drop duplicates
df_marches = pd.DataFrame.from_dict(marches)
df_concessions = pd.DataFrame.from_dict(concessions)
_add_meta_modifications(df_marches,df_concessions,False)

print("Dedoublonnage")

df_marches['backup__montant'] = df_marches['montant']
df_marches['montant'] = df_marches['montant'].apply(lambda x: int(x) if pd.notna(x) else np.nan)
dedoublonnage(df_marches,False)
if 'backup__montant' in df_marches:
    df_marches['montant'] = df_marches['backup__montant']
    del df_marches['backup__montant']

print(f"marchés : {len(df_marches)}")
marches =  [{k: v for k, v in m.items() if str(v) != 'nan'}
                for m in df_marches.to_dict(orient='records')]
print(f"marchés : {len(marches)}")

comma = False
with open(file_path, 'a', encoding='utf-8') as file:
    for marche in marches:
            if comma:
                file.write(",\n") # Ajout d'une virgule pour séparer les éléments
            else:
                comma = True
            json.dump(marche, file, indent=2, ensure_ascii=False)

dedoublonnage(df_concessions,False)
print(f"concessions : {len(df_concessions)}")
concessions =  [{k: v for k, v in m.items() if str(v) != 'nan'}
                for m in df_concessions.to_dict(orient='records')]
print(f"concessions : {len(concessions)}")

comma = False
with open(file_path, 'a', encoding='utf-8') as file:
    file.write("},\"\"") # Ajout d'une virgule pour séparer les éléments
    for concession in concessions:
            if comma:
                file.write(",\n") # Ajout d'une virgule pour séparer les éléments
            else:
                comma = True
            json.dump(concession, file, indent=2, ensure_ascii=False)

with open(file_path, 'a', encoding='utf-8') as file:
    file.write("\n  ]\n}")

print("End")
