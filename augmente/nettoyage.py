import json
import os
import pickle
import logging.handlers
import re
import math
import argparse
import numpy as np
import pandas as pd,csv
import augmente.utils
import time
from datetime import datetime
import augmente.convert_json_to_pandas
from utils.StepMngmt import StepMngmt
from utils.Step import Step

from stdnum import luhn
from stdnum.exceptions import *
from stdnum.fr import siren
from stdnum.util import clean

from reporting.Report import Report


PATTERN_DATE = r'^20[0-9]{2}-[0-1]{1}[0-9]{1}-[0-3]{1}[0-9]{1}$'
light_errors = []


logger = logging.getLogger("main.nettoyage2")
logger.setLevel(logging.DEBUG)
pd.options.mode.chained_assignment = None  # default='warn'

report = Report('augmente')

with open(os.path.join("confs", "var_glob.json")) as f:
    conf_glob = json.load(f)

def compute_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logging.info(f"Execution time of {func.__name__}: {execution_time} seconds")
        return result
    return wrapper


path_to_conf = "confs"
if not (os.path.exists(path_to_conf)):  # Si le chemin confs n'existe pas (dans le cas de la CI et de Saagie)
    os.mkdir(path_to_conf)
with open(os.path.join("confs", "config_data.json")) as f:
    conf_data = json.load(f)

path_to_data = conf_data["path_to_data"]
decp_file_name = conf_data["decp_file_name"]
#path_to_data = conf_data["path_to_data"]  # Réécris


def main(data_format:str = '2022'):
    step = StepMngmt()
    if not step.bypass(StepMngmt.SOURCE_ALL,Step.AUGMENTE_CLEAN):
        logger.info("Chargement des données")
        # load data from local
        args = augmente.utils.parse_args()

        logger.info("Format utilisé " + data_format)

        #json_source = 'decp_'+data_format +'.json'
        json_source = f"results/decp-daily.json"

        logger.info(f"Opening {json_source}")
        with open(json_source, 'rb') as f:
            # c'est long de charger le json, je conseille de le faire une fois et de sauvegarder le df en pickle pour les tests
            df = augmente.convert_json_to_pandas.manage_modifications(json.load(f),data_format)
        if args.test:
            #m = math.ceil(len(df.index)/3)
            df = df.sample(n=len(df.index), random_state=1)   #on récupère tous les marchés et concessions
            logger.info("Mode test activé")

        logger.info("Nettoyage des données")
        manage_data_quality(df,data_format)

        #Étant donné qu'on ne fait pas l'enrichissement pour l'instant le programme s'arrête ici et on upload les 4 fichiers.

        step.snapshot_dataframe(StepMngmt.SOURCE_ALL,Step.AUGMENTE_CLEAN,df)

def restore_nc(df,field):
    if 'backup__'+field in df.columns:
        df[field] = df.apply(lambda row: row['backup__'+field] if pd.isna(row[field]) or row['backup__'+field] == 'NC' else row[field], axis=1)

# Fonction pour remplacer les valeurs
def modifier_source(valeur):
    if valeur == 'data.gouv.fr_pes':
        return 'DGFIP – PES marche'
    elif valeur == 'marches-publics_aws':
        return 'AWS'
    elif valeur == 'e-marchespublics':
        return 'Dematis'
    elif valeur == 'xmarches':
        return 'SPL-XDEMAT'
    elif valeur == 'ppsmj':
        return 'Region Ile-de-France'
    return valeur  # Renvoie la valeur d'origine si aucune correspondance n'est trouvée

@compute_execution_time
def manage_data_quality(df: pd.DataFrame,data_format:str):
    """
    Cette fonction sépare en deux le dataframe d'entrée. Les données ne respectant pas les formats indiqués par les
    règles de gestion de la DAJ sont mise de côtés. Les règles de gestions sont dans un mail du 15 février 2023.

    /!\
    Dans les règles de gestion, certaine valeur de champ d'identification unique du marché ne sont pas accessibles
    dans la donnée brute. On va donc ne traiter dans cette fonction que les variables accessibles de manières brutes
    et lorsque les règles portent sur des variables non brutes, on appliquera les règles à ce moment-là. (ex : idtitulaire)
    /!\

    Les lignes exclues seront publiées sur data.economie.gouv.fr dans un fichier csv.

    Args:
    ----------
    df :  le dataframe des données bruts.


    Return
    -----------
    df (dataFrame) : le dataframe des données à enrichir.
    df_badlines (dataFrame) : le dataframe des données exclues.

    """
    def convert_list_to_str(df,col):
        if col in df.columns:
            df[col] = df[col].str[2:-2] #.apply(lambda x: ', '.join(map(str, x)))

    def convert_all_list_to_str(df):
        convert_list_to_str(df,'considerationsSociales')
        convert_list_to_str(df,'considerationsEnvironnementales')
        convert_list_to_str(df,'modalitesExecution')
        convert_list_to_str(df,'techniques')
        convert_list_to_str(df,'typesPrix')

    def convert_col_boolean(df,col):
        if col in df.columns:
            df[col] = df[col].map({'True': True, 'False': False})
            df[col] = df[col].apply(lambda x: 'oui' if x else 'non')

    def convert_boolean(df):
        convert_col_boolean(df,'marcheInnovant')
        convert_col_boolean(df,'attributionAvance')
        convert_col_boolean(df,'sousTraitanceDeclaree')

    # séparation des marchés et des concessions, car traitement différent
    df_marche = None
    df_concession = None

    if data_format=='2019':
        df_marche = df.loc[~df['nature'].str.contains('concession', case=False, na=False)]

        df_concession1 = df.loc[df['nature'].str.contains('concession', case=False, na=False)]
        # df_concession prend aussi en compte les lignes restantes ou la colonne "_type" contient "concession" dans le df_marche et concatène les deux dataframes
        df_concession = pd.concat([df_concession1, df_marche.loc[df_marche['_type'].str.contains('concession', case=False, na=False)]])
        # remove old df for memory
        del df_concession1
        df_marche = df_marche.loc[~df_marche['_type'].str.contains('concession', case=False, na=False)]
    else:
        df_marche = df.loc[df['_type'].str.contains('March', case=False, na=False)]
        df_concession = df.loc[~df['_type'].str.contains('March', case=False, na=False)]

    delete_columns(df_concession,"concession_"+data_format)
    augmente.utils.save_csv(df_concession, "concession.csv")

    delete_columns(df_marche,"marche_"+data_format)
    augmente.utils.save_csv(df_marche, "marche.csv")

    if not df_concession.empty:
        replace_nc_colonne(df_concession,'dureeMois')
        df_concession, df_concession_badlines = regles_concession(df_concession,data_format)
    else:
        df_concession = pd.DataFrame([])
        df_concession_badlines = pd.DataFrame([])

    if not df_marche.empty:
        # Replace NC with NA
        replace_nc_colonne(df_marche,'offresRecues')
        replace_nc_colonne(df_marche,'marcheInnovant')
        replace_nc_colonne(df_marche,'attributionAvance')
        replace_nc_colonne(df_marche,'sousTraitanceDeclaree')
        replace_nc_colonne(df_marche,'dureeMois')
        #replace_nc_colonne(df_marche,'variationPrixActeSousTraitance')
        #replace_nc_colonne(df_marche,'dureeMoisActeSousTraitance',True)
        df_marche, df_marche_badlines = regles_marche(df_marche,data_format)
    else:
        df_marche = pd.DataFrame([])
        df_marche_badlines = pd.DataFrame([])
    
    # Reporting
    report.nb_out_bad_marches = len(df_marche_badlines)
    # deja reporté report.add('Regles marchés','BAD_MARCHE','Marchés inconsistants',df_marche_badlines)

    if data_format=="2022":
        if not df_concession.empty:
            restore_nc(df_concession,'dureeMois')

            df_concession = stabilize_columns(df_concession,"concession_"+data_format)
            df_concession_badlines = stabilize_columns(df_concession_badlines,"concession_"+data_format,True)

            df_concession = concession_mark_fields(df_concession)

        if not df_marche.empty:
            restore_nc(df_marche,'offresRecues')
            restore_nc(df_marche,'marcheInnovant')
            restore_nc(df_marche,'attributionAvance')
            restore_nc(df_marche,'sousTraitanceDeclaree')
            restore_nc(df_marche,'dureeMois')
            restore_nc(df_marche,'dureeMoisActeSousTraitance')
            restore_nc(df_marche,'variationPrixActeSousTraitance')

            df_marche = stabilize_columns(df_marche,"marche_"+data_format)
            df_marche_badlines = stabilize_columns(df_marche_badlines,"marche_"+data_format,True)
            
            df_marche = marche_mark_fields(df_marche)

    # Reporting
    report.nb_out_bad_concessions = len(df_concession_badlines)
    # deja reporté report.add('Regles concessions','P_BAD_CONCESSION','Concessions inconsistantes',df_concession_badlines)

    if not df_concession.empty:
        logging.info("Concession valides : "+ str(df_concession.shape[0]))
        logging.info("Concession mauvaises : "+ str(df_concession_badlines.shape[0]))
        logging.info("Concession mal rempli % : "+ str((df_concession_badlines.shape[0] / (df_concession.shape[0] + df_concession_badlines.shape[0]) * 100)))
    else:
        logging.info("Aucune concession traitée")
        
    if not df_marche.empty:
        logging.info("Marchés valides : "+ str(df_marche.shape[0]))
        logging.info("Marché mauvais : "+ str(df_marche_badlines.shape[0]))
        logging.info("Marché mal rempli % : "+ str((df_marche_badlines.shape[0] / (df_marche.shape[0] + df_marche_badlines.shape[0]) * 100)))
    else:
        #df_marche_badlines = df_marche.empty
        logging.info("Aucun marché traité")

    # Formater la date sous le format "YYYY-MM-DD"
    maintenant = datetime.now() 
    date = maintenant.strftime("%Y-%m-%d")

    report.fix_statistics('all sources')
    report.save()

    if not df_concession.empty:
        if 'source' in df_concession.columns:
            # Modification de la colonne 'source'
            df_concession['source'] = df_concession['source'].apply(modifier_source)
        # save data to csv files
        if 'objet' not in df_concession.columns:
            df_concession['objet'] = pd.NA    
        else:
            df_concession['objet'] = df_concession['objet'].str.replace('\n', '\\n', regex=False)
            df_concession['objet'] = df_concession['objet'].str.replace('\r', '\\r', regex=False)
    convert_all_list_to_str(df_concession)
    convert_boolean(df_concession)
    df_concession.to_csv(os.path.join(conf_data["path_to_data"], f'{date}-concession-{data_format}.csv'), index=False, header=True)
    
    if not df_marche.empty:
        if 'source' in df_marche.columns:
            # Modification de la colonne 'source'
            df_marche['source'] = df_marche['source'].apply(modifier_source)
        if 'objet' not in df_marche.columns:
            df_marche['objet'] = pd.NA
        else:
            df_marche['objet'] = df_marche['objet'].str.replace('\n', '\\n', regex=False)
            df_marche['objet'] = df_marche['objet'].str.replace('\r', '\\r', regex=False)
    convert_all_list_to_str(df_marche)
    convert_boolean(df_marche)
    df_marche.to_csv(os.path.join(conf_data["path_to_data"], f'{date}-marche-{data_format}.csv'), index=False, header=True)
    
    if not df_marche_badlines.empty:
        if 'source' in df_marche_badlines.columns:
            # Modification de la colonne 'source'
            df_marche_badlines['source'] = df_marche_badlines['source'].apply(modifier_source)
        if 'objet' not in df_marche_badlines.columns:
            df_marche_badlines['objet'] = pd.NA
        else:
            df_marche_badlines['objet'] = df_marche_badlines['objet'].str.replace('\n', '\\n', regex=False)
            df_marche_badlines['objet'] = df_marche_badlines['objet'].str.replace('\r', '\\r', regex=False)
    convert_all_list_to_str(df_marche_badlines)
    convert_boolean(df_marche_badlines)
    df_marche_badlines.to_csv(os.path.join(conf_data["path_to_data"], f'{date}-marche-exclu-{data_format}.csv'), index=False,  header=True)
    
    if not df_concession_badlines.empty:
        if 'source' in df_concession_badlines.columns:
            # Modification de la colonne 'source'
            df_concession_badlines['source'] = df_concession_badlines['source'].apply(modifier_source)
        if 'objet' not in df_concession_badlines.columns:
            df_concession_badlines['objet'] = pd.NA    
        else:
            df_concession_badlines['objet'] = df_concession_badlines['objet'].str.replace('\n', '\\n', regex=False)
            df_concession_badlines['objet'] = df_concession_badlines['objet'].str.replace('\r', '\\r', regex=False)
    convert_all_list_to_str(df_concession_badlines)
    convert_boolean(df_concession_badlines)
    df_concession_badlines.to_csv(os.path.join(conf_data["path_to_data"], f'{date}-concession-exclu-{data_format}.csv'), index=False,  header=True)

    # Concaténation des dataframes pour l'enrigissement (re-séparation après)
    df = pd.concat([df_concession, df_marche])

    return df

def delete_columns(df:pd.DataFrame,set:str):
    columns_to_delete = conf_glob["purge_df_"+set]
    for column in columns_to_delete:
        if column in df.columns:
            del df[column]

def populate_error(dfb:pd.DataFrame,error_message:str,message_for_all:bool=False):
    bool_nan_errors = dfb.loc[:, "Erreurs"].isna()
    dfb.loc[bool_nan_errors, "Erreurs"] = error_message
    
    if message_for_all:
        report.add_forced('nettoyage',report.D_DATA,error_message,dfb)
    else:
        report.add_forced('nettoyage',report.D_DATA,error_message,dfb.loc[bool_nan_errors])

    return dfb

def df_add_error(df:pd.DataFrame,selection,message:str) -> pd.DataFrame:
    df.loc[selection, 'Erreurs'] = (
        df.loc[selection, 'Erreurs'].fillna('') +
        (df.loc[selection, 'Erreurs'].notna().map(lambda x: '; ' if x else '')) +
        message
    )
    return df    

def reorder_columns(dfb:pd.DataFrame):
    """
    La fonction a pour but de mettre en première position 
    la colonne "Erreur". Si la colonne est déja présente,
    on ne la rajoute pas.
    """
    newColumnsTitle = ['Erreurs']

    for col in dfb.columns:
        if col != 'Erreurs':
            newColumnsTitle.append(col)
    return dfb.reindex(columns=newColumnsTitle)

def order_columns_marches(df: pd.DataFrame):
    """
    La fonction ordonne les colonnes d'une marché
    du dataframe dans l'ordre indiqué de la liste.
    """
    liste_col_ordonnes = [
    "titulaire_id_1",
    "titulaire_typeIdentifiant_1",
    "titulaire_id_2",
    "titulaire_typeIdentifiant_2",
    "titulaire_id_3",
    "titulaire_typeIdentifiant_3",
    "id",
    "nature",
    "objet",
    "codeCPV",
    "procedure",
    "dureeMois",
    "dateNotification",
    "datePublicationDonnees",
    'source',
    "montant",
    "formePrix",
    "attributionAvance",
    "offresRecues",
    "marcheInnovant",
    "ccag",
    "sousTraitanceDeclaree",
    "typeGroupementOperateurs",
    "idAccordCadre",
    "acheteur.id",
    "lieuExecution.code",
    "lieuExecution.typeCode",
    "considerationsSociales",
    "considerationsEnvironnementales",
    "modalitesExecution",
    "techniques",
    "typesPrix",
    "tauxAvance",
    "origineUE",
    "origineFrance",
    "idActeSousTraitance",
    "dureeMoisActeSousTraitance",
    "dateNotificationActeSousTraitance",
    "datePublicationDonneesActeSousTraitance",
    "montantActeSousTraitance",
    "variationPrixActeSousTraitance",
    "idSousTraitant",
    "typeIdentifiantSousTraitant",
    "idModification",
    "montantModification",
    "dureeMoisModification",
    "idTitulaireModification",
    "typeIdentifiantTitulaireModification",
    "dateNotificationModificationModification",
    "datePublicationDonneesModificationModification",
    "idModificationActeSousTraitance",
    "dureeMoisModificationActeSousTraitance",
    "dateNotificationModificationSousTraitanceModificationActeSousTraitance",
    "montantModificationActeSousTraitance",
    "datePublicationDonneesModificationActeSousTraitance",
    "backup__offresRecues",
    "backup__marcheInnovant",
    "backup__attributionAvance",
    "backup__sousTraitanceDeclaree",
    "backup__dureeMois",
    "backup__dureeMoisActeSousTraitance",
    "backup__variationPrixActeSousTraitance"
]
    #On garde que les colonnes présentes dans le dataframe
    colonnes_presentes = [col for col in liste_col_ordonnes if col in df.columns]
    #Réorganisation des colonnes
    df = df.reindex(colonnes_presentes, axis=1)
    return df

def order_columns_concessions(df: pd.DataFrame):
    """
    La fonction ordonne les colonnes d'une concession
    du dataframe dans l'orde indiqué de la liste.
    """
    liste_col_ordonnes = [
    "concessionnaire_id_1",
    "concessionnaire_typeIdentifiant_1",
    "concessionnaire_id_2",
    "concessionnaire_typeIdentifiant_2",
    "concessionnaire_id_3",
    "concessionnaire_typeIdentifiant_3",
    "id",
    "nature",
    "objet",
    "procedure",
    "dureeMois",
    "datePublicationDonnees",
    "source",
    "considerationsSociales",
    "considerationsEnvironnementales",
    "dateSignature",
    "dateDebutExecution",
    "valeurGlobale",
    "montantSubventionPublique",
    "autoriteConcedante.id",
    "idModification",
    "dureeMoisModification",
    "valeurGlobaleModification",
    "dateSignatureModificationModification",
    "datePublicationDonneesModificationModification",
    "donneesExecution.datePublicationDonneesExecution",
    "donneesExecution.depensesInvestissement",
    "donneesExecution.intituleTarif",
    "donneesExecution.tarif",
    "backup__dureeMois"
    ]

    #On garde que les colonnes présentes dans le dataframe
    colonnes_presentes = [col for col in liste_col_ordonnes if col in df.columns]
    #Réorganisation
    df = df.reindex(colonnes_presentes, axis=1)
    return df

def stabilize_columns(df:pd.DataFrame,set:str,add_error_columnns:bool=False):
    """
    On ajoute des colonnes vides si celles-ci doivent exister et on supprimer les colonnes en trop
    """
    columns_reference = conf_glob["df_"+set]

    if add_error_columnns is True:
        columns_reference.insert(0, "Erreurs")
        if 'Erreurs' not in df.columns:
            df['Erreurs'] = pd.NA

    # Add column in df
    for column in columns_reference:
        if column not in df.columns:
            df[column] = pd.NA
    # Delete columns in df which are not in columns_reference
    for column in df.columns:
        if column not in columns_reference and not (add_error_columnns is True and column == 'Erreurs'):
            df.drop(columns=[column], inplace=True)
    return df[columns_reference]

@compute_execution_time
def regles_marche(df_marche_: pd.DataFrame,data_format:str) -> pd.DataFrame:
    
    #Cas spécial. Ces colonnes existent déjà dans le df et sont, par défaut, rempli avec le 1er élément de la liste
    suppression_colonnes =['dureeMoisActeSousTraitance', 'montantActeSousTraitance', 'variationPrixActeSousTraitance',\
                            'montantActeSousTraitance', 'idActeSousTraitance', 'dateNotificationActeSousTraitance',\
                            'datePublicationDonneesActeSousTraitance', 'typeIdentifiantSousTraitant','idSousTraitant']
    for column in suppression_colonnes:
        if column in df_marche_.columns:
            df_marche_.drop(columns=suppression_colonnes, inplace=True)

    # On initialise la table des marches exclus a l'identique de celle des marches
    df_marche_badlines_ = pd.DataFrame(columns=df_marche_.columns)
    
    @compute_execution_time
    def dedoublonnage_marche(df: pd.DataFrame, feature_doublons_marche) -> pd.DataFrame:
        
        """
        Sont considérés comme doublons des marchés ayant les mêmes valeurs aux champs suivants :
        id,
        idAcheteur,
        idTitulaire,
        dateNotification,
        Montant
        En clair cela signifie que c’est bel et bien le même contrat.
        - Si même (id, idAcheteur, idTitulaire, dateNotification, Montant), regarder datePublicationDonnees, qui correspond à la date d’arrivée de la donnée dans data.gouv. Conserver seulement l’enregistrement ayant la datePublicationDonnees la plus récente.
        - Si même datePublicationDonnees en plus de même jeu de variable, alors regarder le niveau de complétude de chaque enregistrement avec un score ( : compter le nombre de fois où les variables sont renseignées pour chaque enregistrement. Cela constitue un « score »). Prendre l’enregistrement ayant le score le plus élevé.
        - Si même (id, idAcheteur, idTitulaire, dateNotification, Montant, datePublicationDonnees ) et même score, alors garder la dernière ligne du groupe par défaut
        """

        def extract_values(row: list,data_format:str):
            """
            create 9 new columns with the values of the titulaires column

            template for new col name : titulaires_ + col name + _ + value
                - value is number from 1 to 3
                - col name are : typeIdentifiant, id, denominationSociale

            row contains a list of dict, each dict is a titulaires
                - can be empty
                - can contain 1, 2 or 3 titulaires or more keeping only 3 first
                - if 1 value can be a dict and not a list of dict

            :param row: the dataframe row to extract values from
            :return: a new dataframe with the values of the titulaires column, new value are nan if not present
            """
            new_columns = {}
            new_cols_names = ['denominationSociale', 'id', 'typeIdentifiant']
            if data_format=='2022':
                new_cols_names = ['id', 'typeIdentifiant']
                
            # create new columns all with nan value
            for value in range(1, 4):
                for col_name in new_cols_names:
                    new_col_name = f'titulaire_{col_name}_{value}'
                    new_columns[new_col_name] = np.nan

            if isinstance(row, list):
                row = row[:3]  # Keep only the first three concession
            else:
                # if row is not a list, then it is empty and for obscure reason script thinks it's a float so returning nan
                return pd.Series(new_columns)

            # fill new columns with values from concessionnaires column if exist
            for value, concession in enumerate(row, start=1):
                # replace value in new_columns by corresponding value in concession
                for col_name in new_cols_names:
                    col_to_fill = f'titulaire_{col_name}_{value}'
                    # col_name is key in concession dict, col_to_fill is key in new_columns dict. get key value in col_name and put it in col_to_fill
                    if concession:
                        new_columns[col_to_fill] = concession.get('titulaire').get(col_name, np.nan)

            return pd.Series(new_columns)


        df = df["titulaires"].apply(extract_values,data_format=data_format).join(df)

        if "titulaires" in df.columns:
            df.drop(columns=["titulaires"], inplace=True)

        logging.info("dedoublonnage_marche")
        logging.info("df_marché avant dédoublonnage : " + str(df.shape))
        # filtre pour mettre la date de publication la plus récente en premier
        df = df.sort_values(by=["datePublicationDonnees"], ascending=False)

        df["acheteur.id"] = df["acheteur.id"].astype(str)
        df["id"] = df["id"].astype(str)
        df["titulaire_id_1"] = df["titulaire_id_1"].astype(str)
        df["montant"] = df["montant"].astype(str)
        if data_format=='2022':
            df["dureeMois"] = df["dureeMois"].astype(str)
            
            df["marcheInnovant"] = df["marcheInnovant"].astype(str)
            df["attributionAvance"] = df["attributionAvance"].astype(str)
            df["sousTraitanceDeclaree"] = df["sousTraitanceDeclaree"].astype(str)
            # Fix FutureWarning df["offresRecues"] = df["offresRecues"].fillna(0).astype(int).astype(str)
            if 'offresRecues' in df.columns:
                with pd.option_context("future.no_silent_downcasting", True):
                    df["offresRecues"] = df["offresRecues"].fillna(0).infer_objects(copy=False) #.astype(int).astype(str)
                df["offresRecues"] = df["offresRecues"].astype(int).astype(str)
            if 'tauxAvance' in df.columns:
                df["tauxAvance"] = df["tauxAvance"].astype(str)
            if 'origineUE' in df.columns:
                df["origineUE"] = df["origineUE"].astype(str)
            if 'origineFrance' in df.columns:
                df["origineFrance"] = df["origineFrance"].astype(str)
            if ('origineUE' in df.columns) and ('origineFrance' in df.columns) :
                df.astype({"dureeMois": 'str', "origineUE": 'str', "origineFrance": 'str'}) 
            if 'idActeSousTraitance' in df.columns:
                df["idActeSousTraitance"] = pd.to_numeric(df["idActeSousTraitance"], downcast='signed')
            #if 'lieuExecution.code' in df.columns:
            #    df["lieuExecution.code"] = pd.to_numeric(df["lieuExecution.code"], downcast='signed')
            if 'dureeMoisActeSousTraitance' in df.columns:
                df["dureeMoisActeSousTraitance"] = pd.to_numeric(df["dureeMoisActeSousTraitance"], downcast='signed')
            if 'montantActeSousTraitance' in df.columns:
                df["montantActeSousTraitance"] = df["montantActeSousTraitance"].astype(str)
            if 'idModification' in df.columns:
                df["idModification"] = df["idModification"].astype(str)
            if 'montantModification' in df.columns:
                df["montantModification"] = df["montantModification"].astype(str)
            if 'dureeMoisModification' in df.columns:
                df["dureeMoisModification"] = pd.to_numeric(df["dureeMoisModification"], downcast='signed')
            if 'dureeMoisModificationActeSousTraitance' in df.columns:
                df["dureeMoisModificationActeSousTraitance"] = pd.to_numeric(df["dureeMoisModificationActeSousTraitance"], downcast='signed')
            if 'idModificationActeSousTraitance' in df.columns:
                df["idModificationActeSousTraitance"] = pd.to_numeric(df["idModificationActeSousTraitance"], downcast='signed')
            if 'idSousTraitant' in df.columns:
                df["idSousTraitant"] = df["idSousTraitant"].astype(str)
            if 'montantModificationActeSousTraitance' in df.columns:
                df["montantModificationActeSousTraitance"] = df["montantModificationActeSousTraitance"].astype(str)      

        # Only for reporting
        index_to_keep = df.drop_duplicates(subset=feature_doublons_marche).index.tolist()
        # Mémoriser la nombre de marchés avant et après dédoublonnage
        report.nb_in_good_marches = len(df)
        report.nb_duplicated_marches = len(df)-len(index_to_keep)
        # Ajouter au reporting les doublons supprimés
        report.add('Dédoublonnage marchés','E_DUPLICATE_MARCHE','Marchés en doublon',df[df.duplicated(feature_doublons_marche)])

        # suppression des doublons en gardant la première ligne donc datePublicationDonnees la plus récente
        dff = df.drop_duplicates(subset=feature_doublons_marche, keep="first")

        logging.info("df_marché après dédoublonnage : " + str(dff.shape))
        logging.info("% de doublons marché : "+ str((df.shape[0] - dff.shape[0]) / df.shape[0] * 100))
        return dff

    def marche_check_empty(df: pd.DataFrame, dfb: pd.DataFrame) -> pd.DataFrame:
        col_name = ["id", "acheteur.id", "montant", "titulaire_id_1", "titulaire_typeIdentifiant_1", "dureeMois"]  # titulaire contient un dict avec des valeurs dont id
        for col in col_name:
            mask_col_vide = df[col].isna() | (df[col] == '<NA>')
            df = df_add_error(df,mask_col_vide,f"Champ {col} non renseigné")
        return df

    def marche_replace_titulaire_type(df: pd.DataFrame) -> pd.DataFrame:
        bad_label = df["titulaire_typeIdentifiant_1"].str.match("FRW", na=True)
        df.loc[bad_label,'titulaire_typeIdentifiant_1'] = 'FRWF'
        bad_label = df["titulaire_typeIdentifiant_1"].str.match("HORS_UE", na=False)
        df.loc[bad_label,'titulaire_typeIdentifiant_1'] = 'HORS-UE'
        bad_label = df["titulaire_typeIdentifiant_1"].str.match("TVA-intracommunautaire", na=False)
        df.loc[bad_label,'titulaire_typeIdentifiant_1'] = 'TVA'
        return df

    def marche_check_type(df: pd.DataFrame, dfb: pd.DataFrame) -> pd.DataFrame:
        mask_bad_type = ~((df['titulaire_typeIdentifiant_1'].str[0:] == "SIRET") 
                | (df['titulaire_typeIdentifiant_1'].str[0:] == "TVA")
                | (df['titulaire_typeIdentifiant_1'].str[0:] == "TAHITI")
                | (df['titulaire_typeIdentifiant_1'].str[0:] == "RIDET")
                | (df['titulaire_typeIdentifiant_1'].str[0:] == "FRWF")
                | (df['titulaire_typeIdentifiant_1'].str[0:] == "IREP")
                | (df['titulaire_typeIdentifiant_1'].str[0:] == "HORS-UE")
                )
        df = df_add_error(df,mask_bad_type,f"Type erroné pour la colonne titulaire_typeIdentifiant_1")
        return df

    def marche_cpv_object(df: pd.DataFrame, dfb: pd.DataFrame) -> pd.DataFrame:
        # Si CPV manquant et objet du marché manquant ou < 5 caractères (V4), alors le marché est mis de côté
        # Fix FutureWarning df["objet"] = df["objet"].replace("\n", "\\n").replace("\r", "\\r")
        with pd.option_context("future.no_silent_downcasting", True):
            df["objet"] = df["objet"].replace("\n", "\\n").infer_objects(copy=False)
            df["objet"] = df["objet"].replace("\r", "\\r").infer_objects(copy=False)
        
        mask_bad_cpv = ( ~pd.notna(df["codeCPV"]) & ~pd.notna(df["objet"])) 
        df = df_add_error(df,mask_bad_cpv,f"Champs codeCPV et objet manquants")
        
        mask_bad_cpv = (df['codeCPV'].str.len() < 10) & ~pd.notna(df["objet"])
        df = df_add_error(df,mask_bad_cpv,f"Champ codeCPV renseigné mais objet manquants")
        
        mask_bad_cpv = (df['codeCPV'].str.len() < 10) & (df['objet'].str.len()<5)
        df = df_add_error(df,mask_bad_cpv,f"Champ codeCPV renseigné mais objet incomplet")
                                                        
        return df

    @compute_execution_time
    def marche_cpv(df: pd.DataFrame, cpv_2008_df: pd.DataFrame, data_format:str) -> pd.DataFrame:
        """
        Le CPV comprend 10 caractères (8 pour la racine + 1 pour le séparateur « - » et +1 pour la clé) – format texte pour ne pas supprimer les « 0 » en début de CPV.
        Un code CPV est INEXPLOITABLE s’il n’appartient pas à la liste des codes CPV existants dans la nomenclature européenne 2008 des CPV
        Les CPV fonctionnent en arborescence. Le CPV le plus générique est le premier de la liste d’une division. Il y a 45 divisions (03, 09, 14, 15, 16,18…).
        En lisant de gauche à droite, le code CPV le plus générique de la division comportera un « 0 » au niveau du 3ᵉ caractère.
        Ex pour la division 45 : CPV le plus générique : 45000000-7 (travaux de construction).
        Règles :
            - Si la clé du code CPV est manquante et que la racine du code CPV est correcte (8 premiers caractères) alors il convient de compléter avec la clé correspondante issue de la base CPV 2008.
            - Si la racine du code CPV est complète, mais qu’elle n’existe pas dans la base CPV 2008, alors il convient de prendre le code CPV le plus générique de son arborescence.
            - Si la racine du code CPV est correcte, mais que la clé est incorrecte, alors il convient de remplacer par la clé correspondante à la racine issue de la base CPV 2008.
            - Si la racine du code CPV est incomplète, mais qu’au moins les deux premiers caractères du code CPV (la division) sont renseignées correctement, alors il convient de compléter avec le code CPV le plus générique de la division
            - Si le code CPV n’est pas renseigné, mais qu’il y a un objet de marché, il convient de laisser la donnée initiale et de ne pas mettre de côté le marché.
        AUCUN RETRAITEMENT POSSIBLE :
            - Si la racine du code CPV est incomplète, qu’aucun objet de marché n’est présent et que les deux premiers caractères du code CPV sont erronés, alors aucun retraitement n’est possible et l’enregistrement est mis de côté (ex : 111111).
            - Si la racine du code CPV est complète, mais erronée, qu’aucun objet de marché n’est présent et que les deux premiers caractères du code CPV sont erronés, alors aucun retraitement n’est possible et l’enregistrement est mis de côté (ex : 11111111-1).
        L'ordre de vérification est important. 
        Parameters :
            df (pd.DataFrame): dataframe to clean
            cpv_2008_df: file cpv which is in the folder "data"
        Returns :
            df (pd.DataFrame): cleaned dataframe
        """
        def get_cpv_key(cpv_root):
            # check if CPV root exists in CPV 2008 database column "CODE" and only keep the first 8 characters
            cpv_mask = cpv_2008_df["CODE"].str[:8] == cpv_root
            cpv_key = cpv_2008_df.loc[cpv_mask, "CODE"].str[-1].values[0] if cpv_mask.any() else ""
            return cpv_key

        def get_cpv_key_with_dash(cpv_root):
            # check if CPV root exists in CPV 2008 database column "CODE" and only keep the first 8 characters
            cpv_mask = cpv_2008_df["CODE"].str[:8] == cpv_root
            cpv_key = '-'+cpv_2008_df.loc[cpv_mask, "CODE"].str[-1].values[0] if cpv_mask.any() else ""
            return cpv_key

        def get_completed_key(cpv_root):
            return '0'+cpv_root

        #Dans le datafram cpv, on crée la colonne "CPV Root", contenant que les racines du code CPV
        cpv_2008_df["CPV Root"] = cpv_2008_df["CODE"].str[:8]

        # Check if CPV is empty string
        not_empty_cpv_mask = df['codeCPV'] != ''
        df.loc[not_empty_cpv_mask,'CPVCopy'] = df.loc[not_empty_cpv_mask,'codeCPV']

        # Fix ECO: complete with zero if size is 7
        # First: zero in 1st position without  the key 
        complete_root_mask = df['codeCPV'].str.len() == 7
        cpv_roots = '0'+df.loc[complete_root_mask, 'codeCPV'].str[:7]
        non_existing_roots_mask = ~cpv_roots.isin(cpv_2008_df["CPV Root"].values)
        cpv_roots.loc[non_existing_roots_mask] = cpv_roots.loc[non_existing_roots_mask].str[1:8]
        cpv_keys = cpv_roots.str[:8].apply(get_cpv_key_with_dash)
        df.loc[complete_root_mask, 'codeCPV'] = cpv_roots + cpv_keys

        # Secondly: zero in last position  without  the key 
        complete_root_mask = df['codeCPV'].str.len() == 7
        cpv_roots = df.loc[complete_root_mask, 'codeCPV'].str[:7]+'0'
        non_existing_roots_mask = ~cpv_roots.isin(cpv_2008_df["CPV Root"].values)
        cpv_roots.loc[non_existing_roots_mask] = cpv_roots.loc[non_existing_roots_mask].str[0:7]
        cpv_keys = cpv_roots.str[:8].apply(get_cpv_key_with_dash)
        df.loc[complete_root_mask, 'codeCPV'] = cpv_roots + cpv_keys

        #Pattern and mask for the next check 
        format_regex = r'^\d{7}-\d{1}$'
        complete_root_mask = df["codeCPV"].str.match(format_regex, na=False)
        
        # First: zero in 1st position with  the key 
        cpv_roots = '0'+df.loc[complete_root_mask, 'codeCPV'].str[:9]
        non_existing_roots_mask = ~cpv_roots.isin(cpv_2008_df["CODE"].values)
        cpv_roots.loc[non_existing_roots_mask] = cpv_roots.loc[non_existing_roots_mask].str[1:10]
        df.loc[complete_root_mask, 'codeCPV'] = cpv_roots

        # Secondly: zero in last position  with  the key 
        cpv_roots = df.loc[complete_root_mask, 'codeCPV'].str[:7]+'0-'+  df.loc[complete_root_mask, 'codeCPV'].str[8]
        non_existing_roots_mask = ~cpv_roots.isin(cpv_2008_df["CODE"].values)
        cpv_roots.loc[non_existing_roots_mask] = cpv_roots.loc[non_existing_roots_mask].str[0:7]+'-'+cpv_roots.loc[non_existing_roots_mask].str[9]
        df.loc[complete_root_mask, 'codeCPV'] = cpv_roots
        

        # For "full" CPV code check if exists, if not use the 2 first number
        full_root = df['codeCPV'].str.len() == 10
        cpv_roots = df.loc[full_root, 'codeCPV'].str[:10]
        # Search for not existing record
        non_existing_roots_mask = ~cpv_roots.isin(cpv_2008_df["CODE"].values)
        cpv_roots.loc[non_existing_roots_mask] = cpv_roots.loc[non_existing_roots_mask].str[:8]
        df.loc[full_root, 'codeCPV'] = cpv_roots

        # Check if CPV root is complete
        complete_root_mask = df['codeCPV'].str.len() == 8
        cpv_roots = df.loc[complete_root_mask, 'codeCPV'].str[:8]
        non_existing_roots_mask = ~cpv_roots.isin(cpv_2008_df["CPV Root"].values)
        cpv_roots.loc[non_existing_roots_mask] = cpv_roots.loc[non_existing_roots_mask].str[:2] + '000000'
        cpv_keys = cpv_roots.str[:8].apply(get_cpv_key)
        df.loc[complete_root_mask, 'codeCPV'] = cpv_roots + '-' + cpv_keys
        
        if data_format=='2022':
            format_regex = r'^\d{8}-\d{1}$'
            complete_root_mask = ~df["codeCPV"].str.match(format_regex, na=False)
            cpv_roots = df.loc[complete_root_mask, 'codeCPV'].str[:2]+'000000'
            cpv_keys = cpv_roots.str[:8].apply(get_cpv_key_with_dash)
            df.loc[complete_root_mask, 'codeCPV'] = cpv_roots + cpv_keys

        format_regex = r'^\d{8}-\d{1}$'
        erroned_root_mask = ~df["codeCPV"].str.match(format_regex, na=False)
        if data_format=='2019':
            erroned_root_mask = df['codeCPV'].str.len() == 9
        df.loc[erroned_root_mask, 'codeCPV'] = 'INX '+df.loc[erroned_root_mask, 'CPVCopy']
        
        # Check if CPV key is missing only if CPV root is complete
        #missing_key_mask = (df['codeCPV'].str.len() >= 8) & (df['codeCPV'].str[9:].isin(['', None]))
        #df.loc[missing_key_mask, 'CPV'] = (
        #    df.loc[missing_key_mask, 'codeCPV'].str[:8].apply(get_cpv_key)
        #)
        del df['CPVCopy']
        #del df['CPV']

        return df

    def marche_date(df: pd.DataFrame, dfb: pd.DataFrame) -> pd.DataFrame:
        # Si la date de notification et la date de publication est manquante, alors le marché est mis de côté

        mask_empty_date =  ~pd.notna(df["dateNotification"]) & ~pd.notna(df["datePublicationDonnees"])
        df = df_add_error(df,mask_empty_date,"Champs dateNotification et datePublicationDonnees manquants")

        return df

    def marche_date_valid(df: pd.DataFrame, dfb: pd.DataFrame,data_format:str,col:str) -> pd.DataFrame:
        """
        Format AAAA-MM-JJ
            Si MM<01 ou>12,
            SI JJ<01 ou >31 (voir si possibilité de vérifier le format jour max en fonction du mois et année)
        La date de notification est INEXPLOITABLE si elle ne respecte pas le format, ou si elle ne peut pas être retransformée au format initial (ex : JJ-MM-AAAA)
        Correction si INEXPLOITABLE :3abb5676-c994-4e70-9713-0f5faf7c8e4c
            Si la date de notification du marché est manquante et qu’il existe une date de publication des données essentielles du marché public
            respectant le format AAAA-MM-JJ (ou pouvant être retransformé en ce format) alors il convient d’affecter la date de publication à la date de notification.
        """

        # vérification du format de la date de notification (AAAA-MM-JJ) et correction si besoin création d'un dataframe avec les lignes à corriger
        format_regex = r'^20\d{2}-\d{2}-\d{2}$'
        invalid_dates = df[~df[col].str.match(format_regex, na=False)]
        if col== "dateNotification":
            invalid_dates["dateNotification"] = invalid_dates["datePublicationDonnees"]
            mask_bad_col = ~df[col].str.match(format_regex, na=False) & ~df["datePublicationDonnees"].str.match(format_regex, na=False)
        else:
            mask_bad_col = ~df[col].str.match(format_regex, na=False)

        if data_format=='2019':
            current_year = str(datetime.now().year)
            invalid_dates = df[(df["dateNotification"].str[0:4] > current_year)]
            df = df[df["dateNotification"].str[0:4] <= current_year]
            invalid_dates["dateNotification"] = invalid_dates["datePublicationDonnees"]
            still_invalid_dates = invalid_dates[invalid_dates["dateNotification"].str[0:4] > current_year]
            no_more_invalide_dates = invalid_dates[invalid_dates["dateNotification"].str[0:4] <= current_year]
            df = pd.concat([df, no_more_invalide_dates])
            dfb = pd.concat([dfb, still_invalid_dates])
        else:
            df = df_add_error(df,mask_bad_col,f"Champ {col} erroné")

        return df
    
    feature_doublons_marche = ["id", "acheteur.id", "titulaire_id_1", "montant", "dateNotification"] 

    df_marche_ = dedoublonnage_marche(df_marche_,feature_doublons_marche)

    augmente.utils.save_csv(df_marche_, "df_marche_dedoublonnage.csv")

    df_marche_ = marche_replace_titulaire_type(df_marche_)

    df_marche_["Erreurs"] = pd.NA
    df_marche_badlines_["Erreurs"] = pd.NA
    
    df_marche_ = marche_check_empty(df_marche_, df_marche_badlines_)
    df_marche_ = marche_check_type(df_marche_, df_marche_badlines_)
    df_marche_ = marche_cpv_object(df_marche_, df_marche_badlines_)
    df_marche_ = marche_date(df_marche_, df_marche_badlines_)

    df_marche_ = check_montant(df_marche_, df_marche_badlines_, "montant",3000000000)
    df_marche_ = check_siret(df_marche_, df_marche_badlines_, "acheteur.id")
    
    df_marche_ = check_siret_ext(df_marche_, df_marche_badlines_, "titulaire",'SIRET')
    df_marche_ = check_siret_ext(df_marche_, df_marche_badlines_, "titulaire",'TVA')
    df_marche_ = check_siret_ext(df_marche_, df_marche_badlines_, "titulaire",'TAHITI')
    df_marche_ = check_siret_ext(df_marche_, df_marche_badlines_, "titulaire",'RIDET')
    df_marche_ = check_siret_ext(df_marche_, df_marche_badlines_, "titulaire",'FRWF')
    df_marche_ = check_siret_ext(df_marche_, df_marche_badlines_, "titulaire",'IREP')
    df_marche_ = check_siret_ext(df_marche_, df_marche_badlines_, "titulaire",'HORS-UE')

    df_cpv = pd.read_excel("data/cpv_2008_fr.xls", engine="xlrd")  #engine=openpyxl   xlrd

    df_marche_ = marche_cpv(df_marche_, df_cpv, data_format)

    #Champs ayant des listes
    df_marche_ = keep_more_recent(df_marche_,"modifications","Modification")
    df_marche_ = keep_more_recent(df_marche_,"modificationsActesSousTraitance","ModificationActeSousTraitance")
    df_marche_ = keep_more_recent(df_marche_,"actesSousTraitance","ActeSousTraitance")

    replace_nc_colonne(df_marche_,'variationPrixActeSousTraitance')
    replace_nc_colonne(df_marche_,'dureeMoisActeSousTraitance',True)

    # delete df_cpv to free memory
    del df_cpv

    df_marche_ = check_duree_contrat(df_marche_, df_marche_badlines_, 180)
    df_marche_ = marche_date_valid(df_marche_, df_marche_badlines_, data_format, "dateNotification")
    df_marche_ = marche_date_valid(df_marche_, df_marche_badlines_, data_format, "datePublicationDonnees")

    df_marche_ = check_id_format(df_marche_, df_marche_badlines_)

    df_marche_badlines_ = df_marche_[df_marche_['Erreurs'].notna()] # get all line with Erreurs = ~isna()
    df_marche_ = df_marche_[~df_marche_['Erreurs'].notna()] # df_marche_ - df_marche_badlines_

    df_marche_badlines_ = reorder_columns(df_marche_badlines_)
    df_marche_ = order_columns_marches(df_marche_)
    
    return df_marche_, df_marche_badlines_


@compute_execution_time
def regles_concession(df_concession_: pd.DataFrame,data_format:str) -> pd.DataFrame:

    @compute_execution_time
    def dedoublonnage_concession(df: pd.DataFrame, feature_doublons_concession:list) -> pd.DataFrame:
        """
        Sont considérés comme doublons des concessions ayant les mêmes valeurs aux champs suivants :
        id,
        idautoriteConcedante,
        idconcessionnaires,
        dateDebutExecution,
        valeurGlobale.
        En clair cela signifie que c’est bel et bien le même contrat.
        - Si même (id, idautoriteConcedante, idconcessionnaires, dateDebutExecution, valeurGlobale), regarder datePublicationDonnees, qui correspond à la date d’arrivée de la donnée dans data.gouv. Garder datePublicationDonnees la plus récente.
        - Si même datePublicationDonnees en plus de même jeu de variable, alors regarder le niveau de complétude de chaque enregistrement avec un score ( : compter le nombre de fois où les variables sont renseignées pour chaque enregistrement. Cela constitue un « score »). Prendre l’enregistrement ayant le score le plus élevé.
        - Si même (id, idautoriteConcedante, idconcessionnaires, dateDebutExecution, valeurGlobale, datePublicationDonnees) et même score, alors garder la dernière ligne du groupe.
        """

        def extract_values(row: list,data_format:str):
            """
            create 9 new columns with the values of the concessionnaires column

            template for new col name : concessionnaire_ + col name + _ + value
                - value is number from 1 to 3
                - col name are : denominationSociale, id, typeIdentifiant

            row contains a list of dict, each dict is a concessionnaire
                - can be empty
                - can contain 1, 2 or 3 concessionnaires or more keeping only 3 first
                - if 1 value can be a dict and not a list of dict

            :param row: the dataframe row to extract values from
            :return: a new dataframe with the values of the concessionnaires column, new value are nan if not present
            """
            new_columns = {}
            new_cols_names = ['denominationSociale', 'id', 'typeIdentifiant']
            if data_format=='2022':
                new_cols_names = ['id', 'typeIdentifiant']

            # create new columns all with nan value
            for value in range(1, 4):
                for col_name in new_cols_names:
                    new_col_name = f'concessionnaire_{col_name}_{value}'
                    new_columns[new_col_name] = pd.NA

            if isinstance(row, list):
                # how is the list of concessionnaires
                # if contain a dict where key is exactly : concessionnaire, then the list we want is the value of this dict key
                if 'concessionnaire' in row[0].keys():
                    row = [item['concessionnaire'] for item in row]
                row = row[:3]  # Keep only the first three concession
            else:
                # if row is not a list, then it is empty and for obscure reason script thinks it's a float so returning nan
                return pd.Series(new_columns)

            # le traitement ici à lieux car comme on dit : "Garbage in, garbage out" mais on est gentil on corrige leurs formats -_-
            # check if row is a list of list of dict, if so, keep only the first list
            if isinstance(row[0], list):
                row = row[0]

            # fill new columns with values from concessionnaires column if exist
            for value, concession in enumerate(row, start=1):
                # replace value in new_columns by corresponding value in concession
                for col_name in new_cols_names:
                    col_to_fill = f'concessionnaire_{col_name}_{value}'
                    # col_name is key in concession dict, col_to_fill is key in new_columns dict. get key value in col_name and put it in col_to_fill
                    if concession:
                        new_columns[col_to_fill] = concession.get(col_name, np.nan)

            return pd.Series(new_columns)

        def extract_values_donnees_execution(row: list):
            """
            select the element the most recent in the donneesExecution column
            """
            if row is None:
                return row
            dico_le_plus_recent = {}
            for element in (row):
                #Dictionnaire avec plusieurs clés et valeurse
                if isinstance(element,dict):
                    date1 = dico_le_plus_recent.get("datePublicationDonneesExecution", None)
                    date2 = element.get("datePublicationDonneesExecution", None)

                    #Comparaison de date pour sélectionner le dictionnaire le plus récent
                    if date1 is None or (date1 < date2):
                        dico_le_plus_recent = element

            datePublication = dico_le_plus_recent.get("datePublicationDonneesExecution", None)
            depensesInvestissement = dico_le_plus_recent.get("depensesInvestissement", None)

            # Gestion du champ "tarifs" pour obtenir le dernier tarif et son intitulé
            derniers_tarifs = dico_le_plus_recent.get("tarifs", [])
            if derniers_tarifs: 
                dernier_tarif_info = derniers_tarifs[-1].get("tarif", {})
                intituleTarif = dernier_tarif_info.get("intituleTarif", None)
                tarif = dernier_tarif_info.get("tarif", None)
            else:
                intituleTarif = None
                tarif = None
                
            return datePublication, depensesInvestissement, intituleTarif, tarif

        #if data_format=='2022':
        #    df = df["donneesExecution"].apply(extract_values_donnees_execution).join(df)
        #    df.drop(columns=["donneesExecution"], inplace=True)

        if data_format=='2022' and "concessionnaires.concessionnaire" in df.columns:
            df["concessionnaires"] = df["concessionnaires.concessionnaire"]

        df = df["concessionnaires"].apply(extract_values,data_format=data_format).join(df)
        df.drop(columns=["concessionnaires"], inplace=True)

        #Donnees execution
        #if "donneesExecution" in df.columns:
        #    df[["donneesExecution.datePublicationDonneesExecution", "donneesExecution.depensesInvestissement", \
        #        "donneesExecution.intituleTarif", "donneesExecution.tarif"]] = df["donneesExecution"].apply(extract_values_donnees_execution).apply(pd.Series)

        logging.info("dedoublonnage_concession")
        logging.info("df_concession_ avant dédoublonnage : " + str(df.shape))
        # filtre pour mettre la date de publication la plus récente en premier
        df = df.sort_values(by=["datePublicationDonnees"], ascending=[False])

        # Only for reporting
        index_to_keep = df.drop_duplicates(subset=feature_doublons_concession).index.tolist()
        # Mémoriser la nombre de concessions avant et après dédoublonnage
        report.nb_in_good_concessions = len(df)
        report.nb_duplicated_concessions = len(df) - len(index_to_keep)
        # Ajouter au reporting les doublons supprimés
        report.add('Dédoublonnage concessions','E_DUPLICATE_CONCESSION','Concessions en doublon',df[df.duplicated(feature_doublons_concession)])

        # suppression des doublons en gardant la première ligne donc datePublicationDonnees la plus récente
        dff = df.drop_duplicates(subset=feature_doublons_concession,
                                                            keep="first")
        logging.info("df_concession_ après dédoublonnage : " + str(df.shape))
        logging.info("% doublon concession : "+ str((df.shape[0] - dff.shape[0]) / df.shape[0] * 100))
        return dff

    df_concession_badlines_ = pd.DataFrame(columns=df_concession_.columns)

    def concession_replace_concessionnaire_type(df: pd.DataFrame) -> pd.DataFrame:
        bad_label = df["concessionnaire_typeIdentifiant_1"].str.match("FRW", na=False)
        df.loc[bad_label,'concessionnaire_typeIdentifiant_1'] = 'FRWF'
        bad_label = df["concessionnaire_typeIdentifiant_1"].str.match("HORS_UE", na=False)
        df.loc[bad_label,'concessionnaire_typeIdentifiant_1'] = 'HORS-UE'
        bad_label = df["concessionnaire_typeIdentifiant_1"].str.match("TVA-intracommunautaire", na=False)
        df.loc[bad_label,'concessionnaire_typeIdentifiant_1'] = 'TVA'
        return df

    def concession_check_type(df: pd.DataFrame, dfb: pd.DataFrame) -> pd.DataFrame:
        mask_bad_col = ~((df['concessionnaire_typeIdentifiant_1'].str[0:] == "SIRET") 
                | (df['concessionnaire_typeIdentifiant_1'].str[0:] == "TVA")
                | (df['concessionnaire_typeIdentifiant_1'].str[0:] == "TAHITI")
                | (df['concessionnaire_typeIdentifiant_1'].str[0:] == "RIDET")
                | (df['concessionnaire_typeIdentifiant_1'].str[0:] == "FRWF")
                | (df['concessionnaire_typeIdentifiant_1'].str[0:] == "IREP")
                | (df['concessionnaire_typeIdentifiant_1'].str[0:] == "HORS-UE")
                )
        df = df_add_error(df,mask_bad_col,f"Champ concessionnaire_typeIdentifiant_1 erroné")
        return df

    def concession_check_empty(df_con: pd.DataFrame, df_bad: pd.DataFrame) -> pd.DataFrame:
        col_name = ["id", "autoriteConcedante.id", "concessionnaire_id_1", "objet", "valeurGlobale",
                    "dureeMois"]
        for col in col_name:
            mask_bad_col = ~pd.notna(df_con[col])
            df_con = df_add_error(df_con,mask_bad_col,f"Champ {col} non renseigné")
        return df_con

    def concession_date(df_con: pd.DataFrame, df_bad: pd.DataFrame) -> pd.DataFrame:
        # Si la date de début d’exécution et la date de publication est manquante alors le contrat de concession est mis de côté

        mask_bad_col =  ~pd.notna(df_con["dateDebutExecution"]) | ~pd.notna(df_con["datePublicationDonnees"])
        df_con = df_add_error(df_con,mask_bad_col,f"Champs dateDebutExecution et datePublicationDonnees manquants")
        
        return df_con

    def concession_date_2022(df_con: pd.DataFrame, df_bad: pd.DataFrame) -> pd.DataFrame:
        # Si la date de début d’exécution et la date de publication est manquante alors le contrat de concession est mis de côté

        mask_bad_col = ~pd.notna(df_con["dateDebutExecution"]) & ~pd.notna(df_con["datePublicationDonnees"])
        df_con = df_add_error(df_con,mask_bad_col,f"Champs dateDebutExecution et datePublicationDonnees manquants")

        return df_con

    def concession_dateDebutExecution(df: pd.DataFrame, dfb: pd.DataFrame) -> pd.DataFrame:
        # vérification du format de la date de début d'execution (AAAA-MM-JJ) et correction si besoin création d'un dataframe avec les lignes à corriger
        format_regex = r'^20\d{2}-\d{2}-\d{2}$'

        mask_bad_col = ~df["dateDebutExecution"].str.match(format_regex, na=False)
        df_con = df_add_error(df_con,mask_bad_col,f"Champ dateDebutExecution erroné")

        return df

    def concession_dateDebutExecution_2022(df: pd.DataFrame, dfb: pd.DataFrame) -> pd.DataFrame:
        # vérification du format de la date de début d'execution (AAAA-MM-JJ) et correction si besoin création d'un dataframe avec les lignes à corriger
        format_regex = r'^20\d{2}-\d{2}-\d{2}$'
        
        mask_bad_col = ~df["dateDebutExecution"].str.match(format_regex, na=False) & ~df["datePublicationDonnees"].str.match(format_regex, na=False)
        df = df_add_error(df,mask_bad_col,f"Champ dateDebutExecution erroné")

        return df#

    def concession_dateDebutExecutionOld(df: pd.DataFrame) -> pd.DataFrame:
        """
        Format AAAA-MM-JJ
            Si MM<01 ou>12,
            SI JJ<01 ou >31 (voir si possibilité de vérifier le format jour max en fonction du mois et année)
        Si la date de début d’exécution du contrat de concession est manquante et qu’il existe une date de publication des données d’exécution, respectant le format AAAA-MM-JJ (ou pouvant être retransformé en ce format) alors il convient d’affecter la date de publication à la date de début d’exécution.
        """

        # vérification du format de la date de notification (AAAA-MM-JJ) et correction si besoin création d'un dataframe avec les lignes à corriger
        df["dateDebutExecution"] = pd.to_datetime(df["dateDebutExecution"], format='%Y-%m-%d', errors='ignore')
        df["datePublication"] = pd.to_datetime(df["datePublication"], format='%Y-%m-%d', errors='ignore')

        # si la date de début d'exécution n'est pas au format AAAA-MM-JJ regarder la date de publication et si elle est au format AAAA-MM-JJ alors mettre la date de publication dans la date de début d'exécution
        df.loc[(df["dateDebutExecution"].isnull()) & (df["datePublication"].notnull()), "dateDebutExecution"] = df["datePublication"]

        return df

    feature_doublons_concession = ["id", "autoriteConcedante.id", "dateDebutExecution", "concessionnaire_id_1","valeurGlobale"]

    df_concession_ = dedoublonnage_concession(df_concession_,feature_doublons_concession)
    augmente.utils.save_csv(df_concession_, "df_concession_dedoublonnage.csv")

    df_concession_ = concession_replace_concessionnaire_type(df_concession_)
    
    df_concession_badlines_ = pd.DataFrame(columns=df_concession_.columns)
    df_concession_badlines_['Erreurs'] = pd.NA
    df_concession_['Erreurs'] = pd.NA
    
    df_concession_ = concession_check_empty(df_concession_, df_concession_badlines_)
    df_concession_ = concession_check_type(df_concession_, df_concession_badlines_)
    if data_format=='2019':
        df_concession_ = concession_date(df_concession_, df_concession_badlines_)
        df_concession_ = concession_dateDebutExecution(df_concession_, df_concession_badlines_)
    else:
        df_concession_ = concession_date_2022(df_concession_, df_concession_badlines_)
        df_concession_ = concession_dateDebutExecution_2022(df_concession_, df_concession_badlines_)

    df_concession_ = check_montant(df_concession_, df_concession_badlines_, "valeurGlobale")
    df_concession_ = check_siret(df_concession_, df_concession_badlines_, "autoriteConcedante.id")
    if data_format=='2019':
        df_concession_ = check_siret(df_concession_, df_concession_badlines_, "concessionnaire_id_1")
    else:
        df_concession_ = check_siret_ext(df_concession_, df_concession_badlines_, "concessionnaire","SIRET")
        df_concession_ = check_siret_ext(df_concession_, df_concession_badlines_, "concessionnaire","TVA")
        df_concession_ = check_siret_ext(df_concession_, df_concession_badlines_, "concessionnaire","TAHITI")
        df_concession_ = check_siret_ext(df_concession_, df_concession_badlines_, "concessionnaire","RIDET")
        df_concession_ = check_siret_ext(df_concession_, df_concession_badlines_, "concessionnaire","FRWF")
        df_concession_ = check_siret_ext(df_concession_, df_concession_badlines_, "concessionnaire","IREP")
        df_concession_ = check_siret_ext(df_concession_, df_concession_badlines_, "concessionnaire","HORS-UE")
        df_concession_ = check_id_format(df_concession_, df_concession_badlines_)

    df_concession_ = check_duree_contrat(df_concession_, df_concession_badlines_, 360)

    df_concession_badlines_ = df_concession_[df_concession_['Erreurs'].notna()] # get all line with Erreurs = ~isna()
    df_concession_ = df_concession_[~df_concession_['Erreurs'].notna()] # df_concession_ - df_concession__badlines_

    df_concession_badlines_ = reorder_columns(df_concession_badlines_)
    df_concession_ = order_columns_concessions(df_concession_)
    
    if 'Erreurs' in df_concession_.columns:
        del df_concession_['Erreurs']

    return df_concession_, df_concession_badlines_

def keep_more_recent(df:pd.DataFrame,field_name:str,suffix:str)-> pd.DataFrame:
    """
    Cette fonction gère les champs qui ont une liste de dictionnaire. 
    """

    #Sélectionner le dictionnaire ayant l'id le plus élevé
    def comparer_dico(dico_un: dict, dico_deux:dict)->dict:
        if dico_un is None:
            return dico_deux
        elif dico_deux is None:
            return dico_un

        date_une = dico_un.get("datePublicationDonnees", None) or dico_un.get("datePublicationDonneesModification", None)
        date_deux = dico_deux.get("datePublicationDonnees", None) or dico_deux.get("datePublicationDonneesModification", None)

        if date_une is None or (date_une <= date_deux):
            return dico_deux
        if date_deux is None or(date_une > date_deux):
            return dico_un
        
    #Sélectionner le dictionnaire ayant la date la plus récente
    
    if field_name in df.columns:
        listes_non_vides = df[df[field_name].apply(lambda x: isinstance(x, list) and len(x) > 0)]
        listes_vides = df[~df[field_name].apply(lambda x: isinstance(x, list) and len(x) > 0)]        
        
        if not 'id'+suffix in listes_non_vides:
            listes_non_vides['id'+suffix] = ""
        else:
            listes_non_vides['id'+suffix] = listes_non_vides['id'+suffix].astype(int,errors='ignore').astype(str)

        if not 'dureeMois'+suffix in listes_non_vides:
            listes_non_vides['dureeMois'+suffix] = ""
        else:
            listes_non_vides['dureeMois'+suffix] = listes_non_vides['dureeMois'+suffix].astype(int,errors='ignore').astype(str)

        if not 'datePublicationDonnees'+suffix in listes_non_vides:
            listes_non_vides['datePublicationDonnees'+suffix] = ""
        else:
            listes_non_vides['datePublicationDonnees'+suffix].astype(str)

        #if not 'dureeMoisModificationActeSousTraitance' in listes_non_vides:
        #    listes_non_vides['idModificationActeSousTraitance'] = ""
        #else:
        #    listes_non_vides['idModificationActeSousTraitance'].astype(str)
            
        #Parcourir chaque ligne du dataframe
        for index, ligne in listes_non_vides.iterrows():
            dico_plus_recent = {}
            #Parcourir chaque liste 
            for element in ligne[field_name]:
                #Dictionnaire avec une seule clé dont la valeur est un dictionnaire
                if isinstance(element,dict) and len(element.keys())==1:
                    cle = list(element.keys())[0]
                    dico_deux = element[cle]
                    dico_plus_recent = comparer_dico(dico_plus_recent,dico_deux)
                #Dictionaire avec plusieurs clés et valeurs
                elif isinstance(element,dict):
                    dico_plus_recent = comparer_dico(dico_plus_recent,element)
            # Mettre à jour le DataFrame avec le dictionnaire le plus récent
            listes_non_vides.at[index, field_name] = [dico_plus_recent] if dico_plus_recent else []
            listes_non_vides = complete_columns_from_list(listes_non_vides,field_name,index,dico_plus_recent)
        df = pd.concat([listes_non_vides, listes_vides], ignore_index=True)
    return df

def complete_columns_from_list(df:pd.DataFrame,field_name:str, ligne:int, dico: dict) -> pd.DataFrame:
    if field_name=='actesSousTraitance':
        df.loc[ligne, 'idActeSousTraitance'] = dico.get('id', None)
        df.loc[ligne, 'dureeMoisActeSousTraitance'] = dico.get('dureeMois', None)
        df.loc[ligne, 'dateNotificationActeSousTraitance'] = dico.get('dateNotification', None)
        df.loc[ligne, 'montantActeSousTraitance'] = dico.get('montant', None)
        df.loc[ligne, 'variationPrixActeSousTraitance'] = dico.get('variationPrix', None)
        df.loc[ligne, 'datePublicationDonneesActeSousTraitance'] = dico.get('datePublicationDonnees', None)
        df.loc[ligne, 'idSousTraitant'] = dico.get('sousTraitant', {}).get('id', None)
        df.loc[ligne, 'typeIdentifiantSousTraitant'] = dico.get('sousTraitant', {}).get('typeIdentifiant', None)

    if field_name=='modifications':
        df.loc[ligne, 'idModification'] = dico.get('id', None)
        df.loc[ligne, 'dureeMoisModification'] = dico.get('dureeMoisActeSousTraitance', None)
        df.loc[ligne, 'montantModification'] = dico.get('montant', None) 
        df.loc[ligne, 'idTitulaireModification'] = dico.get('titulaires', [{}])[0].get('id', None) 
        df.loc[ligne, 'typeIdentifiantTitulaireModification'] = dico.get('titulaires', [{}])[0].get('typeIdentifiant', None)
        df.loc[ligne, 'dateNotificationModificationModification'] = dico.get('dateNotificationModification', None)
        df.loc[ligne, 'datePublicationDonneesModificationModification'] = dico.get('datePublicationDonneesModification', None)

    if field_name=='modificationsActesSousTraitance':
        df.loc[ligne, 'idModificationActeSousTraitance'] = dico.get('id', None)
        df.loc[ligne, 'dureeMoisModificationActeSousTraitance'] = dico.get('dureeMois', None)
        df.loc[ligne, 'dateNotificationModificationSousTraitanceModificationActeSousTraitance'] = dico.get('dateNotificationModificationSousTraitance', None)
        df.loc[ligne, 'montantModificationActeSousTraitance'] = dico.get('montant', None)
        df.loc[ligne, 'datePublicationDonneesModificationActeSousTraitance'] = dico.get('datePublicationDonnees', None)
    return df

def check_montant(df: pd.DataFrame, dfb: pd.DataFrame, col: str, montant : int = 15000000000) -> pd.DataFrame:
    """
    La valeur est jugée INEXPLOITABLE
    si :
    -1 La valeur est supérieure à 3 000 000 000€ (Remarque : voir si règles des exceptions à transmettre plus tard).
    -2 Le montant est inférieur à 1€
    -3 Pour un seuil de 100 000 000, il y a
        -1 une succession de mêmes chiffres (ex: 999999999, 888888888, 99999988) les 0 ne sont pas considérés comme des chiffres identiques
        -2 la séquence du montant commençant par 123456789
        Méthodologie ci-dessous :
            Méthode de détection automatique des inexploitables par succession de mêmes chiffres (il convient initialement de passer en caractère le nombre pour le traiter comme une chaîne de caractère pour l’algorithme) :
                (Nombre de répétition du caractère le plus fréquent dans la chaîne de caractère > Nombre de caractères de la chaîne -2)
                & (Caractère le plus fréquent différent de « 0 »)
                & (Les positions du caractère le plus fréquent dans la chaîne de caractère se suivent sans interruption, càd constituent une suite croissante) alors INEXPLOITABLE
            Exemple applicatif : montant de 99999988€. Le « 9 » est l’occurrence la plus fréquente, la chaine de caractère est égale à 8 est donc 8-2 =6. La chaîne de caractère ne contient pas de 0.
            Répétition du « 9 » sans interruption (pas de « 8 » entre deux séries de « 9 »).
            Conclusion : INEXPLOITABLE

    Si  INEXPLOITABLE, le contrat est mis de côté.
    """
    # replace string '' by 0
    # Fix FutureWarning df[col] = df[col].replace('', 0)
    with pd.option_context("future.no_silent_downcasting", True):
        df[col] = df[col].replace('', 0).infer_objects(copy=False)
    # change col to float
    df[col] = df[col].astype(float)

    # 1

    mask_high_montant = df[col] > montant
    df = df_add_error(df,mask_high_montant,f"Valeur du champ {col} trop élevée")

    # 2
    #Fix FutureWarning dfb = pd.concat([dfb, df[df[col] < 1]])

    mask_low_montant = df[col] < 1
    df = df_add_error(df,mask_low_montant,f"Valeur du champ {col} inférieur à 1")

    # 3.1
    # si le même chiffre autre que 0 est répété plus de 6 fois pour les montants supérieur à 100 000 000 alors INEXPLOITABLE
    same_digit_count = df[col].astype(str).apply(lambda x: max(x.count('1'),x.count('2'),x.count('3'),x.count('4'),x.count('5'),x.count('7'),x.count('8'),x.count('9')))

    mask_bad_montant = (same_digit_count > 6) & (df[col].astype(str).str[0] != "0") & (df[col] > 100000000)
    df = df_add_error(df,mask_bad_montant,f"Champ {col} probablement erroné")

    # 3.2
    # si le montant commence par 123456789 alors INEXPLOITABLE

    mask_bad_montant = (df[col].astype(str).str[0:9] == "123456789")
    df = df_add_error(df,mask_bad_montant,f"Champ {col} probablement erroné")

    #dfb[col] = dfb[col].astype(float)

    return df


def check_siret(df: pd.DataFrame, dfb: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Le SIRET comprend 14 caractères (9 pour le SIREN + 5 pour le NIC) – format texte pour ne pas supprimer les « 0 » en début de Siret.
    L’identifiant autorité concédante est INEXPLOITABLE s’il ne respecte pas le format.
    Si INEXPLOITABLE, le contrat est mis de côté.
    """

    mask_bad_siret = ~df[col].astype(str).str.match("^[0-9]{14}$")
    df = df_add_error(df,mask_bad_siret,f"Numéro SIRET erroné pour le champ {col}")

    return df

def check_siret_ext(df: pd.DataFrame, dfb: pd.DataFrame, col: str, type:str) -> pd.DataFrame:
    """
    Le SIRET comprend 14 caractères (9 pour le SIREN + 5 pour le NIC) – format texte pour ne pas
    supprimer les « 0 » en début de Siret. L’identifiant autorité concédante est INEXPLOITABLE 
    s’il ne respecte pas le format. Si INEXPLOITABLE, le contrat est mis de côté.
    """
    col_id = col +'_id_1'
    col_type = col +'_typeIdentifiant_1'
    expression = None

    if type=='SIRET':
        expression =  "^[0-9]{14}$"
    #if type=='TVA':
    #    expression = ?
    if type=='TAHITI':
        expression =  "^[a-zA-Z0-9]{9}$"
    if type=='RIDET':
        expression =  "^[a-zA-Z0-9]{10}$"
    if type=='FRWF':
        expression =  "^FRWF[a-zA-Z0-9]{14}$"
    if type=='IREP':
        expression =  "^[0-9]{5}[a-zA-Z0-9]*$"
    if type=='HORS-UE':
        expression =  "^[A-Z]{2}[a-zA-Z0-9]{0,16}$"
  
    if expression!=None:
        
        mask_bad_col = (df[col_type]==type) & (~df[col_id].astype(str).str.match(expression))
        
        if type=='SIRET' and (col_id=='titulaire_id_1' or col_id=='concessionnaire_id_1'):
            mask_bad_col = (df[col_type]==type) & (~df[col_id].apply(check_insee_field))
            df = df_add_error(df,mask_bad_col,f"Numéro {type} erroné pour le champ {col}")

        df = df_add_error(df,mask_bad_col,f"Numéro {type} erroné pour le champ {col}")

    return df


def check_id(df: pd.DataFrame, dfb: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    L’identifiant d'un contrat de concession/marché comprend :
        - 4 caractères pour l’année de notification
        - 1 à 10 caractères pour le numéro interne
        - 2 caractères pour le numéro d’ordre de la modification
    Le numéro d’identification est INEXPLOITABLE s’il ne respecte pas le format.
    """

    def validate_contract_identifier(identifier):
        pattern = r'^\d{4}[A-Z0-9]{1,10}\d{2}$'  # Regex pattern for the identifier format
        return bool(re.match(pattern, identifier))

    dfb = pd.concat([dfb, df[~df[col].astype(str).apply(validate_contract_identifier)]])
    df = df[df[col].astype(str).apply(validate_contract_identifier)]
    return df, dfb


def check_duree_contrat(df: pd.DataFrame, dfb: pd.DataFrame, month: int) -> pd.DataFrame:
    """
    Si durée en mois > month alors INEXPLOITABLE
    Si durée en mois = 0 alors INEXPLOITABLE
    """
    df["dureeMois"] = df["dureeMois"].astype(int)

    mask_bad_col = df["dureeMois"] > month
    df = df_add_error(df,mask_bad_col,f"Champ dureeMois trop grand")

    mask_bad_col = df["dureeMois"] <= 0
    df = df_add_error(df,mask_bad_col,f"Champ dureeMois trop petit")

    return df


def check_id_format(df: pd.DataFrame, dfb: pd.DataFrame) -> pd.DataFrame:
    """
    Si le format de l'id est mauvais alors INEXPLOITABLE donc mis en exclu
    """
    pattern = r'^[A-Za-z0-9/\-_ .#]{1,16}$'
    
    mask_bad_col = ~df["id"].str.match(pattern,na=False)
    df = df_add_error(df,mask_bad_col, f"Champ id au mauvais format")
    
    return df

def mark_mandatory_field(df: pd.DataFrame,field_name:str) -> pd.DataFrame:
    """
    Le contenu de la colonne "field_name" du dataframe "df" est vérifié.
    La colonne "filed_name" est un colonne obligatoire.
    Les cases vides sont complétées par le tag "MQ", qui signifie 
    "manquant".
    """
    if field_name in df.columns:
        empty_mandatory = ~pd.notna(df[field_name]) | pd.isnull(df[field_name]) \
         | (df[field_name]=='<NA>') | (df[field_name]=='nan')
        if not empty_mandatory.empty:
            df[field_name] = df[field_name].astype('str')
            df.loc[empty_mandatory,field_name] = 'MQ'  
    return df

def mark_mixed_field(df:pd.DataFrame, field_name:str) -> pd.DataFrame:
    """
    Fonction traitant un cas particulier pour les champs "orgineUE"
    et "orgineFrance". Selon la valeur du codeCPV, ces deux
    champs sont obligatoires. Donc ils doivent être tagués par "MQ".    
    """
    # Transformation de la colonne CPV      
    df_cpv = pd.read_excel("data/cpv_2008_fr.xls", engine="xlrd")
    # Fix FutureWarning df_cpv['CODE'] = df_cpv['CODE'].replace("-", ".")
    with pd.option_context("future.no_silent_downcasting", True):
        df_cpv['CODE'] = df_cpv['CODE'].replace("-", ".").infer_objects(copy=False) #On souhaite  réaliser ue conversion numérique. Donc 
                                                                                    #on remplace les "-" par les points.
    df_cpv['CODE'] = pd.to_numeric(df_cpv['CODE'], errors='coerce')

    #Liste des intervalles de codes 
    codes_obligatoires = [
    (15100000.9, 15982200.7),
    (34100000.8, 34144910.0),
    (34510000.5, 34522700.9),
    (34600000.3, 34622500.8),
    (34710000.7, 34722200.6),
    (33100000.1, 33198200.6),
    (33600000.6, 33698300.2),
    (18100000.0, 18453000.9),
    (18800000.7, 18843000.0)
    ]

    #Nous utiliserons cette variable pour le masque pour chacun des intervalles
    masque_codes_obligatoires = pd.Series([False] * len(df_cpv))

    #Mise à jour du masque
    for debut, fin in codes_obligatoires:
        masque_intervalle = (df_cpv['CODE'] >= debut) & (df_cpv['CODE'] <= fin)
        masque_codes_obligatoires = masque_codes_obligatoires | masque_intervalle  #OU inclusif

    #Obtention de du dataframe ayant les codes CPV où les champs "orgineFrance" et "origineUE" sont obligatoires
    df_codes_obligatoires = df_cpv[masque_codes_obligatoires]
    # Fix FutureWarning df_codes_obligatoires = df_codes_obligatoires['CODE'].replace(".", "-")
    with pd.option_context("future.no_silent_downcasting", True):
        df_codes_obligatoires = df_codes_obligatoires['CODE'].replace(".", "-").infer_objects(copy=False)
    
    #Selon la liste, nous allons marquer les colonnes "orgineFrance" et "origineUE" par le tag "MQ"
    mandatory_code = df['codeCPV'].isin(df_codes_obligatoires.tolist())
    empty_mixed  = (~pd.notna(df[field_name]) | pd.isnull(df[field_name]) | (df[field_name]=='') | \
                    (df[field_name]=='nan')) & mandatory_code
    if not empty_mixed.empty: 
        df.loc[empty_mixed,field_name] = 'MQ'
    df[field_name] = df[field_name].astype(str)
    return df

def mark_optional_field(df: pd.DataFrame,field_name:str) -> pd.DataFrame:
    """
    Le contenu de la colonne "field_name" du dataframe "df" est vérifié.
    La colonne "filed_name" est un colonne optionnelle.
    Les cases vides sont complétées par le tag "CDL", qui signifie 
    "conditionnelle".
    """
    if field_name in df.columns:
        empty_optional  = ~pd.notna(df[field_name]) | pd.isnull(df[field_name]) | \
            (df[field_name]=='') | (df[field_name]=='<NA>') | (df[field_name]=='nan')
        if not empty_optional.empty:
            df[field_name] = df[field_name].astype('str')
            df.loc[empty_optional,field_name] = 'CDL'
    return df

def mark_bad_format_field(df: pd.DataFrame,field_name:str,pattern:str) -> pd.DataFrame:
    if field_name in df.columns:
        empty_mandatory = pd.notna(df[field_name]) & ~pd.isnull(df[field_name]) & \
            ~df[field_name].str.match(r'^(?:MQ|CDL|INX)$', na=False, case=False) & \
            ~df[field_name].str.match(pattern, na=False, case=False)
        if not empty_mandatory.empty:
            df.loc[empty_mandatory,field_name] = 'INX '+df.loc[empty_mandatory,field_name]
    return df

def mark_bad_format_field_list(df: pd.DataFrame,field_name:str,pattern:str) -> pd.DataFrame:
    if field_name in df.columns:
        empty_mandatory = pd.notna(df[field_name]) & ~pd.isnull(df[field_name]) & \
            ~df[field_name].str.match(r'^(?:MQ|CDL)$', na=False, case=False) & \
            ~df[field_name].str.match(pattern, na=False, case=False)
        if not empty_mandatory.empty and type(df.loc[empty_mandatory,field_name]) == list:
            df.loc[empty_mandatory,field_name] = 'INX '+df.loc[empty_mandatory,field_name]
    return df

def mark_bad_value_field(df: pd.DataFrame,field_name:str,field_name_2:str,pattern:str) -> pd.DataFrame:
    if field_name in df.columns:
        empty_mandatory = pd.notna(df[field_name]) & ~pd.isnull(df[field_name]) & \
            df[field_name].str.match(r'^(?:true|oui|1)$', na=False, case=False) & \
            df[field_name_2].str.match(pattern, na=False, case=False)
        if not empty_mandatory.empty:
            df.loc[empty_mandatory,field_name_2] = 'INX '+df.loc[empty_mandatory,field_name_2]
    return df

def has_at_least_one(data:list):
    if isinstance(data,list):
        return len(data)>0
    else:
        return ((data != None) and (data != ''))

def evaluate_field_value(data:list,pattern:str):
    if isinstance(data,list):
        for num, value in enumerate(data, start=0):
            if isinstance(value,list):
                for num, value in enumerate(value, start=0):
                    if not re.match(pattern, value, re.IGNORECASE):
                        data[num] = "INX "+data[num]
                        return False
            else:
                if not re.match(pattern, value[0], re.IGNORECASE):
                    data[num] = "INX "+data[num]
                    return False
    else:
        if not re.match(pattern, data, re.IGNORECASE):
            data = "INX "+data
            return False

    return True

def mark_bad_format_multi_field(df: pd.DataFrame,field_name:str,pattern:str) -> pd.DataFrame:
    if field_name in df.columns:
        empty_mandatory = pd.notna(df[field_name]) & ~pd.isnull(df[field_name]) & ~df[field_name].apply(evaluate_field_value,pattern=pattern)
        empty_mandatory = pd.notna(df[field_name]) & ~pd.isnull(df[field_name]) & ~df[field_name].apply(has_at_least_one)
        if not empty_mandatory.empty:
            df.loc[empty_mandatory,field_name] = 'MQ'
    return df

def mark_bad_format_int_field(df: pd.DataFrame,field_name:str,pattern:str = r'^[0-9]{1,12}(\.0{1,4})?$') -> pd.DataFrame:
    if field_name in df.columns:
        empty_mandatory = pd.notna(df[field_name]) & ~pd.isnull(df[field_name]) & \
            ~df[field_name].astype(str).str.match(r'^(?:MQ|CDL)$', na=False, case=False) & \
            ~df[field_name].astype(str).str.match(pattern, na=False, case=False)
        if not empty_mandatory.empty:
            df.loc[empty_mandatory,field_name] = 'INX '+df.loc[empty_mandatory,field_name].astype(str)
            
        #Les lignes dont le contenu est de la forme "XXXX.0" sont transformés en entier. On ne garde que la partie entière car la partie décimale est nulle
        almost_int = df[field_name].astype(str).str.match(r'^[0-9]+\.(0+)$', na=False, case=False)
        df.loc[almost_int, field_name] = df.loc[almost_int, field_name].apply(lambda x: x.split('.')[0])
    return df

def mark_bad_format_float_field(df: pd.DataFrame,field_name:str,pattern:str = r'^[0-9]{1,12}.{0,1}[0-9]{0,4}$') -> pd.DataFrame:
    if field_name in df.columns:
        empty_mandatory = pd.notna(df[field_name]) & ~pd.isnull(df[field_name]) & \
            ~df[field_name].astype(str).str.match(r'^(?:MQ|CDL)$', na=False, case=False) & \
            ~df[field_name].astype(str).str.match(pattern, na=False, case=False)
        if not empty_mandatory.empty:
            df.loc[empty_mandatory,field_name] = 'INX '+df.loc[empty_mandatory,field_name].astype(str)
    return df

def check_insee_field(number):
    number = str(number)
    if not pd.isna(number): 
        number = clean(number, ' .').strip()
        if not number.isdigit():
            #raise InvalidFormat()
            return False
        if len(number) != 14:
            #raise InvalidLength()
            return False
        try:
            luhn.validate(number)
            #siren.validate(number[:9])
        except InvalidChecksum:
            return False
    return True

def evaluate_insee(number: str):
    if not pd.isna(number) and check_insee_field(number):
        return number
    else:
        return None

def mark_bad_insee_field(df: pd.DataFrame,field_name:str,field_type:str = None) -> pd.DataFrame:
    pattern = r'^[0-9]{1,14}$'
    if field_name in df.columns:
        if field_type == None:
            empty_mandatory = pd.notna(df[field_name]) & ~pd.isnull(df[field_name]) &  \
                ~df[field_name].astype(str).str.match(r'^(?:MQ|CDL)$', na=False, case=False) & \
                (~df[field_name].str.match(pattern, na=False) | ~df[field_name].apply(check_insee_field))
            if not empty_mandatory.empty:
                df.loc[empty_mandatory,field_name] = 'INX '+df.loc[empty_mandatory,field_name]
        else:
            empty_mandatory = pd.notna(df[field_name]) & ~pd.isnull(df[field_name]) &  \
                ~df[field_name].astype(str).str.match(r'^(?:MQ|CDL)$', na=False, case=False) & \
                ((~df[field_type].astype(str).str.match('SIRET')) & (~df[field_type].astype(str).str.match('TVA')) \
                & (~df[field_name].astype(str).str.match(pattern, na=False)) | \
                ((df[field_type].astype(str).str.match('SIRET')) & (~df[field_name].apply(check_insee_field))) )
            if not empty_mandatory.empty:
                df.loc[empty_mandatory,field_name] = 'INX '+df.loc[empty_mandatory,field_name].astype(str)
    return df

@compute_execution_time
def marche_mark_fields(df: pd.DataFrame) -> pd.DataFrame:

    #df = mark_mandatory_field(df,"id")
    df = mark_mandatory_field(df,"nature")
    df = mark_mandatory_field(df,"objet")
    df = mark_mandatory_field(df,"techniques")
    df = mark_mandatory_field(df,"modalitesExecution")
    df = mark_mandatory_field(df,"codeCPV")
    df = mark_mandatory_field(df,"procedure")
    df = mark_mandatory_field(df,"dureeMois")
    df = mark_mandatory_field(df,"dateNotification")
    df = mark_mandatory_field(df,"considerationsSociales")
    df = mark_mandatory_field(df,"considerationsEnvironnementales")
    df = mark_mandatory_field(df,"marcheInnovant")
    df = mark_mandatory_field(df,"ccag")
    df = mark_mandatory_field(df,"offresRecues")
    df = mark_mandatory_field(df,"montant")
    df = mark_mandatory_field(df,"formePrix")
    df = mark_mandatory_field(df,"typesPrix")
    df = mark_mandatory_field(df,"attributionAvance")
    df = mark_mandatory_field(df,"datePublicationDonnees")
    df = mark_mandatory_field(df,"acheteur.id")
    df = mark_mandatory_field(df,"lieuExecution.code")
    df = mark_mandatory_field(df,"lieuExecution.typeCode")
    df = mark_mandatory_field(df,"titulaire_id_1")
    df = mark_mandatory_field(df,"titulaire_typeIdentifiant_1")
    
    #Mixed fields particualr case
    df = mark_mixed_field(df,"origineUE")
    df = mark_mixed_field(df,"origineFrance")

    # Optional fields
    df = mark_optional_field(df,"titulaire_id_2")
    df = mark_optional_field(df,"titulaire_typeIdentifiant_2")
    df = mark_optional_field(df,"titulaire_id_3")
    df = mark_optional_field(df,"titulaire_typeIdentifiant_3")
    df = mark_optional_field(df,"idAccordCadre")
    df = mark_optional_field(df,"tauxAvance")
    df = mark_optional_field(df,"typeGroupementOperateurs")
    df = mark_optional_field(df,"sousTraitanceDeclaree")
    df = mark_optional_field(df,"origineUE")
    df = mark_optional_field(df,"origineFrance")

    # Actes sous traitance
    df = mark_optional_field(df,"idActeSousTraitance")
    df = mark_optional_field(df,"dureeMoisActeSousTraitance")
    df = mark_optional_field(df,"dateNotificationActeSousTraitance")
    df = mark_optional_field(df,"montantActeSousTraitance")
    df = mark_optional_field(df,"variationPrixActeSousTraitance")
    df = mark_optional_field(df,"datePublicationDonneesActeSousTraitance")
    # Actes sous traitance /  Sous traitant
    df = mark_optional_field(df,"idSousTraitant")
    df = mark_optional_field(df,"typeIdentifiantSousTraitant")
    # Modifications
    df = mark_optional_field(df,"idModification")
    df = mark_optional_field(df,"dureeMoisModification")
    df = mark_optional_field(df,"montantModification")
    df = mark_optional_field(df,"dateNotificationModificationModification")
    df = mark_optional_field(df,"datePublicationDonneesModificationModification")
    # Modifications / Titulaires
    df = mark_optional_field(df,"idTitulaireModification")
    df = mark_optional_field(df,"typeIdentifiantTitulaireModification")
    # Modification actes sous traitance
    df = mark_optional_field(df,"idModificationActeSousTraitance")
    df = mark_optional_field(df,"typeIdentifiantModificationActeSousTraitance")
    df = mark_optional_field(df,"dureeMoisModificationActeSousTraitance")
    df = mark_optional_field(df,"dateNotificationModificationSousTraitanceModificationActeSousTraitance")
    df = mark_optional_field(df,"montantModificationActeSousTraitance")
    df = mark_optional_field(df,"datePublicationDonneesModificationActeSousTraitance")

    # Format check
    #df = mark_bad_format_field(df,"id",r'^[A-Za-z0-9\-_.\\/]{1,16}$')
    df = mark_bad_insee_field(df,"acheteur.id")
    df = mark_bad_format_field(df,"nature",r'^(?:Marché|Marché de partenariat|Marché de défense ou de sécurité)$')
    df = mark_bad_format_field(df,"objet",r'^.{0,1000}$')
    df = mark_bad_format_multi_field(df,"techniques",r'^(Accord-cadre|Concours|Système de qualification|Système d\'acquisition dynamique|Catalogue électronique|Enchère électronique|Sans objet)$')
    df = mark_bad_format_multi_field(df,"modalitesExecution",r'^(Tranches|Bons de commande|Marchés subséquents|Sans objet)$')
    df = mark_bad_format_field(df,"idAccordCadre",r'^[A-Za-z0-9\-_ .\\/]{1,16}$')
    #df = mark_bad_format_field(df,"codeCPV",r'^[0-9]{8}[-]{1}[0-9]{1}$')
    df = mark_bad_format_field(df,"procedure",r'^(Procédure adaptée|Appel d\'offres ouvert|Appel d\'offres restreint|Procédure avec négociation|Marché passé sans publicité ni mise en concurrence préalable|Dialogue compétitif)$')
    #df = mark_bad_format_field(df,"lieuExecution.code",r'^[A-Za-z0-9]{1,6}$')
    df = mark_bad_format_field(df,"lieuExecution.typeCode",r'^(Code postal|Code commune|Code arrondissement|Code canton|Code département|Code région|Code pays)$')
    df = mark_bad_format_int_field(df,"dureeMois")
    df = mark_bad_format_field(df,"dateNotification",PATTERN_DATE)  
    df = mark_bad_format_multi_field(df,"considerationsSociales",r'^(Clause sociale|Critère social|Marché réservé|Pas de considération sociale)$')
    df = mark_bad_format_multi_field(df,"considerationsEnvironnementales",r'^(Clause environnementale|Critère environnemental|Pas de considération environnementale)$')
    df = mark_bad_format_field(df,"marcheInnovant",r'^(True|False|0|1|oui|non)$')
    df = mark_bad_format_float_field(df,"origineUE")
    df = mark_bad_format_float_field(df,"origineFrance")
    df = mark_bad_format_field(df,"ccag",r'^(Travaux|Maitrise d\'œuvre|Fournitures courantes et services|Marchés industriels|Prestations intellectuelles|Techniques de l\'information et de la communication|Pas de CCAG)$')
    df = mark_bad_format_int_field(df,"offresRecues")
    #df = mark_bad_format_float_field(df,"montant")
    df = mark_bad_format_field(df,"formePrix",r'^(Unitaire|Forfaitaire|Mixte)$')
    df = mark_bad_format_multi_field(df,"typesPrix",r'^(Définitif ferme|Définitif actualisable|Définitif révisable|Provisoire)$')
    df = mark_bad_format_field(df,"attributionAvance",r'^(True|False|0|1|oui|non)$')
    df = mark_bad_format_float_field(df,"tauxAvance")
    df = mark_bad_insee_field(df,"titulaire_id_1","titulaire_typeIdentifiant_1")
    df = mark_bad_insee_field(df,"titulaire_id_2","titulaire_typeIdentifiant_2")
    df = mark_bad_insee_field(df,"titulaire_id_3","titulaire_typeIdentifiant_3")
    df = mark_bad_format_field(df,"titulaire_typeIdentifiant_1",r'^(SIRET|TVA|TAHITI|RIDET|FRWF|IREP|HORS-UE)$')
    df = mark_bad_format_field(df,"titulaire_typeIdentifiant_2",r'^(SIRET|TVA|TAHITI|RIDET|FRWF|IREP|HORS-UE)$')
    df = mark_bad_format_field(df,"titulaire_typeIdentifiant_3",r'^(SIRET|TVA|TAHITI|RIDET|FRWF|IREP|HORS-UE)$')
    df = mark_bad_format_field(df,"typeGroupementOperateurs",r'^(Conjoint|Solidaire|Pas de groupement)$')
    df = mark_bad_format_field(df,"sousTraitanceDeclaree",r'^(True|False|0|1|oui|non)$')
    df = mark_bad_format_field(df,"datePublicationDonnees",PATTERN_DATE)
    # ActesSousTraitance
    df = mark_bad_format_int_field(df,"idActeSousTraitance")
    # ActesSousTraitance
    df = mark_bad_format_int_field(df,"dureeMoisActeSousTraitance")
    df = mark_bad_format_field(df,"dateNotificationActeSousTraitance",PATTERN_DATE)
    df = mark_bad_format_float_field(df,"montantActeSousTraitance")
    df = mark_bad_format_field(df,"variationPrixActeSousTraitance",r'^(Ferme|Actualisable|Révisable)$')
    df = mark_bad_format_field(df,"datePublicationDonneesActeSousTraitance",PATTERN_DATE)
    # ActesSousTraitance / Sous traitants 
    df = mark_bad_insee_field(df,"idSousTraitant","typeIdentifiantSousTraitant")
    df = mark_bad_format_field(df,"typeIdentifiantSousTraitant",r'^(SIRET|TVA|TAHITI|RIDET|FRWF|IREP|HORS-UE)$')
    # Modifications
    df = mark_bad_format_int_field(df,"idModification")
    df = mark_bad_format_int_field(df,"dureeMoisModification")
    df = mark_bad_format_float_field(df,"montantModification")
    # Modifications / Titulaires
    df = mark_bad_insee_field(df,"idTitulaireModification","typeIdentifiantTitulaireModification")
    df = mark_bad_format_field(df,"typeIdentifiantTitulaireModification",r'^(SIRET|TVA|TAHITI|RIDET|FRWF|IREP|HORS-UE)$')
    # Modifications
    df = mark_bad_format_field(df,"dateNotificationModification",PATTERN_DATE)
    df = mark_bad_format_field(df,"datePublicationDonneesModification",PATTERN_DATE)
    # ModificationsActesSousTraitance
    df = mark_bad_format_int_field(df,"idModificationActeSousTraitance")
    df = mark_bad_format_int_field(df,"dureeMoisModificationActeSousTraitance")
    df = mark_bad_format_field(df,"dateNotificationModificationSousTraitanceModificationActeSousTraitance",PATTERN_DATE)
    df = mark_bad_format_float_field(df,"montantModificationActeSousTraitance")
    df = mark_bad_format_field(df,"datePublicationDonneesModificationActeSousTraitance",PATTERN_DATE)
    
    df = mark_bad_value_field(df,"attributionAvance","tauxAvance",r'^(?:0|0.0)$')

    return df

@compute_execution_time
def concession_mark_fields(df: pd.DataFrame) -> pd.DataFrame:

    #df = mark_mandatory_field(df,"id")
    df = mark_mandatory_field(df,"nature")
    df = mark_mandatory_field(df,"objet")
    df = mark_mandatory_field(df,"procedure")
    df = mark_mandatory_field(df,"dureeMois")
    df = mark_mandatory_field(df,"dateDebutExecution")
    df = mark_mandatory_field(df,"dateSignature")
    df = mark_bad_format_multi_field(df,"considerationsSociales",r'^(Clause sociale|Critère social|Concession réservé|Pas de considération sociale)$')
    df = mark_bad_format_multi_field(df,"considerationsEnvironnementales",r'^(Clause environnementale|Critère environnemental|Pas de considération environnementale)$')
    df = mark_mandatory_field(df,"valeurGlobale")
    df = mark_mandatory_field(df,"montantSubventionPublique")
    df = mark_mandatory_field(df,"datePublicationDonnees")
    df = mark_mandatory_field(df,"autoriteConcedante.id")
    df = mark_mandatory_field(df,"concessionnaire_id_1")
    df = mark_mandatory_field(df,"concessionnaire_typeIdentifiant_1")
    df = mark_mandatory_field(df,"donneesExecution.depensesInvestissement")
    df = mark_mandatory_field(df,"donneesExecution.datePublicationDonneesExecution")
    df = mark_mandatory_field(df,"donneesExecution.intituleTarif")
    df = mark_mandatory_field(df,"donneesExecution.tarif")

    df = mark_optional_field(df,"idModification")
    df = mark_optional_field(df,"dureeMoisModification")
    df = mark_optional_field(df,"valeurGlobaleModification")
    df = mark_optional_field(df,"dateSignatureModificationModification")
    df = mark_optional_field(df,"datePublicationDonneesModificationModification")
    df = mark_optional_field(df,"concessionnaire_id_2")
    df = mark_optional_field(df,"concessionnaire_typeIdentifiant_2")
    df = mark_optional_field(df,"concessionnaire_id_3")
    df = mark_optional_field(df,"concessionnaire_typeIdentifiant_3")

    #df = mark_bad_format_field(df,"id",r'^[A-Za-z0-9/\-_ ]{1,16}$')
    # Caractéristiques de l’autorité concédante
    df = mark_bad_insee_field(df,"idAutoriteConcedante")
    # Caractéristiques du contrat de concession
    df = mark_bad_format_field(df,"nature",r'^(?:Concession de travaux|Concession de service|Concession de service public|Délégation de service public)$')
    df = mark_bad_format_field(df,"objet",r'^.{0,1000}$')
    df = mark_bad_format_field(df,"procedure",r'^(Procédure négociée ouverte|Procédure non négociée ouverte|Procédure négociée restreinte|Procédure non négociée restreinte)$')
    df = mark_bad_format_float_field(df,"dureeMois")
    df = mark_bad_format_field(df,"dateDebutExecution",PATTERN_DATE)  
    df = mark_bad_format_field(df,"dateSignature",PATTERN_DATE)  
    df = mark_bad_format_multi_field(df,"considerationsSociales",r'^(Clause sociale|Critère social|Concession réservée|Pas de considération sociale)$')
    df = mark_bad_format_multi_field(df,"considerationsEnvironnementales",r'^(Clause environnementale|Critère environnemental|Pas de considération environnementale)$')
    # Concessionnaires
    df = mark_bad_insee_field(df,"concessionnaire_id_1","concessionnaire_typeIdentifiant_1")
    df = mark_bad_insee_field(df,"concessionnaire_id_2","concessionnaire_typeIdentifiant_2")
    df = mark_bad_insee_field(df,"concessionnaire_id_3","concessionnaire_typeIdentifiant_3")
    df = mark_bad_format_field(df,"concessionnaire_typeIdentifiant_1",r'^(SIRET|TVA|TAHITI|RIDET|FRWF|IREP|HORS-UE)$')
    df = mark_bad_format_float_field(df,"valeurGlobale")
    #df = mark_bad_format_field(df,"montantSubventionPublique",r'^[0-9]{1,14}$')
    df = mark_bad_format_field(df,"datePublicationDonnees",PATTERN_DATE)  
    # Modification du contrat de concession
    df = mark_bad_format_int_field(df,"idModification")
    df = mark_bad_format_int_field(df,"dureeMoisModification")
    df = mark_bad_format_float_field(df,"valeurGlobaleModification")
    df = mark_bad_format_field(df,"dateSignatureModification",PATTERN_DATE)  
    df = mark_bad_format_field(df,"datePublicationDonneesModification",PATTERN_DATE)  
    # Données d’exécution du contrat de concession
    df = mark_bad_format_float_field(df,"depensesInvestissementDonneesExecution")
    df = mark_bad_format_float_field(df,"dureeMoisDonneesExecution")
    df = mark_bad_format_float_field(df,"valeurGlobaleDonneesExecution")
    df = mark_bad_format_float_field(df,"donneesExecution.tarif")
    df = mark_bad_format_field(df,"donneesExecution.intituleTarif",r'^.{0,256}$')
    df = mark_bad_format_field(df,"datePublicationDonneesExecutionDonneeExecution",PATTERN_DATE)  

    return df

def replace_nc_colonne(df: pd.DataFrame,nom_colonne:str,is_float:bool=False) -> pd.DataFrame:
    if nom_colonne in df.columns:
        df['backup__' + nom_colonne] = df[nom_colonne]
        #probleme de reimport si ajout de colonne df[nom_colonne+'_source'] = df[nom_colonne]
        # Fix FutureWarning df[nom_colonne] = df[nom_colonne].replace("NC",pd.NA)
        with pd.option_context("future.no_silent_downcasting", True):
            if is_float:
                df[nom_colonne] = df[nom_colonne].replace("NC",0).infer_objects(copy=False)
            else:
                df[nom_colonne] = df[nom_colonne].replace("NC",pd.NA).infer_objects(copy=False)
    
    return df

def replace_nc_colonne_inside(df: pd.DataFrame,nom_colonne:str,nom_noeud:str,nom_element:str) -> pd.DataFrame:
    def replace_nc (content,noeud:str,sous_element:str,colonne:str):
        if isinstance(content,list):
            for element in content:
                if sous_element in element and isinstance(element[sous_element],dict) \
                    and colonne in element[sous_element] and element[sous_element][colonne] == "NC":
                        element[sous_element]['backup__'+colonne] = element[sous_element][colonne]
                        element[sous_element][colonne] = None
        return content
    if nom_noeud in df.columns:
        #probleme de reimport si ajout de colonne df[nom_colonne+'_source'] = df[nom_colonne]
        df[nom_noeud] = df[nom_noeud].apply(replace_nc,noeud=nom_noeud,sous_element=nom_element,colonne=nom_colonne)
    
    return df

if __name__ == '__main__':
    main()
