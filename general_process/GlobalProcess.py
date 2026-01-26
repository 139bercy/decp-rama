from database.DbDecp import DbDecp
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
from utils.UtilsJson import UtilsJson

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

    GLOBAL_RESULT_PATH = "results/decp-global.json"

    date_pattern = r'\d{4}-\d{2}-\d{2}'
    date_pattern_inv = r'\d{2}.\d{2}.\d{4}'

    #Critères de dédoublonnage
    feature_doublons_marche = ["id", "acheteur", "titulaires", "dateNotification", "montant"] 
    feature_doublons_concession = [ "id", "autoriteConcedante", "concessionnaires", "dateDebutExecution", "valeurGlobale"]
    feature_doublons_marche_order = ["id", "acheteur", "titulaires", "dateNotification", "montant",'tmp__max_date'] 
    feature_doublons_concession_order = [ "id", "autoriteConcedante", "concessionnaires", "dateDebutExecution", "valeurGlobale",'tmp__max_date']

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
            self.df = pd.concat(self.dataframes, ignore_index=True, copy=True)
            self.df = self.df.reset_index(drop=True)
            logging.info("Merge OK")
            del self.dataframes
        else:
            logging.info("Aucune données à traiter")
        
        #print(self.df['tmp__max_date'].apply(lambda x: type(x)).value_counts())
        #mask = self.df['tmp__max_date'].apply(lambda x: isinstance(x, (tuple, list)))
        #print(self.df.loc[mask, ['tmp__max_date']].head(10))
        #mask2 = df['tmp__max_date'].apply(lambda x: isinstance(x, str))
        #print(self.df.loc[mask2, ['tmp__max_date']].head(10))
        
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

        #if 'source' in self.df.columns:
        #    self.df.sort_values(by="source", inplace=True) 
        #else : 
        #    self.df['source'] = pd.NA
        self.dedoublonnage(self.df,True)
        logging.info("Suppression OK")
        logging.info(f"Nombre de marchés dans Df après suppression des doublons sur les nouvelles données : {len(self.df)}")

    def dedoublonnage(self,df: pd.DataFrame, add_report=True) -> pd.DataFrame:
        nb_duplicated_marches = 0
        nb_duplicated_concessions = 0
        
        #TODO type
        #df['dureeMois'] = pd.to_numeric(df['dureeMois'].astype(str).str.replace(',', '.', regex=False),
        #                        errors='coerce').astype('Int64')
        #print(df['tmp__max_date'].apply(lambda x: type(x)).value_counts())
        #mask = df['tmp__max_date'].apply(lambda x: isinstance(x, (tuple, list)))
        #print(df.loc[mask, ['tmp__max_date']].head(10))

        df.sort_values(
            by=['tmp__max_date'],
            ascending=[False],  # max_date décroissant -> conserve la plus récente
            inplace=True,
            kind='mergesort'  # tri stable
        )
        
        mask = df['_type'].eq('Marché')
        to_drop = df.loc[mask, self.feature_doublons_marche].astype(str).duplicated(keep='last')
        nb_duplicated_marches = df.loc[mask, self.feature_doublons_marche].astype(str).duplicated(keep='last').sum()
        df.drop(index=to_drop[to_drop].index, inplace=True)
        df.reset_index(drop=True, inplace=True)

        logging.info(f"Nombre de marché en doublon {nb_duplicated_marches}")

        mask = df['_type'].ne('Marché')
        columns_compare = [c for c in self.feature_doublons_concession if c in df.columns] #
        to_drop = df.loc[mask, columns_compare].astype(str).duplicated(keep='last')
        nb_duplicated_concessions = df.loc[mask, columns_compare].astype(str).duplicated(keep='last').sum()
        df.drop(index=to_drop[to_drop].index, inplace=True)
        df.reset_index(drop=True, inplace=True)

        logging.info(f"Nombre de concession en doublon {nb_duplicated_concessions}")
        logging.info(f"Nombre de marchés / concession après dédoublonnage: {len(df)}")
            
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
            if 'titulaires' in df_marches.columns:
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
            
    def _merge_in_file(self, file_path:str, df_new:pd.DataFrame):#dico:dict) -> dict:
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
                df_new = self.dedoublonnage(df_new)
                dico = {'marches': [{k: v for k, v in m.items() if str(v) != 'nan'}
                    for m in df_new.to_dict(orient='records')]}
                self.file_dump(file_path,dico)
            else:
                dico_global = dico_file['marches']
                #On transforme le dictionnaires en dataframes pour dédoublonner les nouvelles données
                df_global = pd.DataFrame.from_dict(dico_global)
                
                # On complete les colonnes backup  pour les marches ajoutés depuis l'export qui ne sont pas passé par fix
                keys_to_backup = ['offresRecues','marcheInnovant','attributionAvance','sousTraitanceDeclaree','dureeMois','variationPrix', 'montant', 'valeurGlobale']
                for key in keys_to_backup:
                    if key in df_global.columns:
                        df_global[f'backup__{key}'] = df_global[key]

                # On complete la colonne backup montant pour les marches ajoutés depuis l'export qui ne sont pas passé par fix
                if "montant" in df_global.columns and 'backup__montant' in df_global.columns \
                    and df_global.loc[df_global['_type'] == 'Marché', 'backup__montant'].isna().any():
                    df_global.loc[(df_global['backup__montant'].isna()) & (df_global['_type'] == 'Marché'), 'backup__montant'] = df_global['montant']
                    df_global.loc[df_global['_type'] == 'Marché', 'montant'] = df_global.loc[df_global['_type'] == 'Marché', 'montant'].apply(lambda x: int(x) if pd.notna(x) else np.nan)
                
                self._nan_correction_dico(df_global)
                
                # on ajoute les nouvelles données au données extraite du fichier pour pouvoir ensuite faire le dédoublonnage sur tout le fichier
                df_global = pd.concat([df_global, df_new], ignore_index=True)

                df_global = self.dedoublonnage(df_global)
                
                dico_final = {'marches': [{k: v for k, v in m.items() if str(v) != 'nan'}
                    for m in df_global.to_dict(orient='records')]}
                
                self.file_dump(file_path,dico_final)                
        else:
            # Le fichier n'existait pas on ajoute le nouveau dictionnaire dedans
            df_new = self.dedoublonnage(df_new)
            dico = {'marches': [{k: v for k, v in m.items() if str(v) != 'nan'}
                for m in df_new.to_dict(orient='records')]}
            self.file_dump(file_path,dico)
    
    def _make_copy_for_data_gouv(self,suffix):
        file_path = f"results/decp-{suffix}.json"
        file_path_copy = f"results/decp-{suffix}_data_gouv.json"
        if os.path.exists(file_path):
            dico = self.file_load(file_path)
            if 'marches' in dico:
                keys_to_backup = ['offresRecues','marcheInnovant','attributionAvance','sousTraitanceDeclaree','dureeMois','variationPrix','montant']
                for el in dico['marches']:
                    for key in keys_to_backup:
                        if key in el:
                            el[f'backup__{key}'] = el[key]

            dico = self._dico_purge(dico)
            with open(file_path_copy, 'w', encoding="utf-8") as f:
                json.dump(dico, f, indent=2, ensure_ascii=False)

    def upload_on_datagouv(self, suffixes):
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

        if not suffixes[0] == "global":

            for suffix_month in suffixes:
                logging.info(f"Uploading file decp-{suffix_month}_data_gouv.json")
                if(not os.path.exists(f'results/decp-{suffix_month}_data_gouv.json')):
                    self._make_copy_for_data_gouv(suffix_month)
                resource_id_month = self._get_ressource_id(headers,api,dataset_id,suffix_month)
                resource_id_month = self._upload_file(headers,api,dataset_id,resource_id_month,suffix_month)
                suffix_year = suffix_month[0:4]
                if not suffix_year in years:
                    years += [suffix_year]

            for suffix_year in years:
                file_path = f'results/decp-{suffix_year}_data_gouv.json'
                logging.info(f"Uploading file {file_path}")
                if(not os.path.exists(file_path)):
                    self._make_copy_for_data_gouv(suffix_year)
                resource_id_year = self._get_ressource_id(headers,api,dataset_id,suffix_year)
                resource_id_year = self._upload_file(headers,api,dataset_id,resource_id_year,suffix_year)
        else:
            suffix = "global"
            file_path = f'results/global/decp-{suffix}.json'
            logging.info(f"Uploading file {file_path}")
            resource_id = self._get_ressource_id(headers,api,dataset_id,suffix)
            resource_id = self._upload_file(headers,api,dataset_id,resource_id,suffix)
             
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
    def generate_export(self,local:bool):
        # if df is empty then return
        if len(self.df) == 0:
            logging.warning("Le DataFrame global est vide, impossible d'exporter")
            return
        """Étape exportation des résultats au format json et xml dans le dossier /results"""
        logging.info("--- ÉTAPE EXPORTATION")
        logging.info("Début de l'étape Exportation en JSON")

        # Creation du sous répertoire "results"
        os.makedirs("results", exist_ok=True)
        
        # Sauvegarde des données journalières
        # daily replaced by global
        #path_result_daily = "results/decp-daily.json"
        #self.file_dump(path_result_daily,dico)

        ## Exportation des données dans des fichiers mensuels 
        current_year_month  = f"{datetime.now().year}-{datetime.now().month:02d}"
        years = []
        for year_month, group in self.df.groupby('tmp__annee_mois'):
            if year_month <= current_year_month:
                output_file = f"results/decp-{year_month}.json"

                nb_marches = group[group['_type'].str.contains("Marché")].shape[0]
                nb_concessions = group[~group['_type'].str.contains("Marché")].shape[0]
                logging.info(f"Ajout de {nb_marches} marchés et {nb_concessions} concessions au fichier {output_file}")
                
                self._merge_in_file(output_file,group)
                
                suffix_year = year_month[0:4]
                if not suffix_year in years:
                    years += [suffix_year]

        for year in years:
            output_file_year = f"results/decp-{year}.json"
            df_new = pd.DataFrame()
            total_marches = 0
            total_concessions = 0
            for year_month, group in self.df.groupby('tmp__annee_mois'):
                if year == year_month[0:4]:
                    df_new = pd.concat([df_new,group],ignore_index=True)
                    
                    total_marches += group[group['_type'].str.contains("Marché")].shape[0]
                    total_concessions += group[~group['_type'].str.contains("Marché")].shape[0]
                
            logging.info(f"Ajout de {total_marches} marchés et {total_concessions} concessions au fichier {output_file_year} pour l'annee {year}")
            self._merge_in_file(output_file_year,df_new)

        logging.info("Exportation JSON OK")


    def get_suffixes_exported_files(self):
        suffixes = []
        current_year_month = f"{datetime.now().year}-{datetime.now().month:02d}"
        for year_month, group in self.df.groupby('tmp__annee_mois'):
            if year_month <= current_year_month:
                suffixes += [year_month]
        return suffixes


    @StepMngmt().decorator(Step.GLOBAL,None)
    def update_global_data(self):
        logging.info("Update data_out in database")
        
        self._nan_correction_dico(self.df)

        dico = {'marches': [{k: v for k, v in m.items() if str(v) != 'nan'}
                            for m in self.df.to_dict(orient='records')]}
        
        db = DbDecp()
        if 'marches' in dico:
            i=0
            pairs_marches=[]
            for marche in dico['marches']:
                if not marche['db_id']==0:
                    if marche["_type"]=='Marché':
                        pairs_marches.append([int(marche['db_id']),marche])
                        i+=1
                        if i % 10000 == 0:
                            logging.info("Updating 10000 records")
                            db.bulk_update_marche(pairs_marches)
                            pairs_marches = []
                    else:
                        db.update_concession(marche['db_id'],marche)
            if not pairs_marches == []:
                db.bulk_update_marche(pairs_marches)
        logging.info("Data updated in database")
        db.close()
   
    def generate_global(self, generate_month=True):
        logging.info("Launching file generation for augmente data treatment")
        # Creation du sous répertoire "results"
        os.makedirs("results", exist_ok=True)
        os.makedirs("results/global", exist_ok=True)
        db = DbDecp()
        db.extract_json_to_file("results/global/decp-global.json",generate_month)
        db.close()
        logging.info("File generation ok for augmente data treatment")
        
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
                if 'backup__datePublicationDonnees' in marche_in and not pd.isna(marche['backup__datePublicationDonnees']):
                    marche['datePublicationDonnees'] = marche['backup__datePublicationDonnees']
                    
                self._restore_attributes_by_prefix(marche,'backup__')
                self._restore_attributes_by_prefix_in_node(marche,'actesSousTraitance','acteSousTraitance','backup__')

                marches.append(marche)
            
        if 'concessions' in dico_in:
            for marche_in in dico_in['concessions']:
                marche = marche_in.copy()
                if 'backup__montant' in marche_in:
                    marche['montant'] = marche['backup__montant']
                self._restore_attributes_by_prefix(marche,'backup__')
                self._restore_attributes_by_prefix_in_node(marche,'actesSousTraitance','acteSousTraitance','backup__')

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
        
        utilsJson = UtilsJson()

        marches = []
        concessions = []
        for marche_in in dico_in['marches']:
            marche = utilsJson.format_json(marche_in.copy(),False)
            if 'db_id' in marche:
                del marche["db_id"]

            """
            delete_attributes_by_prefix(marche,'report__')
            delete_attributes_by_prefix(marche,'tmp__')

            if 'idAccordCadre' in marche and (marche['idAccordCadre'] == '' or pd.isna(marche['idAccordCadre'])):
                del marche["idAccordCadre"]
            if 'origineUE' in marche and (marche['origineUE'] == '' or pd.isna(marche['origineUE'])):
                del marche["origineUE"]
            if 'origineFrance' in marche and (marche['origineFrance'] == '' or pd.isna(marche['origineFrance'])):
                del marche["origineFrance"]
            if 'tauxAvance' in marche and (marche['tauxAvance'] == '' or pd.isna(marche['tauxAvance'])):
                del marche["tauxAvance"]

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
                if not pd.isnull(marche['backup__datePublicationDonnees']):
                    marche['datePublicationDonnees'] = marche['backup__datePublicationDonnees']
                del marche['backup__datePublicationDonnees']
            
            self._restore_attributes_by_prefix(marche,'backup__')
            self._restore_attributes_by_prefix_in_node(marche,'actesSousTraitance','acteSousTraitance','backup__')

            self.force_int_or_nc('dureeMois',marche)
            self.force_int_or_nc('offresRecues',marche)
            self.force_bool_or_nc('marcheInnovant',marche)
            self.force_bool_or_nc('attributionAvance',marche)
            self.force_bool_or_nc('sousTraitanceDeclaree',marche)
            """
        
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
            self._update_description(headers,api,dataset_id,resource_id_month,suffix_month)
            
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
                
            self.reorder_resources(headers,api,dataset_id)

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

    # Update resource description on data.gouv
    def _update_description(self, headers, api, dataset_id, ressource_id, suffix):
        mois_annee = self._get_mois_annee(suffix)
        description = f"Fichier cumulatif des données essentielles de la commande publique pour {mois_annee}"
        #description = "Fichier des données essentielles de la commande publique au format 2022 pour toutes les années après dédoublonnage"
        data = {
            "format": "json",
            "title": f"decp-{suffix}.json",
            "description": f"{description} ",
            "type": "main",
            "mime": "application/json",
            "url": f"https://www.data.gouv.fr/api/1/datasets/r/{ressource_id}"
        }
        url_update = f"{api}/datasets/{dataset_id}/resources/{ressource_id}/"
        response = requests.put(url_update, headers=headers, json=data)

        logging.INFO(f"Statut de la requête : {response.status_code}")
        logging.info("Réponse : ", response.json())


    # Set all dataSet resources in order on data.gouv
    def reorder_resources(self,headers,api,dataset_id):
        resources = self._get_all_resources(headers,api,dataset_id)
        resources = self._sort_resources(resources)
        self._set_resources_order(headers,api,dataset_id,resources)

    def _get_all_resources(self, headers, api, dataset_id) -> list:
        url = f"{api}/datasets/{dataset_id}/"
        response = requests.get(url, headers=headers)
        print(f"Statut de la requête : {response.status_code}")
        if response.status_code == 200:
            # Récupérer la réponse en JSON
            response_data = response.json()
            return response_data["resources"]
        
        return None
    
    # Sort an array of dataset resources by tihle xith priority to global_decp.jsob
    def _sort_resources(self, resources) -> list:
        # Priorités
        priority_titles = {"decp-global.json", "decp_global.json"}

        # Keep all items whose title matches priority (preserve their original order)
        priority_items = [item for item in resources
            if str(item.get("title", "")).strip().lower() in priority_titles]

        # Remaining items
        others = [item for item in resources
            if str(item.get("title", "")).strip().lower() not in priority_titles]

        # Sort remaining items by title (case-insensitive)
        others.sort(key=lambda x: str(x.get("title", "")).lower())

        # Combined result: priority items first, then sorted others
        resources = priority_items + others

        return resources


    # Order resources of a dataset based on resources sequence in
    def _set_resources_order(self,headers,api,dataset_id,resources):
        url = f"{api}/datasets/{dataset_id}/resources/"
        response = requests.put(url,headers=headers,json=resources)
        print(f"Statut de la requête : {response.status_code}")


    def _get_mois_annee(self,suffix):
        year,month = suffix.split("-")
        date_obj = datetime.datetime(int(year),int(month),1)
        return date_obj.strftime("%B %Y")

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
        
        if suffix=="global":
            file_path = f"results/global/decp-global.json"
        else:
            file_path = f"results/decp-{suffix}_data_gouv.json"
        try:
            # On charge le fichier  existant
            file = {
                "file": (f"decp-{suffix}.json", open(file_path, "rb"))
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
            if not pd.isna(marche[key]):
                marche[key[len(prefix):]] = marche[key]
            del marche[key]

    def _restore_attributes_by_prefix_in_node(self,marche,node_parent:str,node_child:str,prefix:str):
        if node_parent in marche and isinstance(marche[node_parent],list):
            for element in marche[node_parent]:
                if node_child in element and isinstance(element[node_child],dict):
                    self._restore_attributes_by_prefix(element[node_child],prefix)


    
    def force_int_or_nc(self,cle:str,marche:dict):
        if cle in marche.keys() and marche[cle] != 'NC':
            try:
                # Convertir la valeur en entier
                marche[cle] = int(marche[cle])
            except ValueError:
                None
                #logging.warning(f"Erreur : la valeur de la clé '{cle}' ne peut pas être convertie en entier.")
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

