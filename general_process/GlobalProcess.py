import pandas as pd
import numpy as np
import ast
import json
import os
import re
from datetime import date
import pickle
import logging
import boto3
import requests
import math
import csv
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import jsonschema
from jsonschema import validate,Draft7Validator,Draft202012Validator
from reporting.Report import Report
from utils.NodeFormat import NodeFormat
from utils.StepMngmt import StepMngmt
from utils.Step import Step

with open(os.path.join("confs", "var_glob.json")) as f:
    conf_glob = json.load(f)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
class GlobalProcess:
    """La classe GlobalProcess est une classe qui définit les étapes de traitement une fois toutes
    les étapes pour toutes les sources effectuées : création des variables de la classe (__init__),
    fusion des sources dans un seul DataFrame (merge_all), suppression des doublons (drop_duplicate)
    et l'exportation des données en json pour publication (export)."""

    columns_with_list = ['titulaires','donneesExecution','modifications','concessionnaires','tarifs']
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    date_pattern_inv = r'\d{2}.\d{2}.\d{4}'

    def __init__(self,data_format="2022", report:Report=None):
        """L'étape __init__ crée les variables associées à la classe GlobalProcess : le DataFrame et
        la liste des dataframes des différentes sources."""
        logging.info("------------------------------GlobalProcess------------------------------")
        self.report = report
        self.df = pd.DataFrame()
        self.dataframes = []
        self.data_format = data_format

    @StepMngmt().decorator(Step.MERGE_ALL,StepMngmt.FORMAT_DATAFRAME)
    def merge_all(self) -> None:
        """Étape merge all qui permet la fusion des DataFrames de chacune des sources en un seul."""
        logging.info("--- ÉTAPE MERGE ALL")
        logging.info("Début de l'étape Merge des Dataframes")
        if len(self.dataframes)>0:
            self.df = pd.concat(self.dataframes, ignore_index=True)
            self.df = self.df.reset_index(drop=True)
            logging.info("Merge OK")
        else:
            logging.info("Aucune données à traiter")
        logging.info(f"Nombre de marchés dans le DataFrame fusionné après merge : {len(self.df)}")

    @StepMngmt().decorator(Step.FIX_ALL,StepMngmt.FORMAT_DATAFRAME)
    def fix_all(self):
        """
        Étape fix all qui permet l'uniformisation du DataFrame.
        """
        logging.info("--- ÉTAPE FIX ALL")
        logging.info("Début de l'étape Fix_all du DataFrame fusionné")

        if len(self.df) == 0:
            logging.warning("Le DataFrame est vide, pas de fix à faire.")
        
        # On met les acheteurs et lieux au bon format    #on a enlevé la suppression de "acheteur"
        if 'acheteur.id' in self.df.columns:
            self.df['acheteur.id'] = self.df['acheteur.id'].astype(str)
        if self.data_format=='2019' and 'lieuExecution.code' in self.df.columns:
            self.df['lieuExecution.code'] = self.df['lieuExecution.code'].astype(str)

        # Suppression des colonnes inutiles
        if 'dateTransmissionDonneesEtalab' in self.df.columns:
            self.df = self.df.drop('dateTransmissionDonneesEtalab', axis=1)
        # Format des dates
        #if self.data_format=='2022':
        #    date_columns = ['dateNotification', 'datePublicationDonnees',
        #                'dateDebutExecution',
        #                'acteSousTraitance.datePublicationDonneesSousTraitance',
        #                'modifications.titulaires.dateNotification',
        #                'modifications.titulaires.datePublicationDonneesModification',
        #                'modifications.sousTraitants.dateNotification',
        #                'modifications.sousTraitanrs.datePublicationDonnees']
        #else:
        #    date_columns = ['dateNotification', 'datePublicationDonnees',
        #                'dateDebutExecution']
        date_columns = ['dateNotification', 'datePublicationDonnees',
                        'dateDebutExecution']

        for s in date_columns:
            if s in self.df.columns:
                self.df[s] = self.df[s].apply(str)
                self.df[s] = self.df[s].apply(lambda x:
                                            x.replace('+', '-') if str(x) != 'nan' else x)
                self.df[s] = \
                    self.df[s].apply(lambda x:
                                    date(int(float(x.split("-")[0])),\
                                    min(int(float(x.split("-")[1])),12), \
                                    min(int(float(x.split("-")[2])),31)).isoformat()
                                    if str(x) != 'nan' and len(x.split("-")) >= 3 else x)
        logging.info(f"Nombre de marchés dans le DataFrame fusionné après merge : {len(self.df)}")
        if 'dureeMois' in self.df.columns:
            self.df['dureeMois'] = self.df['dureeMois'].apply(lambda x: 0 if x == '' or
                                                            str(x) in ['nan', 'None'] else x)
        else:
            self.df['dureeMois'] = pd.NA
        # Montant doit être un float
        if 'montant' in self.df.columns: 
            self.df['montant'] = self.df['montant'].apply(lambda x: 0 if x == '' or
                                                        str(x) in ['nan', 'None'] else float(x))
        else:
            self.df['montant'] = pd.NA
        # Type de contrat qui s'étale sur deux colonnes, on combine les deux et garde _type qui est l'appelation dans Ramav1
        dict_mapping = {"MARCHE_PUBLIC": "Marché", "CONTRAT_DE_CONCESSION":"Contrat de concession"}
        if '_type' in self.df.columns:
            bool_nan_type = self.df.loc[:, "_type"].isna()
            cols_to_drop = []
            if "typeContrat" in self.df.columns:  # Dans le cas où typeContrat n'existe pas, on ne fait rien
                self.df.loc[bool_nan_type, "_type"] = self.df.loc[bool_nan_type, "typeContrat"].map(dict_mapping)
                cols_to_drop.append("typeContrat") # On supprime donc typeContrat qui est maintenant vide
            if "ReferenceAccordCadre" in self.df.columns: # Dans le cas où ReferenceAccordCadre n'existe pas, on ne fait rien
                cols_to_drop.append("ReferenceAccordCadre")
            # ReferenceAccordCadre n'a que 6 valeurs non nul sur 650k lignes et en plus cette colonne n'existe pas dans v1.
            self.df = self.df.drop(cols_to_drop, axis=1)
            if "nature" in self.df.columns:
                self.df.loc[bool_nan_type, "_type"] = self.df.loc[bool_nan_type,"nature"].apply(lambda x: "Marché" if "march" in x.lower() else "Concession")
        else:
            logging.warning("_type non defini")
        # S'il y a des Nan dans les modifications, on met une liste vide pour coller au format du v1
        if "modifications" in self.df.columns:
            mask_modifications_nan = self.df.loc[:, "modifications"].isnull()
            self.df.loc[mask_modifications_nan, "modifications"] = self.df.loc[mask_modifications_nan, "modifications"].apply(lambda x: [])
            #self.df.modifications.loc[mask_modifications_nan] = self.df.modifications.loc[mask_modifications_nan].apply(lambda x: [])
        # Gestion des multiples modifications  ===> C'est traité dans la partie gestion de la version flux. On va garder cette manière de faire, mais il faut une autre solution pour les unashable type.
        #col_to_normalize = "modifications"
        #mask_multiples_modifications = self.df.modifications.apply(lambda x:len(x)>1)
        #self.df.loc[mask_multiples_modifications, col_to_normalize] = self.df.loc[mask_multiples_modifications, col_to_normalize].apply(concat_modifications).apply(trans)
        
        #mask_modif = self.df.modifications.apply(len)>0
        #self.df.loc[mask_modif, "modifications"] = self.df.loc[mask_modif, "modifications"].apply(remove_titulaire_key_in_modif)
        self._add_meta_modifications(self.df,pd.DataFrame())
        
    def drop_by_date_2024(self):
        """ 
        Supprime les lignes ne respectant pas les critères de date. Si le format suivi est de 2022, 
        les champs 'dateNotification' et 'dateDebutExecution' doivent être supérieurs au 01/01/24.
        Si le format suivi est de 2019, ces champs doivent être inférieurs au 01/01/24.
        """
        # Delete all records with dateNotification or dateDebutExecution> 2024-01-01 ECO Compatibility V4
        if self.data_format=='2022':
            self.df = self.df[~(((~self.df['nature'].str.contains('concession', case=False, na=False)) & (self.df['dateNotification']<'2024-01-01') |
                            ((self.df['nature'].str.contains('concession', case=False, na=False)) & (self.df['dateDebutExecution']<'2024-01-01'))))]
        else:
            self.df = self.df[~(((~self.df['nature'].str.contains('concession', case=False, na=False)) & (self.df['dateNotification']>='2024-01-01') |
                            ((self.df['nature'].str.contains('concession', case=False, na=False)) & (self.df['dateDebutExecution']>='2024-01-01'))))]

    @StepMngmt().decorator(Step.DUPLICATE,StepMngmt.FORMAT_DATAFRAME)
    def drop_duplicate(self):
        """
        L'étape drop_duplicate supprime les duplicats purs après avoir 
        supprimé les espaces et convertis l'ensemble du DataFrame en string.
        """

        logging.info("--- ÉTAPE DROP DUPLICATE")
        # if df is empty then return
        if len(self.df) == 0:
            logging.warning(f"Le DataFrame global est vide, impossible de supprimer les doublons")


        # Séparation des lignes selon la colonne "modifications"
        logging.info("Début de l'étape Suppression des doublons")

        if 'source' in self.df.columns:
            self.df.sort_values(by="source", inplace=True) 
        else : 
            self.df['source'] = pd.NA
        self.df = self.dedoublonnage(self.df,True)
        logging.info("Suppression OK")
        logging.info(f"Nombre de marchés dans Df après suppression des doublons sur les nouvelles données : {len(self.df)}")

    def dedoublonnage(self,df: pd.DataFrame,add_report=True) -> pd.DataFrame:
        nb_duplicated_marches = 0
        nb_duplicated_concessions = 0

        # On complete la colonne backup montant pour les marches ajoutés depuisl'export qui ne sont pas passé par fix
        if "montant" in self.df.columns and 'backup__montant' in self.df.columns \
            and df.loc[df['_type'] == 'Marché', 'backup__montant'].isna().any():
            df.loc[(df['backup__montant'].isna()) & (df['_type'] == 'Marché'), 'backup__montant'] = df['montant']
            df.loc[df['_type'] == 'Marché', 'montant'] = df.loc[df['_type'] == 'Marché', 'montant'].apply(lambda x: int(x) if pd.notna(x) else np.nan)

        #Critères de dédoublonnage
        feature_doublons_marche = ["id", "acheteur", "titulaires", "dateNotification", "montant"] 
        feature_doublons_marche_order = ["id", "acheteur", "titulaires", "dateNotification", "montant",'tmp__dateModification','tmp__idModification'] 
        feature_doublons_concession = [ "id", "autoriteConcedante", "concessionnaires", "dateDebutExecution", "valeurGlobale"]
        feature_doublons_concession_order = [ "id", "autoriteConcedante", "concessionnaires", "dateDebutExecution", "valeurGlobale",'tmp__dateModification','tmp__idModification']

        #Séparation des marches et des concessions, suppression des doublons
        df_marche = df[df['_type'].str.contains("Marché")]
        if not df_marche.empty:
            df_marche = df_marche.astype(str)
            df_marche = df_marche.sort_values(
                feature_doublons_marche_order,
                ascending=[True, True, True, True, True, True, True]
            )
            index_to_keep = df_marche.drop_duplicates(subset=feature_doublons_marche, keep='last').index.tolist()

        # Mémoriser la nombre de marchés en double
        nb_duplicated_marches = len(df_marche)-len(index_to_keep)
        if add_report:
            self.report.nb_duplicated_marches += nb_duplicated_marches

        df_concession = df[~df['_type'].str.contains("Marché")]
        if not df_concession.empty:
            df_concession = df_concession.astype(str)
            df_concession = df_concession.sort_values(
                feature_doublons_concession_order,
                ascending=[True, True, True, True, True, True, True]
            )
            index_to_keep += df_concession.drop_duplicates(subset=feature_doublons_concession, keep='last').index.tolist()

        # Mémoriser la nombre de concessions après dédoublonnage
        nb_duplicated_concessions = len(df_concession) - ( len(index_to_keep) - (len(df_marche) - nb_duplicated_marches) )
        if add_report:
            self.report.nb_duplicated_concessions += nb_duplicated_concessions

        if add_report:
            # Ajouter au reporting les doublons supprimés
            self.report.add('FixAll/Marchés',self.report.D_DUPLICATE,'Marchés en doublon',df_marche[df_marche.duplicated(feature_doublons_marche)])
            self.report.add('FixAll/Concessions',self.report.D_DUPLICATE,'Concessions en doublon',df_concession[df_concession.duplicated(feature_doublons_concession)])

        df = df.loc[index_to_keep, :]
        df = df.reset_index(drop=True)
        
        logging.info(f"Dedoublonnage {nb_duplicated_marches + nb_duplicated_concessions} lignes supprimées")
        return df

    def dedoublonnage_OLD(self,df: pd.DataFrame,add_report=True) -> pd.DataFrame:
        nb_duplicated_marches = 0
        nb_duplicated_concessions = 0

        # On complete la colonne backup montant pour les marches ajoutés depuisl'export qui ne sont pas passé par fix
        if "montant" in self.df.columns and 'backup__montant' in self.df.columns \
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
        if add_report:
            self.report.nb_duplicated_marches += nb_duplicated_marches_no_modif

        df_nomodif_concession = df_nomodif_str[~df_nomodif_str['_type'].str.contains("Marché")]
        index_to_keep_nomodif += df_nomodif_concession.drop_duplicates(subset=feature_doublons_concession).index.tolist()

        # Mémoriser la nombre de concessions après dédoublonnage
        nb_duplicated_concessions_no_modif = len(df_nomodif_concession) - ( len(index_to_keep_nomodif) - (len(df_nomodif_marche) - nb_duplicated_marches_no_modif) )
        if add_report:
            self.report.nb_duplicated_concessions += nb_duplicated_concessions_no_modif

        if add_report:
            # Ajouter au reporting les doublons supprimés
            self.report.add('FixAll/Marchés',self.report.D_DUPLICATE,'Marchés en doublon',df_nomodif_marche[df_nomodif_marche.duplicated(feature_doublons_marche)])
            self.report.add('FixAll/Concessions',self.report.D_DUPLICATE,'Concessions en doublon',df_nomodif_concession[df_nomodif_concession.duplicated(feature_doublons_concession)])

        #Séparation des marches et des concessions, tri selon la date et suppression ses doublons
        if not df_modif.empty:
            df_modif_str  = df_modif.astype(str)     #en str pour réaliser le dédoublonnage
            df_modif_str.sort_values(by=["datePublicationDonnees"], inplace=True)   #Tri
            
            df_modif_marche = df_modif_str[df_modif_str['_type'].str.contains("Marché")]
            index_to_keep_modif = df_modif_marche.drop_duplicates(subset=feature_doublons_marche,keep='last').index.tolist()  #'last', permet de garder la ligne avec la date est la plus récente

            # Mémoriser la nombre de marchés après dédoublonnage
            nb_duplicated_marches = len(df_modif_marche)-len(index_to_keep_modif)
            if add_report:
                self.report.nb_duplicated_marches += nb_duplicated_marches

            df_modif_concession = df_modif_str[~df_modif_str['_type'].str.contains("Marché")]
            index_to_keep_modif += df_modif_concession.drop_duplicates(subset=feature_doublons_concession,keep='last').index.tolist()  #on ne garde que que les indexs pour récupérer les lignes qui sont dans df_modif (dont le type est dict)

            # Mémoriser la nombre de concessions après dédoublonnage
            nb_duplicated_concessions = len(df_modif_concession) - ( len(index_to_keep_modif) - ( len(df_modif_marche) - nb_duplicated_marches ) )
            if add_report:
                self.report.nb_duplicated_concessions += nb_duplicated_concessions

            if add_report:
                # Ajouter au reporting les doublons supprimés
                self.report.add('FixAll/Merchés',self.report.D_DUPLICATE,'Marchés en doublon',df_nomodif_marche[df_nomodif_marche.duplicated(feature_doublons_marche)])
                self.report.add('FixAll/Concessions',self.report.D_DUPLICATE,'Concessions en doublon',df_nomodif_concession[df_nomodif_concession.duplicated(feature_doublons_concession)])

            df = pd.concat([df_nomodif.loc[index_to_keep_nomodif, :], df_modif.loc[index_to_keep_modif, :]])

        else:
            df = df_nomodif.loc[index_to_keep_nomodif, :]
        df = df.reset_index(drop=True)
        
        logging.info(f"Dedoublonnage {nb_duplicated_marches_no_modif + nb_duplicated_concessions_no_modif + nb_duplicated_marches + nb_duplicated_concessions} lignes supprimées")
        return df

    def extract_publication_dates(self, modifications_node) -> list:
        # Pour test sur chaine de caractere modification_list = ast.literal_eval(modification_str)  # Évalue la chaîne comme une structure de données
        dates_publication = []
        for modification in modifications_node:
            if 'modification' in modification and isinstance(modification['modification'],dict):
                if 'datePublicationDonneesModification' in modification['modification']:
                    dates_publication.append(modification['modification']['datePublicationDonneesModification'])
                else:
                    dates_publication.append(modification['modification']['modification']['datePublicationDonneesModification'])
            elif 'modification' in modification and isinstance(modification['modification'],list):
                return self.extract_publication_dates(modification['modification'])
        return dates_publication

    def _add_meta_modifications(self,df_marches,df_concessions,process_dates:bool=True):
        def _extract_max_id_modification(modifications):
            # Récupérer les ids et retourner le maximum
            ids = [item['modification']['id'] for item in modifications if 'modification' in item]
            return max(ids) if ids else 0
        
        def _extract_max_date_modification(modifications):
            # Récupérer les dates et retourner le maximum
            dates = [pd.to_datetime(item['modification']['datePublicationDonneesModification'], errors='coerce') for item in modifications if 'modification' in item]
            return max(dates) if dates else pd.NA
        
        def _max_date(row):
            """Cette fonction revoie la date la plus avancée dans le temps entre les date de modification (tmp__datModification) et la date de publication des données."""
            pub_date = pd.to_datetime(row['datePublicationDonnees'])
            mod_date = pd.to_datetime(row['tmp__dateModification'])
            # Choix de la date maximale, NaN s'il n'y a que NaN
            m = max(pub_date, mod_date) if not (pd.isna(pub_date) and pd.isna(mod_date)) else pd.to_datetime("2024-01-01")
            # Si la date est antérieure à 2024 ou est nulle, on la remplace par 2024-01-01
            if m<pd.to_datetime("2024-01-01") or m is pd.NaT:
                m = pd.to_datetime("2024-01-01")
            return m
        
        def _tri_titulaires(titulaires):
            """Cette fonction trie les titulaires par id afin d'éviter les erreurs de calcul de doublons lorsque l'ordre dans les données en entrée change."""
            return sorted(titulaires, key=lambda x: x['titulaire']['id']) if isinstance(titulaires, list) else titulaires

        def _tri_concessionnaires(concessionnaires):
            """Cette fonction trie les concessionnaires par id afin d'éviter les erreurs de calcul de doublons lorsque l'ordre dans les données en entrée change."""
            return sorted(concessionnaires, key=lambda x: x['concessionnaire']['id']) if isinstance(concessionnaires, list) else concessionnaires

        def _prepare_group_by(df):
            """Cette fonction prépare les données pour le groupby sur tmp__annee_mois  en ajoutant les données dans les colonnes tmp__idModification et tmp__dateModification et tmp__annee_mois."""
            if not df.empty:# df[df['datePublicationDonnees'].isna()]['datePublicationDonnees']
                df['datePublicationDonnees'] = pd.to_datetime(df['datePublicationDonnees'],format='mixed',errors='coerce')
                if 'modifications' in df.columns:
                    df['tmp__idModification'] = df['modifications'].apply(_extract_max_id_modification)
                    df['tmp__dateModification'] = df['modifications'].apply(_extract_max_date_modification)
                else:
                    df['tmp__dateModification'] = pd.NaT
                df['tmp__dateModification'] = df.apply(_max_date, axis=1)
                df['tmp__dateModification'] = df['tmp__dateModification'] #.dt.strftime('%Y-%m')
                df['tmp__annee_mois'] = df['tmp__annee_mois'].where(df['tmp__annee_mois'].notna(), df['tmp__dateModification'].dt.strftime('%Y-%m'))#.strftime('%Y-%m')
                df['tmp__dateModification'] = df['tmp__dateModification'].astype(str)
                df['datePublicationDonnees'] = df['datePublicationDonnees'].astype(str) 

        if not df_marches.empty:
            df_marches['titulaires'] = df_marches['titulaires'].apply(_tri_titulaires)
            if process_dates:
                _prepare_group_by(df_marches) # df_marches)
            if "tmp__dateModification" not in df_marches.columns:
                df_marches['tmp__dateModification'] = df_marches['datePublicationDonnees']
            if "tmp__idModification" not in df_marches.columns:
                df_marches['tmp__idModification'] = 0


        if not df_concessions.empty:
            df_concessions['concessionnaires'] = df_concessions['concessionnaires'].apply(_tri_concessionnaires)
            if process_dates:
                _prepare_group_by(df_concessions) # df_concessions)
            if "tmp__dateModification" not in df_concessions.columns:
                df_concessions['tmp__dateModification'] = df_concessions['datePublicationDonnees']
            if "tmp__idModification" not in df_concessions.columns:
                df_concessions['tmp__idModification'] = 0
            
    def _merge_in_file(self, file_path:str, dico:dict) -> dict:
        """
        La fonction _merge_in_file permet de fusionner un dictionnaires en entrée avec 
        le dictionnaire contenu dans un fichier
        Args:
            file_name: Nom du fichier contenant le dictionnaire à fusionner
            dico: dictionnaire à ajouter
        """
        #On vérifie que le fichier existe bien, sinon on le crée
        if os.path.exists(file_path):
            dico_file = self.file_load(file_path)
            if dico_file=={}:
                self.file_dump(file_path,dico)
            else:
                dico_global = dico['marches'] + dico_file['marches']
                #On transforme les dictionnaires en dataframes pour les dédoublonner
                df_global = pd.DataFrame.from_dict(dico_global)
                df_global = self.dedoublonnage(df_global)
                dico_final = self._nan_correction_dico(df_global)
                self.file_dump(file_path,dico_final)     
                return dico_final              
        else:
            # Le fichier n'existait pas on ajoute le nouveau dictionnaire dedans
            self.file_dump(file_path,dico)
        return dico
    
    def upload_on_datagouv(self):
        logging.info(f"Uploading file ...")
        config_file = "config.json"
        # read info from config.son
        with open(config_file, "r") as f:
            config = json.load(f)
            api = config["url_api"]
            dataset_id = config["dataset_id"]
            data_gouv_api_key = config["data_gouv_api_key"]
            month_previous_update = config["resource_month"]
            year_previous_update = config["resource_year"]

        headers = {
            "X-API-KEY": data_gouv_api_key
        }
        years = []

        for suffix_month, _ in self.df.groupby('tmp__annee_mois'):
            logging.info(f"Uploading file decp-{suffix_month}.json")
            resource_id_month = self._get_ressource_id(headers,api,dataset_id,suffix_month)
            resource_id_month = self._upload_file(headers,api,dataset_id,resource_id_month,suffix_month)
            suffix_year = suffix_month[0:4]
            if suffix_year in years:
                logging.info(f"Uploading file decp-{suffix_year}.json")
                years += [suffix_year]
                resource_id_year = self._get_ressource_id(headers,api,dataset_id,suffix_year)
                resource_id_year = self._upload_file(headers,api,dataset_id,resource_id_year,suffix_year)
        
        current_month = int(self.get_current_date().strftime('%m'))
        current_year = int(self.get_current_date().strftime('%Y'))
        if not current_month == month_previous_update:
            resource_id_year = self._get_ressource_id(headers,api,dataset_id,year_previous_update)
            resource_id_year = self._upload_file(headers,api,dataset_id,resource_id_year,year_previous_update)
            
            config["resource_month"] = current_month
            config["resource_year"] = current_year
            
            with open(config_file, "w") as file:
                json.dump(config, file, indent=4)

    @StepMngmt().decorator(Step.EXPORT,None)
    def export(self,local:bool):
        # if df is empty then return
        if len(self.df) == 0:
            logging.warning("Le DataFrame global est vide, impossible d'exporter")
            return
        """Étape exportation des résultats au format json et xml dans le dossier /results"""
        logging.info("--- ÉTAPE EXPORTATION")
        logging.info("Début de l'étape Exportation en JSON")

        # Creation du sous répertoire "results"
        os.makedirs("results", exist_ok=True)

        ## Exportation des données dans des fichiers mensuels 
        self._nan_correction_dico(self.df)

        for year_month, group in self.df.groupby('tmp__annee_mois'):
            output_file = f"results/decp-{year_month}.json"
            marches = group[group['_type'].str.contains("Marché")]
            concessions = group[~group['_type'].str.contains("Marché")]
            marches_json = marches.to_dict(orient='records')
            concessions_json = concessions.to_dict(orient='records')
            logging.info(f"Ajout de {len(marches_json)} marchés et {len(concessions_json)} concessions au fichier results/decp-{year_month}")
            self._merge_in_file(output_file,{'marches': marches_json, 'concessions': concessions_json})
            output_file_year = output_file[0:17] + '.json'
            self._merge_in_file(output_file_year,{'marches': marches_json, 'concessions': concessions_json})


        dico = {'marches': [{k: v for k, v in m.items() if str(v) != 'nan'}
                            for m in self.df.to_dict(orient='records')]}
        
        #Création du fichier daily
        path_result_daily = "results/decp-daily.json"

        """
        #Création des chemins des fichiers mensuel et annuel(global)
        suffix_year = self.get_current_date().strftime('%Y')
        path_result = f"results/decp-{suffix_year}.json"
        
        config_file = "config.json"
        # read info from config.son
        with open(config_file, "r") as f:
            config = json.load(f)

        # Cas du changement de mois 
        # prenant en compte le cas de l'inactivité de l'application pendant plusieurs jours 
        if ((self.get_current_date().month)!=config["resource_month"]) and config["resource_month"] is not None:
            logging.info("Finalisation du fichier du mois précédent")
            # On récupère la date du mois précédent  
            # pour pouvoir retrouver le nom du fichier contenant les marchés et concession du mois précédent.
            a_month_ago = self.get_current_date() - relativedelta(months=1)
            suffix_month_ago = a_month_ago.strftime('%Y-%m')
            path_result_last_month = f"results/decp-{suffix_month_ago}.json"


            # Si l'execution de l'application ne s'est pas faite depuis plusieurs jours 
            # il faut scinder le dico en 2: les données du mois précédent et celle du mois en cours
            #self.df['datePublicationDonnees_comp'] = pd.to_datetime(self.df['datePublicationDonnees'],format='mixed',errors='coerce')
            #self.df['dateModifications_tmp'] = self.df['modifications'].apply(self.extract_publication_dates)
            #self.df['dateModifications_comp'] = self.df['dateModifications_tmp'].apply(lambda x: max(pd.to_datetime(x, errors='coerce')) if x else None)
            #self.df['datePublication__max'] = self.df[['datePublicationDonnees_comp', 'dateModifications_comp']].max(axis=1)
            #del self.df['datePublicationDonnees_comp']
            #del self.df['dateModifications_tmp']
            #del self.df['dateModifications_comp']
            self._add_meta_modifications(self.df,pd.DataFrame(),False)

            month_first_day = self.get_month_first_day(self.get_current_date())
            df_prev_month = self.df[(self.df['datePublication__max'] < month_first_day) | self.df['datePublication__max'].isna()]
            df_curr_month = self.df[(self.df['datePublication__max'] >= month_first_day)]
            del df_prev_month['datePublication__max']
            del df_curr_month['datePublication__max']
            
            dico_curr_month = {'marches': [{k: v for k, v in m.items() if str(v) != 'nan'}
                                for m in df_curr_month.to_dict(orient='records')]}
            # Modification des champs titulaires et modifications
            #dico = self.dico_modifications(dico)

            if not df_prev_month.empty:
                dico_prev_month = {'marches': [{k: v for k, v in m.items() if str(v) != 'nan'}
                                    for m in df_prev_month.to_dict(orient='records')]}
                # On ajoute les nouvelles données (données journalières) au fichier de l'année en cours
                dico_nouveau = self._merge_in_file(path_result_last_month,dico_prev_month)

                self._merge_in_file(path_result,dico_nouveau)



                
            
            dico_ancien = self.file_load(path_result)
            dico_nouveau = self.file_load(path_result_last_month)
            if not df_prev_month.empty:
                logging.info(f"Mise à jour du fichier {path_result_last_month}")
                dico_prev_month = {'marches': [{k: v for k, v in m.items() if str(v) != 'nan'}
                                    for m in df_prev_month.to_dict(orient='records')]}
                # dico_prev_month = self.dico_modifications(dico_prev_month)
                dico_nouveau = self._dico_merge(dico_nouveau,dico_prev_month)
                df_prev_month = pd.DataFrame.from_dict(dico_nouveau)
                df_prev_month = self.dedoublonnage(df_prev_month)
                dico_nouveau = self._nan_correction_dico(df_prev_month)
                try:
                    self.file_dump(path_result_last_month,dico_nouveau) 
                except:
                    logging.error(f"Erreur d'écriture dans le fichier {path_result_last_month}")
            dico_global = self._dico_merge(dico_ancien,dico_nouveau)
            #On transforme les dictionnaires en dataframes pour les dédoublonner
            if dico_global!={}:
                df_global = pd.DataFrame.from_dict(dico_global)
                df_global = self.dedoublonnage(df_global)
                dico_final = self._nan_correction_dico(df_global)
                try:
                    self.file_dump(path_result,dico_final) 
                except:
                    logging.error(f"Erreur d'écriture dans le fichier {path_result}")
                    #Il faudra publier le fichier backup
                self.file_dump(path_result_backup,dico_final)
            elif dico_nouveau !={} :
                try:
                    self.file_dump(path_result,dico_nouveau)
                except:
                    logging.error("Erreur d'écriture dans le fichier {path_result}")
                #self.file_dump(path_result_backup,dico_nouveau)
            




            self.file_dump(path_result_month,dico_curr_month)
        else:
            # On ajoute les nouvelles données au fichier du mois en cours
            self._merge_in_file(path_result_month,dico)
        """
        # Sauvegarde des données journalières
        self.file_dump(path_result_daily,dico)

        logging.info("Exportation JSON OK")
    
        
    def file_load(self,path:str) ->dict:
        """
        La fonction file_load essaie de lire un fichier JSON et de le convertir en dictionnaire.
        Si le fichier est vide ou invalide, on retourne alors un dictionnaire vide. 
        Pour toute autre erreur, elle enregistre un message d'erreur et renvoie également dico.
        
        Args:

            path: chemin du fichier d'où l'on récupère les données

        """
        nb_marches = 0
        nb_concessions = 0
        if(os.path.exists(path)):
            #On essaye de récupérer le fichier grâce au chemein contenu dans la variable path
            try:
                with open(path, encoding="utf-8") as f:
                    dico = json.load(f)
                nb_marches = len(dico['marches'])
                logging.info(f"Chargement de {nb_marches} marches {nb_concessions} concessions du fichier json {path}")
            #Cas où le fichier est vide
            except ValueError:
                dico={}
            #Autres cas où le fichier est invalide
            except Exception as err:
                logging.error(f"Exception lors du chargement du fichier json {path} - {err}")
                dico={}
        else:
            logging.warning("le fichier {path} est vide")
            dico={}
        return dico
    
    def file_dump(self,path: str,dico: dict, is_for_data_gouv=False) -> None:
        """
        La fonction file_dump permet d'écrire un dictionnaire dans un fichier JSON.
        Elle permet de plus d'afficher la taille du fichier traité.

        Args:

            path: chemin du fichier d'où l'on récupère les données
            dico: dictionnaire contenant les données qui vont être écrite dans le fichier  
        """
        logging.info(f"Saving file {path}")
        if is_for_data_gouv:
            dico = self._dico_purge(dico)
        else:
            dico_ref = dico
            dico = self._dico_restore_nc(dico)

        try:
            with open(path, 'w', encoding="utf-8") as f:
                json.dump(dico, f, indent=2, ensure_ascii=False)
            
            if not is_for_data_gouv:
                self.file_dump(path.replace(".json","_data_gouv.json"),dico_ref,True)

        except Exception as err:
            logging.error(f"Exception lors de l'ecriture du fichier json {path} - {err}")
        json_size = os.path.getsize(path)
        logging.info(f"Taille de {path} : {json_size}")


    def _dico_restore_nc(self,dico_in:dict) -> dict: 
        """
        La fonction _dico_restore_nc modifie les valeurs des données du dictionnaire 
        pour restorer les valeurs NC  

        Args:

            dico: dictionnaire où on effectue les changements

        """        
        marches = []
        if 'marches' in dico_in:
            for marche_in in dico_in['marches']:
                marche = marche_in.copy()
                if 'backup__montant' in marche_in:
                    marche['montant'] = marche['backup__montant']
                if 'backup__datePublicationDonnees' in marche_in:
                    marche['datePublicationDonnees'] = marche['backup__datePublicationDonnees']
                    
                self._restore_attributes_by_prefix(marche,'backup__')
                self._restore_attributes_by_prefix_in_node(marche,'actesSousTraitance','acteSousTraitance')

                marches.append(marche)
            
        if 'concessions' in dico_in:
            for marche_in in dico_in['concessions']:
                marche = marche_in.copy()
                if 'backup__montant' in marche_in:
                    marche['montant'] = marche['backup__montant']
                self._restore_attributes_by_prefix(marche,'backup__')
                self._restore_attributes_by_prefix_in_node(marche,'actesSousTraitance','acteSousTraitance')

                marches.append(marche)

        return {
                'marches': marches 
        }
    

    def _dico_purge(self,dico_in:dict) -> dict: 
        """
        La fonction _dico_purge modifie le type des données et certains attributs du dictionnaire 
        afin de produire en sortie des fichiers json au format valide 

        Args:

            dico: dictionnaire où on effectue les changements

        """
        def delete_attributes_by_prefix(marche,prefix):
            keys_to_delete = [clé for clé in marche.keys() if clé.startswith(prefix)]
            for key in keys_to_delete:
                del marche[key]
         
        marches = []
        concessions = []
        for marche_in in dico_in['marches']:
            marche = marche_in.copy()

            delete_attributes_by_prefix(marche,'report__')
            delete_attributes_by_prefix(marche,'tmp__')

            if 'report__file' in marche:
                del marche["report__file"]
            if 'report__nbtotal' in marche:
                del marche["report__nbtotal"]
            if 'report__error' in marche:
                del marche["report__error"]
            if 'report__path' in marche:
                del marche["report__path"]
            if 'report__position' in marche:
                del marche["report__position"]
            if 'idAccordCadre' in marche and (marche['idAccordCadre'] == '' or pd.isna(marche['idAccordCadre'])):
                del marche["idAccordCadre"]
            if 'origineUE' in marche and (marche['origineUE'] == '' or pd.isna(marche['origineUE'])):
                del marche["origineUE"]
            if 'origineFrance' in marche and (marche['origineFrance'] == '' or pd.isna(marche['origineFrance'])):
                del marche["origineFrance"]
            if 'tauxAvance' in marche and (marche['tauxAvance'] == '' or pd.isna(marche['tauxAvance'])):
                del marche["tauxAvance"]
            self.force_int_or_nc('dureeMois',marche)
            self.force_int_or_nc('offresRecues',marche)
            self.force_bool_or_nc('marcheInnovant',marche)
            self.force_bool_or_nc('attributionAvance',marche)
            self.force_bool_or_nc('sousTraitanceDeclaree',marche)

            if 'modifications' in marche and isinstance(marche['modifications'],list) and len(marche['modifications'])==0:
                del marche['modifications']                
            if 'actesSousTraitance' in marche \
                and ((isinstance(marche['actesSousTraitance'],list) and len(marche['actesSousTraitance'])==0) \
                    or (isinstance(marche['actesSousTraitance'],str) and marche['actesSousTraitance']=='') or \
                    (not isinstance(marche['actesSousTraitance'],list) and pd.isna(marche['actesSousTraitance']))):
                del marche['actesSousTraitance']  
            if 'modificationsActesSousTraitance' in marche \
                and ((isinstance(marche['modificationsActesSousTraitance'],list) and len(marche['modificationsActesSousTraitance'])==0) \
                    or (isinstance(marche['modificationsActesSousTraitance'],str) and marche['modificationsActesSousTraitance']=='') or \
                    (not isinstance(marche['modificationsActesSousTraitance'],list) and pd.isna(marche['modificationsActesSousTraitance']))):
                del marche['modificationsActesSousTraitance']  

            if 'backup__montant' in marche_in:
                marche['montant'] = marche['backup__montant']
                del marche['backup__montant']
            if 'backup__datePublicationDonnees' in marche_in:
                marche['datePublicationDonnees'] = marche['backup__datePublicationDonnees']
                del marche['backup__datePublicationDonnees']
            
            self._restore_attributes_by_prefix(marche,'backup__')
            self._restore_attributes_by_prefix_in_node(marche,'actesSousTraitance','acteSousTraitance')

            if '_type' in marche and marche['_type'] != 'Marché':
                if 'montant' in marche:
                    del marche["montant"]
                if 'offresRecues' in marche:
                    del marche["offresRecues"]
                if '_type' in marche:
                    del marche["_type"]
                concessions.append(marche)
            else:
                if 'valeurGlobale' in marche:
                    del marche["valeurGlobale"]
                if 'dateSignature' in marche:
                    del marche["dateSignature"]
                if 'donneesExecution' in marche:
                    del marche["donneesExecution"]
                if 'concessionnaires' in marche:
                    del marche["concessionnaires"]
                if 'autoriteConcedante' in marche:
                    del marche["autoriteConcedante"]
                if 'dateDebutExecution' in marche:
                    del marche["dateDebutExecution"]
                if 'montantSubventionPublique' in marche:
                    del marche["montantSubventionPublique"]
                if '_type' in marche:
                    del marche["_type"]
                marches.append(marche)
            
        return {
                'marches': {
                    'marche': marches,
                    'contrat-concession': concessions
                }
        }


    def dico_exists_node_in_node(self,dico,parent_node, child_node):
        if parent_node in dico:
            parent_dico = dico[parent_node]
            
            # Vérifie si le contenu du noeud parent_node est un dictionnaire
            if isinstance(parent_dico, dict):
                # Vérifie si "marche" existe dans le dictionnaire "marches"
                return child_node in parent_dico
            
            # Vérifie si le contenu du noeud parent_node est une liste
            elif isinstance(parent_dico, list):
                for element in parent_dico:
                    # Vérifie si l'élément est un dictionnaire et si le noeud child_node y existe
                    if isinstance(element, dict) and child_node in element:
                        return True
        return False    

    # Vérifie si le noeud "marche" existe à l'intérieur du moeud "marches" dans le dictionnaire
    def dico_exists_marche_in_marches(self,dico):
        return self.dico_exists_node_in_node(dico,'marches','marche')

    def validate_json(self,jsonPath,jsonData:dict,jsonScheme:dict) -> bool:
        """
        Fonction vérifiant si le fichier jsn "jsonData" respecte
        le schéma spécifié dans le  schéma en paramètre "jsonScheme". 

        Args: 

            jsonData: dictionnaire qui va être vérifié par le validateur
            jsonScheme: schéma à respecter

        """
        errors_json = []  # Liste pour stocker les erreurs
    
        validator = Draft7Validator(jsonScheme)
        for error in sorted(validator.iter_errors(jsonData), key=lambda e: e.path):
            error_path = list(error.path)
            error_message = error.message
            errors_json.append(f"Path: {error_path} -- Message: {error_message}")
        
        if errors_json:
            with open('erreur.log.txt', 'w') as error_file:
                error_file.write("\n")
                error_file.write(jsonPath + "\n")
                for error in errors_json:
                    error_file.write(error + "\n")
            logging.info(f"{len(errors_json)} erreurs de validation ont été sauvegardées dans erreur.log.txt.")
            return False
        else:
            logging.info("Le fichier JSON est valide.")
            return True     

    def _dico_merge(self,dico_ancien: dict,dico_nouveau: dict) -> dict:
        """"
        La fonction dico_merge permet de fusionner deux dictionnaires passés en paramètres
        Elle gère de plus les cas où un des deux dictionnaires ou les deux dictionnaires sont vides.

        Args:

            dico_ancien: dictionnaire contenant les données du gros programme decp_2022
            dico_nouveau: dictionnaire contenant les données du fichier decp du mois précédent
        """
        #On affecte à la variable dico_global les dictionnaires non vides
        if(dico_ancien=={}) and (dico_nouveau != {}):
            dico_global = dico_nouveau['marches']
        elif(dico_nouveau=={}) and (dico_ancien!={}):
            dico_global = dico_ancien['marches']
        elif(dico_nouveau=={}) and (dico_ancien=={}):
            logging.info(f"Les fichiers decp_2022 et decp_{self.get_current_date().year}_{self.get_current_date().month-1} sont vides")
            dico_global={}
        else:
            #dico_global récupère l'ensemble des marchés et concessions des deux fichiers
            dico_global = dico_ancien['marches'] + dico_nouveau['marches']
        return dico_global
    
    def _nan_correction_dico(self,df:pd.DataFrame) -> dict:
        """
        La fonction nan_correction remplit les valeurs manquantes du dataframe passé en paramètre 
        en fonction du type de données de chaque colonne.
        Elle convertit enfin le dataFrame en un dictionnaire de listes de dictionnaires avant de retourner le dictionnaire.

        Args:

            df: dataframe que l'on va corriger puis transformer en dictionnaire
        """
        #On transforme les NaN en éléments vides pour éviter de futurs erreurs 
        for i in df.columns:
            if df[i].dtypes == 'float64': 
                df.fillna({i:0.0},inplace=True) 
            elif df[i].dtypes == 'int32':
                df.fillna({i:0},inplace=True) 
            elif df[i].dtypes == 'object':
                df.astype(str).fillna({i:""},inplace=False)
            
        dico_final = {'marches': df.to_dict(orient='records')}
        return dico_final
                

    def upload_s3(self):
        """
        Cette fonction exporte decpv2 sur le S3 decp.
        """
        ACCESS_KEY = os.environ.get("ACCESS_KEY")
        SECRET_KEY = os.environ.get("SECRET_KEY")
        ENDPOINT_S3 = os.environ.get("ENDPOINT_S3")
        BUCKET_NAME = os.environ.get("BUCKET_NAME")
        REGION_NAME = os.environ.get("REGION_NAME")
        session = boto3.session.Session()
        client = session.client(
            service_name='s3',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=REGION_NAME,
            endpoint_url="https://"+str(ENDPOINT_S3)
        )
        client.upload_file(os.path.join("results", f"decp_{self.data_format}.json"), BUCKET_NAME, f"data/decp_{self.data_format}.json")


    @StepMngmt().decorator(Step.UPLOAD_DATA_GOUV,None)
    def upload_datagouv(self):
        """
        Cette fonction exporte les données journalières, 
        annuelles (decp-<Annee>.json) et mensuelles (decp-<Annee>-<mois>.json) sur data.gouv.fr
        Les données exportées sont une copie des données de travail purgées afin de répondre au schéma de validation
        """
        config_file = "config.json"
        # read info from config.son
        with open(config_file, "r") as f:
                config = json.load(f)
                api = config["url_api"]
                dataset_id = config["dataset_id"]
                data_gouv_api_key = config["data_gouv_api_key"]

        headers = {
            "X-API-KEY": data_gouv_api_key
        }

        suffix_month = self.get_current_date().strftime('%Y-%m')

        # Nous avons changé de mois, on doit donc mettre à jour le fichier decp_<Annee> sur datagouv 
        # et créer la ressource pour le fichier mensuel et l'uploader
        if ((self.get_current_date().month)!=config["resource_month"]) and config["resource_month"] is not None:
            a_month_ago = self.get_current_date() - relativedelta(months=1)
            suffix_prev_month = a_month_ago.strftime('%Y-%m')
            resource_id_prev_month = config["resource_id_month"]
            _ = self._upload_file(headers,api,dataset_id,resource_id_prev_month,suffix_prev_month)

            resource_id_global = config["resource_id_global"]
            suffix_year = config["resource_year"]
            resource_id_global = self._upload_file(headers,api,dataset_id,resource_id_global,suffix_year)

            resource_id_month = self._upload_file(headers,api,dataset_id,None,suffix_month)
            
            with open(config_file, "r") as file:
                data = json.load(file)

            data['resource_id_month'] = resource_id_month
            data['resource_month'] = self.get_current_date().month
            data['resource_id_global'] = resource_id_global
            if self.get_current_date().month == 1:
                data['resource_id_global'] = None
                data['resource_year'] = self.get_current_date().year

            with open(config_file, "w") as file:
                json.dump(data, file, indent=4)
        #Cas quand le mois n'a pas changé depuis la dernière exécution (ou lors de la première execution)
        else:
            result_resource_id = self._upload_file(headers,api,dataset_id,config["resource_id_month"],suffix_month)

            if config["resource_id_month"] is None:
                config["resource_id_month"] = result_resource_id
            if config["resource_month"] is None:
                config["resource_month"] = self.get_current_date().month
                config["resource_year"] = self.get_current_date().year
            with open(config_file, "w") as file:
                json.dump(config, file, indent=4) 

    def _get_ressource_id(self,headers,api,dataset_id,suffix:str) -> str:
        resource_id = None

        resource_file = f"decp-{suffix}.json"

        url = f"{api}/datasets/{dataset_id}/"

        response = requests.get(url, headers)

        if response.status_code == 200:
            # Récupérer la réponse en JSON
            response_json = response.json()

            with open('result_trace.txt', 'w') as file:
                #file.write(response.text)
                json.dump(response_json, file, indent=4)
            
            resources = response_json['resources']
            for resource in resources:
                if resource['title'] == resource_file:
                    resource_id = resource['id']
                    
        return resource_id


    def _upload_file(self,headers,api,dataset_id,resource_id:str,suffix:str) -> str:
        if resource_id is None:
            url = f"{api}/datasets/{dataset_id}/upload/"
        else:
            url = f"{api}/datasets/{dataset_id}/resources/{resource_id}/upload/"
        
        try:
            # On charge le fichier annuel existant
            file = {
                "file": (f"decp-{suffix}.json", open(f"results/decp-{suffix}_data_gouv.json", "rb"))
            }
        except Exception:
            file = {
                "file": (f"decp-{suffix}.json", None)
            }

        response = requests.post(url, headers=headers, files=file)
        if response.status_code==200:
            logging.info(f"Upload du fichier decp-{suffix} réussi")
        elif response.status_code==201:
                logging.info(f"Création du fichier decp-{suffix}.json réussie")
                data = response.json()
                resource_id = data['id']
        else:
            logging.error(f'Error {response.status_code} uploading file decp-{suffix}.json')
        
        return resource_id

    def _restore_attributes_by_prefix(self,marche,prefix):
        keys_to_delete = [clé for clé in marche.keys() if clé.startswith(prefix)]
        for key in keys_to_delete:
            if marche[key] == 'NC':
                marche[key[len(prefix):]] = marche[key]
            if pd.isna(marche[key]):
                marche[key[len(prefix):]] = marche[key]
            if pd.isna(marche[key]):
                marche[key[len(prefix):]] = marche[key]
            del marche[key]

    def _restore_attributes_by_prefix_in_node(self,marche,node_parent:str,node_child:str):
        if node_parent in marche and isinstance(marche[node_parent],list):
            for element in marche[node_parent]:
                if node_child in element and isinstance(element[node_child],dict):
                    self._restore_attributes_by_prefix(element[node_child],'backup__')


    
    def force_int_or_nc(self,cle:str,marche:dict):
        if cle in marche.keys() and marche[cle] != 'NC':
            try:
                # Convertir la valeur en entier
                marche[cle] = int(marche[cle])
            except ValueError:
                logging.warning(f"Erreur : la valeur de la clé '{cle}' ne peut pas être convertie en entier.")
            except TypeError:
                logging.warning(f"Erreur : la valeur de la clé '{cle}' est de type incompatible pour la conversion.")

    def force_bool_or_nc(self,cle:str,marche:dict):
        if cle in marche.keys() and marche[cle] != 'NC':
            if ("true"==marche[cle]) or ("oui"==marche[cle]) or ("1"==marche[cle]):
                marche[cle] = True
            elif ("false"==marche[cle]) or ("non"==marche[cle]) or ("0"==marche[cle]):
                marche[cle] = False

    def get_current_date(self) -> datetime:
        # for test: return datetime.strptime("2025-03-01", "%Y-%m-%d")
        return datetime.now()

    def get_month_first_day(self,date:datetime) -> datetime:
        return date.replace(day=1)
        
    def save_report(self):
        self.report.save()

