from pandas import json_normalize
import pandas as pd
import numpy as np
import json
import os
from tqdm import tqdm  # Import tqdm

with open(os.path.join(os.getcwd(),"confs", "var_glob.json")) as f:
    conf_glob = json.load(f)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
# pd.set_option('display.width', None)
# pd.set_option('display.max_colwidth', None)
# pd.options.mode.chained_assignment = None

def extract_values(row: list,name:str):
    new_columns = {}

    # create new columns all with nan value
    for value in range(1, 10):
        new_col_name = f'{name}_{value}'
        new_columns[new_col_name] = np.nan

    if not isinstance(row, list):
        return pd.Series(new_columns)

    # fill new columns with values from concessionnaires column if exist
    for num, value in enumerate(row, start=1):
        col_to_fill = f'{name}_{num}'
        # col_name is key in concession dict, col_to_fill is key in new_columns dict. get key value in col_name and put it in col_to_fill
        if value:
            new_columns[col_to_fill] = value
        else:
            new_columns[col_to_fill] = np.nan

    return pd.Series(new_columns)


def manage_modifications(data: dict,data_format:str) -> pd.DataFrame:
    """
    Conversion du json en pandas et incorporation des modifications

    Retour:
        pd.DataFrame
    """

    def convert_boolean(df,col_name:str) -> None:
        """
        Permet de remplacer les valeurs booléennes "1" ou "0", "Vrai" ou "Faux", "True" ou "False" par True ou False

        Args:

            col_name: colonne où s'effectue le changement

        """
        #Conversion si il s'agit de string
        if df[col_name].dtypes == 'object':
            #df[col_name] = df[col_name].astype(str).replace({'1': True, 'true': True, 'True': True, '0': False, 'false': False, 'False': False})
            with pd.option_context("future.no_silent_downcasting", True):
                df[col_name] = df[col_name].replace({1: True, 0: False, '1': True, 'true': True, 'True': True, '0': False, 'false': False, 'False': False}).infer_objects(copy=False)
        else:
            #df[col_name] = df[col_name].astype(str).replace({'True': True, 'False': False })
            with pd.option_context("future.no_silent_downcasting", True):
                df[col_name] = df[col_name].replace({'True': True, 'False': False }).infer_objects(copy=False)
        #df[col_name] = df[col_name].astype(bool)

    L_indice = indice_marche_avec_modification(data)
    dict_modification = recuperation_colonne_a_modifier(data, L_indice)
    df = json_normalize(data['marches'])

    # Fix ECO add empty columns
    complete_data_column(df)

    if "marcheInnovant" in df.columns:
        convert_boolean(df,'marcheInnovant')
    if "attributionAvance" in df.columns:
        convert_boolean(df,'attributionAvance')
    if "sousTraitanceDeclaree" in df.columns:
        convert_boolean(df,'sousTraitanceDeclaree')
        
    # Replace empty strings with NaN (Not a Number) and convert to float
    # Fix FutureWarning df = df.replace(r'^\s*$', np.nan, regex=True)
    with pd.option_context("future.no_silent_downcasting", True):
        df.replace(r'^\s*$', np.nan, regex=True).infer_objects(copy=False)
    df = df.astype(conf_glob["nettoyage"]['type_col_nettoyage'], copy=False)
    prise_en_compte_modifications(df)
    if data_format=='2022':
        if 'titulairesModification' in df.columns:
            prise_en_compte_modifications(df,'titulairesModification','TitulaireModification','titulaire')
        if 'actesSousTraitance' in df.columns:
            prise_en_compte_modifications(df,'actesSousTraitance','ActeSousTraitance','acteSousTraitance')
        if 'modificationsActesSousTraitance' in df.columns:
            prise_en_compte_modifications(df,'modificationsActesSousTraitance','ModificationActeSousTraitance','modificationActesSousTraitance')
        if 'sousTraitantActeSousTraitance' in df.columns:
            prise_en_compte_modifications(df,'sousTraitantActeSousTraitance','SousTraitant')
        if "typesPrix.typePrix" in df.columns:
            if "typesPrix" in df.columns:
                del df["typesPrix"]
            df = df.rename(columns={
                "typesPrix.typePrix": "typesPrix", 
                })
        if "techniques.technique" in df.columns:
            if "techniques" in df.columns:
                del df['techniques']
            df = df.rename(columns={
                "techniques.technique": "techniques", 
                })
        if "modalitesExecution.modaliteExecution" in df.columns:
            if "modalitesExecution" in df.columns:
                del df['modalitesExecution']
            df = df.rename(columns={
                "modalitesExecution.modaliteExecution": "modalitesExecution", 
                })
        if "considerationsEnvironnementales.considerationEnvironnementale" in df.columns:
            if "considerationsEnvironnementales" in df.columns:
                del df['considerationsEnvironnementales']
            df = df.rename(columns={
                "considerationsEnvironnementales.considerationEnvironnementale": "considerationsEnvironnementales", 
                })
        if "considerationsSociales.considerationSociale" in df.columns:
            if "considerationsSociales" in df.columns:
                del df['considerationsSociales']
            df = df.rename(columns={
                "considerationsSociales.considerationSociale": "considerationsSociales",
                })
        if "modificationsActesSousTraitance.modificationActesSousTraitance.id" in df.columns:
            df = df.rename(columns={
                "modificationsActesSousTraitance.modificationActesSousTraitance.id":"idModificationActeSousTraitance",
                })
        if "modificationsActesSousTraitance.modificationActesSousTraitance.dureeMois" in df.columns:
            df = df.rename(columns={
                "modificationsActesSousTraitance.modificationActesSousTraitance.dureeMois":"dureeMoisModificationActeSousTraitance",
                })
        if "modificationsActesSousTraitance.modificationActesSousTraitance.dateNotificationModificationSousTraitance" in df.columns:
            df = df.rename(columns={
                "modificationsActesSousTraitance.modificationActesSousTraitance.dateNotificationModificationSousTraitance":"dateNotificationModificationSousTraitanceModificationActeSousTraitance",
                })
        if "modificationsActesSousTraitance.modificationActesSousTraitance.montant" in df.columns:
            df = df.rename(columns={
                "modificationsActesSousTraitance.modificationActesSousTraitance.montant":"montantModificationActeSousTraitance",
                })
        if "modificationsActesSousTraitance.modificationActesSousTraitance.datePublicationDonnees" in df.columns:
            df = df.rename(columns={
                "modificationsActesSousTraitance.modificationActesSousTraitance.datePublicationDonnees":"datePublicationDonneesModificationActeSousTraitance",
                })
        if "actesSousTraitance.acteSousTraitance.id" in df.columns:
            df = df.rename(columns={
                "actesSousTraitance.acteSousTraitance.id":"idActeSousTraitance",
                })
        if "actesSousTraitance.acteSousTraitance.dureeMois" in df.columns:
            df = df.rename(columns={
                "actesSousTraitance.acteSousTraitance.dureeMois":"dureeMoisActeSousTraitance",
                })
        if "actesSousTraitance.acteSousTraitance.dateNotification" in df.columns:
            df = df.rename(columns={
                "actesSousTraitance.acteSousTraitance.dateNotification":"dateNotificationActeSousTraitance",
                })
        if "actesSousTraitance.acteSousTraitance.montant" in df.columns:
            df = df.rename(columns={
                "actesSousTraitance.acteSousTraitance.montant":"montantActeSousTraitance",
                })
        if "actesSousTraitance.acteSousTraitance.variationPrix" in df.columns:
            df = df.rename(columns={
                "actesSousTraitance.acteSousTraitance.variationPrix":"variationPrixActeSousTraitance",
                })
        if "actesSousTraitance.acteSousTraitance.datePublicationDonnees" in df.columns:
            df = df.rename(columns={
                "actesSousTraitance.acteSousTraitance.datePublicationDonnees":"datePublicationDonneesActeSousTraitance",
                })
        if "actesSousTraitance.acteSousTraitance.sousTraitant.id" in df.columns:
            df = df.rename(columns={
                "actesSousTraitance.acteSousTraitance.sousTraitant.id":"idSousTraitant",
                })
        if "actesSousTraitance.acteSousTraitance.sousTraitant.typeIdentifiant" in df.columns:
            df = df.rename(columns={
                "actesSousTraitance.acteSousTraitance.sousTraitant.typeIdentifiant":"typeIdentifiantSousTraitant",
                })
    else:
        if "concessionnaires.concessionnaire" in df.columns:
            df['concessionnaires'] = df['concessionnaires.concessionnaire'] 
        # ECO if there is a need for unpacking some fields
        #df["considerationsSociales"].apply(extract_values,name='considerationsSociales').join(df)
        #df["considerationsEnvironnementales"].apply(extract_values).join(df)

    #df = regroupement_marche(df, dict_modification)
    # save df to pickle
    df.to_pickle(os.path.join("data", "dfafterconvertsmall.pkl"))
    return df

def complete_data_column(df: pd.DataFrame):
    if 'uid' not in df.columns:
        df['uid']=None
    if 'uuid' not in df.columns:
        df['uuid']=None
    if '_type' not in df.columns:
        df['_type']=None
    if 'denominationSociale' not in df.columns:
        df['denominationSociale']=None
    if 'typeIdentifiant' not in df.columns:
        df['typeIdentifiant']=None
    if 'id' not in df.columns:
        df['id']=None
    if 'source' not in df.columns:
        df['source']=None
    if 'codeCPV' not in df.columns:
        df['codeCPV']=None
    if 'objet' not in df.columns:
        df['objet']=None
    if 'lieuExecution.code' not in df.columns:
        df['lieuExecution.code']=None
    if 'lieuExecution.typeCode' not in df.columns:
        df['lieuExecution.typeCode']=None
    if 'lieuExecution.nom' not in df.columns:
        df['lieuExecution.nom']=None
    if 'dureeMois' not in df.columns:
        df['dureeMois']=None
    if 'montant' not in df.columns:
        df['montant']=None
    if 'formePrix' not in df.columns:
        df['formePrix']=None
    if 'titulaires' not in df.columns:
        df['titulaires']=None
    if 'modifications' not in df.columns:
        df['modifications']=None
    if 'nature' not in df.columns:
        df['nature']=None
    if 'autoriteConcedante.id' not in df.columns:
        df['autoriteConcedante.id']=None
    if 'autoriteConcedante.nom' not in df.columns:
        df['autoriteConcedante.nom']=None
    if 'acheteur.id' not in df.columns:
        df['acheteur.id']=None
    if 'acheteur.nom' not in df.columns:
        df['acheteur.nom']=None
    if 'donneesExecution' not in df.columns:
        df['donneesExecution']=None
    if 'concessionnaires' not in df.columns:
        df['concessionnaires']=None
    if 'Series' not in df.columns:
        df['Series']=None

def indice_marche_avec_modification(data: dict) -> list:
    """
    Renvoie la liste des indices des marchés contenant une modification

    Retour:
        - list
    """
    liste_indices = []
    for i in range(len(data["marches"])):
        # Ajout d'un identifiant technique -> Permet d'avoir une colonne id unique par marché
        data["marches"][i]["id_technique"] = i
        if "modifications" in data["marches"][i]:
            if data["marches"][i]["modifications"]:
                liste_indices += [i]
    return liste_indices


def recuperation_colonne_a_modifier(data: dict, liste_indices: list) -> dict:
    """
    Renvoie les noms des differentes colonnes recevant une modification
    sous la forme d'un dictionnaire: {Nom_avec_modification: Nom_sans_modification}

    Retour:
        dict
    """
    liste_colonne = []
    colonne_to_modify = {}
    for indice in liste_indices:
        # colonne_modifiees = list(data["marches"][indice]["modifications"][0].keys())
        modifications = data["marches"][indice]["modifications"]
        if modifications and isinstance(modifications, list) and isinstance(modifications[0], dict):
            for col in modifications[0].keys():
                if "Modification" not in col:
                    col += "Modification"
                if col not in liste_colonne:
                    liste_colonne += [col]
    for col in liste_colonne:
        if "Modification" in col and col != "objetModification":
            name_col = col.replace("Modification", "")
            colonne_to_modify[col] = name_col
        else:
            colonne_to_modify[col] = col
    return colonne_to_modify


def prise_en_compte_modifications(df: pd.DataFrame, col_to_normalize: str = 'modifications',
                                  col_suffix: str='Modification',sub_element: str='modification'):
    """
    La fonction json_normalize de pandas ne permet pas de spliter la clef modifications automatiquement.
    Cette fonction permet de le faire
    En entrée : La sortie json_normalize de pandas. (avec une colonne modifications)
    Le dataframe en entrée est directement modifié dans la fonction.
    """
    # Check colonne modifications.
    if col_to_normalize not in df.columns:
        raise ValueError("Il n'y a aucune colonne du nom de {} dans le dataframe entrée en paramètre".format(col_to_normalize))
    to_normalize = df[col_to_normalize]  # Récupération de la colonne à splitter
    df["boolean"+col_suffix] = 0
    for i in range(len(to_normalize)):  #pour chaque ligne de la colonne "modifications"
        json_modification = to_normalize[i]
        if type(json_modification)==dict:
            json_modification = [json_modification]
        if type(json_modification) == list:
            if json_modification != []:  # dans le cas où des modifications ont été apportées
                if len(json_modification[0])>1:   # json_modification [0] est un dictionnaire. C'est le seul élément de la liste
                    for col in json_modification[0].keys():
                        col_init = col
                        # Formatage du nom de la colonne
                        if col_suffix not in col:
                            col += col_suffix
                        # Cas où on tombe sur le premier marche qui modifie un champ
                        if col not in df.columns:  
                            df[col] = "" # Initialisation dans le df initial
                        #Cas particulier
                        if (col == "objetModification") and (json_modification[0][col_init] != None) and (isinstance(json_modification[0][col_init], str)):
                            df.at[i,col]= json_modification[0][col_init].replace("\n", "\\n").replace("\r", "\\r")
                        else:
                            df.at[i,col] = json_modification[0][col_init]    
                        df.at[i,"boolean"+col_suffix] = 1  # Création d'une nouvelle colonne booléenne pour simplifier le subset pour la suite
                       
                else:
                    if sub_element in json_modification[0] and isinstance(json_modification[0][sub_element],dict):
                        for col in json_modification[0][sub_element].keys():
                            col_init = col
                            # Formatage du nom de la colonne
                            if col_suffix not in col:
                                col += col_suffix
                            # Cas ou on tombe sur le premier marche qui modifie un champ
                            if col not in df.columns:  
                                df[col] = ""  # Initialisation dans le df initial
                            if (col == "objetModification") and (json_modification[0][sub_element][col_init] != None) and (isinstance(json_modification[0][sub_element][col_init], str)):
                                 df.at[i,col] = json_modification[0][sub_element][col_init].replace("\n", "\\n").replace("\r", "\\r")
                            else:
                                 df.at[i,col] = json_modification[0][sub_element][col_init]
                            df.loc[i,"boolean"+col_suffix] = 1  # Création d'une booléenne pour simplifier le subset pour la suite


def regroupement_marche(df: pd.DataFrame, dict_modification: dict) -> pd.DataFrame:
    """
    Permet de recoder la variable identifiant.
    Actuellement: 1 identifiant par déclaration (marché avec ou sans modification)
    Un marché peut être déclaré plusieurs fois en fonction du nombre d'entreprise. Si 2 entreprises sur
    En sortie: id correspondra à un identifiant unique pour toutes les lignes composants un marché SI il a eu une modification
    Modification inplace du df source

    Retour:
        pd.DataFrame
    """
    df["idtech"] = ""
    subdata_modif = df[df.booleanModification == 1]  # Tout les marchés avec les modifications
    liste_objet = list(subdata_modif.objet.unique())
    df_to_concatene = pd.DataFrame()  # df vide pour la concaténation
    for objet_marche in tqdm(liste_objet, desc="Processing objet marchés"):
        # Récupération du dataframe modification et du dataframe source
        marche, marche_init = split_dataframe(df, subdata_modif, objet_marche)
        for j in range(len(marche)):
            marche_init = fusion_source_modification(marche.iloc[j], marche_init, dict_modification.keys(), dict_modification)
        marche_init["idtech"] = marche.iloc[-1].id_technique
        df_to_concatene = pd.concat([df_to_concatene, marche_init], copy=False)
    df.update(df_to_concatene)
    # Attention aux id.
    df["idMarche"] = np.where(df.idtech != "", df.idtech, df.id_technique)
    return df


def split_dataframe(df: pd.DataFrame, sub_data: pd.DataFrame, modalite: str) -> tuple:
    """
    Définition de deux dataFrame.
        - Le premier qui contiendra uniquement les lignes avec modification, pour le marché ayant pour objet modalite
        - Le second contiendra l'ensemble des lignes correspondant au marché isolé dans le df1 qui ont pour objet modalite

        :param df: la source totale des données
        :param sub_data: le sous-ensemble correspondant à l'ensemble des marchés avec une modification
        :param modalite: la modalité sur laquelle on veut filtrer

        Retour:
            tuple (pd.DataFrame, pd.DataFrame)
    """
    # Premier df: Contenant les lignes d'un marche avec des colonnes modifications non vide
    marche = sub_data[sub_data.objet == modalite]
    marche = marche.sort_values(by='id')
    # Second dataframe: Dans le df complet, récupération des lignes correspondant au marché récupéré
    date = marche.datePublicationDonnees.iloc[0]
    # A concaténer ?
    marche_init = df[df.objet == modalite]
    marche_init = marche_init[marche_init.datePublicationDonnees == date]
    return (marche, marche_init)


def fusion_source_modification(raw: pd.DataFrame, df_source: pd.DataFrame, col_modification: list, dict_modification: dict) -> pd.DataFrame:
    """
    Permet de fusionner les colonnes xxxModification et sa colonne.
    raw correspond à une ligne du df_source
    Modifie le df_source

    Retour:
        pd.DataFrame
    """
    for col in col_modification:
        col_init = dict_modification[col]
        if raw[col] != '':
            df_source[col_init].loc[raw.name] = raw[col]
    return df_source


def regroupement_marche_(df: pd.DataFrame, dict_modification: dict) -> pd.DataFrame:
    # Assuming you've generated the 'booleanModification' column in df

    # Create a dictionary to store the modified marché dataframes
    modified_marches = {}

    # Group data by "objet" and loop through each group
    for objet_marche, group in tqdm(df[df["booleanModification"] == 1].groupby("objet"), desc="Processing objet marchés"):
        # Initialize the modified marché dataframe with the last row of the group
        modified_marche = group.iloc[-1].copy()

        # Apply modifications from the dict_modification
        modified_marche = fusion_source_modification(modified_marche, group, dict_modification.keys(),
                                                     dict_modification)

        # Store the modified marché dataframe
        modified_marches[objet_marche] = modified_marche

    # Update the original dataframe with the modified marché dataframes
    for objet_marche, modified_marche in tqdm(modified_marches.items(), desc="Updating original dataframe"):
        mask = df["objet"] == objet_marche
        df.loc[mask] = modified_marche

    # Update idMarche based on idtech or id_technique
    df["idMarche"] = np.where(df["idtech"] != "", df["idtech"], df["id_technique"])

    return df
