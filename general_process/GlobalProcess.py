import pandas as pd
import json
import os
from datetime import date
import pickle
import logging
import boto3
import requests
import math
import csv
from datetime import datetime
import time
import jsonschema
from jsonschema import validate,Draft7Validator,Draft202012Validator

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
class GlobalProcess:
    """La classe GlobalProcess est une classe qui définit les étapes de traitement une fois toutes
    les étapes pour toutes les sources effectuées : création des variables de la classe (__init__),
    fusion des sources dans un seul DataFrame (merge_all), suppression des doublons (drop_duplicate)
    et l'exportation des données en json pour publication (export)."""

    def __init__(self,data_format="2022"):
        """L'étape __init__ crée les variables associées à la classe GlobalProcess : le DataFrame et
        la liste des dataframes des différentes sources."""
        logging.info("------------------------------GlobalProcess------------------------------")
        self.df = pd.DataFrame()
        self.dataframes = []
        self.data_format = data_format
    
    def merge_all(self) -> None:
        """Étape merge all qui permet la fusion des DataFrames de chacune des sources en un seul."""
        logging.info("  ÉTAPE MERGE ALL")
        logging.info("Début de l'étape Merge des Dataframes")
        if len(self.dataframes)>0:
            self.df = pd.concat(self.dataframes, ignore_index=True)
            self.df = self.df.reset_index(drop=True)
            logging.info("Merge OK")
        else:
            logging.info("Aucune données à traiter")
        logging.info(f"Nombre de marchés dans le DataFrame fusionné après merge : {len(self.df)}")

    def fix_all(self):
        """
        Étape fix all qui permet l'uniformisation du DataFrame.
        """
        logging.info("  ÉTAPE FIX ALL")
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
        # DureeMois doit être un float
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

    def drop_duplicate(self):
        """
        L'étape drop_duplicate supprime les duplicats purs après avoir 
        supprimé les espaces et convertis l'ensemble du DataFrame en string.
        """

        logging.info("  ÉTAPE DROP DUPLICATE")
        # if df is empty then return
        if len(self.df) == 0:
            logging.warning(f"Le DataFrame global est vide, impossible de supprimer les doublons")


        # Séparation des lignes selon la colonne "modifications"
        logging.info("Début de l'étape Suppression des doublons")

        if 'source' in self.df.columns:
            self.df.sort_values(by="source", inplace=True) 
        else : 
            self.df['source'] = pd.NA
        self.dedoublonnage(self.df)
        logging.info("Suppression OK")
        logging.info(f"Nombre de marchés dans Df après suppression des doublons strictes : {len(self.df)}")

    def dedoublonnage(self,df: pd.DataFrame) -> pd.DataFrame:
        if "modifications" in df.columns: # Règles de dédoublonnages diffèrentes. On part du principe qu'en cas 
                                               # de modifications, la colonne "modifications" est créée ou modifiée
            df_modif = df[df.modifications.apply(len)>0]     #lignes avec modifs     
            df_nomodif = df[df.modifications.apply(len)==0]  #lignes sans aucune modif
        else:
            df_modif = pd.DataFrame() 
            df_nomodif = df

        #Critères de dédoublonnage
        feature_doublons_marche = ["id","acheteur", "titulaires", "dateNotification", "montant"] 
        feature_doublons_concession = [ "id", "autoriteConcedante", "concessionnaires", "dateDebutExecution", "valeurGlobale"]
        
        #Séparation des marches et des concessions, suppression des doublons
        df_nomodif_str = df_nomodif.astype(str)
        df_nomodif_marche = df_nomodif_str[df_nomodif_str['_type'].str.contains("Marché")]
        index_to_keep_nomodif = df_nomodif_marche.drop_duplicates(subset=feature_doublons_marche).index.tolist()

        df_nomodif_concession = df_nomodif_str[~df_nomodif_str['_type'].str.contains("Marché")]
        index_to_keep_nomodif += df_nomodif_concession.drop_duplicates(subset=feature_doublons_concession).index.tolist()

        duplicates = df_nomodif_str[df_nomodif_str.duplicated(subset=feature_doublons_marche, keep='first')]
        # jsonfile = {'marches': doublons}
        for i in range (len(duplicates.axes[0])):
            with open(f'bad_results/{duplicates.iloc[i]["source"]}/doublons_{duplicates.iloc[i]["source"]}.csv', 'a', encoding='utf-8') as f:
                doublon = duplicates.iloc[i][:].to_json(orient='records', lines=True, force_ascii=False)
                f.write(doublon)
           
        # doublons = duplicates.to_json(orient='records', lines=True, force_ascii=False)
        # with open('doublons_demantis.json', 'w', encoding='utf-8') as f:
        #     f.write(doublons)

        #Séparation des marches et des concessions, tri selon la date et suppression ses doublons
        if not df_modif.empty:
            df_modif_str  = df_modif.astype(str)     #en str pour réaliser le dédoublonnage
            df_modif_str.sort_values(by=["datePublicationDonnees"], inplace=True)   #Tri
            #print(df_modif['modifications'])

            df_modif_marche = df_modif_str[df_modif_str['_type'].str.contains("Marché")]
            index_to_keep_modif = df_modif_marche.drop_duplicates(subset=feature_doublons_marche,keep='last').index.tolist()  #'last', permet de garder la ligne avec la date est la plus récente

            df_modif_concession = df_modif_str[~df_modif_str['_type'].str.contains("Marché")]
            index_to_keep_modif += df_modif_concession.drop_duplicates(subset=feature_doublons_concession,keep='last').index.tolist()  #on ne garde que que les indexs pour récupérer les lignes qui sont dans df_modif (dont le type est dict)

            df = pd.concat([df_nomodif.loc[index_to_keep_nomodif, :], df_modif.loc[index_to_keep_modif, :]])

        else:
            df = df_nomodif.loc[index_to_keep_nomodif, :]
        df = df.reset_index(drop=True)
        return df


    def export(self):
        # if df is empty then return
        if len(self.df) == 0:
            logging.warning(f"Le DataFrame global est vide, impossible d'exporter")
            return
        """Étape exportation des résultats au format json et xml dans le dossier /results"""
        logging.info("ÉTAPE EXPORTATION")
        logging.info("Début de l'étape Exportation en JSON")
        dico = {'marches': [{k: v for k, v in m.items() if str(v) != 'nan'}
                            for m in self.df.to_dict(orient='records')]}
        with open('dico.pkl', 'wb') as f:
            pickle.dump(dico, f)
        # Modification des champs titulaires et modifications
        dico = self.dico_modifications(dico)
        #Création des chemins des fichiers mensuel et global
        path_result = f"results/decp-{self.data_format}.json"
        path_result_month = f"results/decp-{datetime.now().year}-{datetime.now().month}.json"
        path_result_daily = f"results/decp-daily.json"
        path_result_backup = f"results/ref-decp-{self.data_format}.json"
        os.makedirs("results", exist_ok=True)

        config_file = "config.json"
        # read info from config.son
        with open(config_file, "r") as f:
                config = json.load(f)

        #Cas du premier jour du mois
        if ((datetime.now().month)!=config["resource_month"]):
            #On récupère la date du mois précédent pour pouvoir upload le fichier contenant les marchés du mois précédent.
            path_result_last_month = f"results/decp-{datetime.now().year}-{datetime.now().month - 1}.json"
            if ((datetime.now().month)==1):
                path_result_last_month = f"results/decp-{datetime.now().year - 1}-12.json"

            dico_ancien = self.file_load(path_result)
            dico_nouveau = self.file_load(path_result_last_month)
            dico_global = self.dico_merge(dico_ancien,dico_nouveau)
            #On transforme les dictionnaires en dataframes pour les dédoublonner
            if dico_global!={}:
                df_global = pd.DataFrame.from_dict(dico_global)
                df_global = self.dedoublonnage(df_global)
                dico_final = self.nan_correction(df_global)
                try:
                    self.file_dump(path_result,dico_final) 
                except:
                    logging.error("Erreur d'écriture dans le fichier {path_result}")
                    #Il faudra publier le fichier backup
                self.file_dump(path_result_backup,dico_final)
            elif dico_nouveau !={} :
                try:
                    self.file_dump(path_result,dico_nouveau)
                except:
                    logging.error("Erreur d'écriture dans le fichier {path_result}")
                self.file_dump(path_result_backup,dico_nouveau)
            self.file_dump(path_result_month,dico)
        else:
            #On vérifie que le fichier su mois a bien été crée, sinon on le crée
            if os.path.exists(path_result_month):
                dico_mensuel = self.file_load(path_result_month)
                if dico_mensuel=={}:
                    self.file_dump(path_result_month,dico)
                else:
                    dico_global = dico['marches'] + dico_mensuel['marches']
                    #On transforme les dictionnaires en dataframes pour les dédoublonner
                    df_global = pd.DataFrame.from_dict(dico_global)
                    df_global = self.dedoublonnage(df_global)
                    dico_final = self.nan_correction(df_global)
                    self.file_dump(path_result_month,dico_final)                      
            else:
                self.file_dump(path_result_month,dico)
        self.file_dump(path_result_daily,dico)
        logging.info("Exportation JSON OK")

    def dico_modifications(self,dico:dict) -> dict: 
        """
        La fonction dico_modifications permet de s'assurer que les champs titulaires et modifications
        soient bien remplies afin que nous puissons manipuler le dictionnaire par la suite

        Args:

            dico: dictionnaire où on effectue les changements

        """
        for marche in dico['marches']:
            if 'titulaires' in marche.keys() and marche['titulaires'] is not None and len(
                    marche['titulaires']) > 0 and type( marche['titulaires'])== list:
                modifs = []
                for i in range(len((marche['titulaires']))):
                    if type( marche['titulaires'][i])== dict and 'titulaire' in marche['titulaires'][i].keys():
                        #On affecte au champ titulaires, le champ titulaire
                        if type(marche['titulaires'][i]['titulaire']) == list:
                            modifs += marche['titulaires'][i]['titulaire']
                        else:
                            modifs += [marche['titulaires'][i]['titulaire']]
                marche['titulaires'] = modifs
            elif 'titulaires' in marche.keys() and marche['titulaires'] is not None and len(
                    marche['titulaires']) > 0 and type( marche['titulaires'])== dict:
                marche['titulaires'] = marche['titulaires']['titulaire']
            
            if 'concessionnaires' in marche.keys() and marche['concessionnaires'] is not None and len(
                    marche['concessionnaires']) > 0 and type( marche['concessionnaires'])== list:
                modifs = []
                for i in range(len((marche['concessionnaires']))):
                    if type( marche['concessionnaires'][i])== dict and 'concessionnaire' in marche['concessionnaires'][i].keys():
                        #On affecte au champ concessionnaires, le champ concessionaire
                        if type(marche['concessionnaires'][i]['concessionnaire']) == list:
                            modifs += marche['concessionnaires'][i]['concessionnaire']
                        else:
                            modifs += [marche['concessionnaires'][i]['concessionnaire']]
                marche['concessionnaires'] = modifs
            elif 'concessionnaires' in marche.keys() and marche['concessionnaires'] is not None and len(
                    marche['concessionnaires']) > 0 and type( marche['concessionnaires'])== dict:
                marche['concessionnaires'] = marche['concessionnaires']['concessionnaire']

            if 'donneesExecution' in marche.keys() and marche['donneesExecution'] is not None and len(
                    marche['donneesExecution']) > 0 and type( marche['donneesExecution'])== list:
                modifs = []
                for i in range(len((marche['donneesExecution']))):
                    if type(marche['donneesExecution'][i])==dict and 'donneesAnnuelles' in marche['donneesExecution'][i].keys() :
                        #On affecte au champ donneesExecution, le champ donneesAnnuelles
                        if type(marche['donneesExecution'][i]['donneesAnnuelles']) == list:
                            modifs += marche['donneesExecution'][i]['donneesAnnuelles']
                        else:
                            modifs += [marche['donneesExecution'][i]['donneesAnnuelles']]
                marche['donneesExecution'] = modifs
            elif 'donneesExecution' in marche.keys() and marche['donneesExecution'] is not None and len(
                    marche['donneesExecution']) > 0 and type( marche['donneesExecution'])== dict:
                marche['donneesExecution'] = marche['donneesExecution']['donneesAnnuelles']

            if 'modifications' in marche.keys() and marche['modifications'] is not None and len(
                    marche['modifications']) > 0 and type( marche['modifications'])== list:
                modifs = []
                for i in range(len((marche['modifications']))):
                    if type( marche['modifications'][i])== dict and 'modification' in marche['modifications'][i].keys():
                        #On affecte au champ modifications, le champ modification
                        if type(marche['modifications'][i]['modification']) == list:
                            modifs += marche['modifications'][i]['modification']
                        else:
                            modifs += [marche['modifications'][i]['modification']]
                marche['modifications'] = modifs
            elif 'modifications' in marche.keys() and marche['modifications'] is not None and len(
                    marche['modifications']) > 0 and type( marche['modifications'])== list:
                marche['modifications'] = marche['modifications']['modification']

            if 'modificationsActesSousTraitance' in marche.keys() and marche['modificationsActesSousTraitance'] is not None and len(
                    marche['modificationsActesSousTraitance']) > 0 and type( marche['modificationsActesSousTraitance'])== list:
                modifs = []
                for i in range(len((marche['modificationsActesSousTraitance']))):
                    if type( marche['modificationsActesSousTraitance'][i])== dict and 'modificationActeSousTraitance' in marche['modificationsActesSousTraitance'][i].keys():
                        #On affecte au champ modificationsActesSousTraitance' le champ acteSousTraitance
                        if type(marche['modificationsActesSousTraitance'][i]['modificationActeSousTraitance']) == list:
                            modifs += marche['modificationsActesSousTraitance'][i]['modificationActeSousTraitance']
                        else:
                            modifs += [marche['modificationsActesSousTraitance'][i]['modificationActeSousTraitance']]
                marche['modificationsActesSousTraitance'] = modifs
            elif 'modificationsActesSousTraitance' in marche.keys() and marche['modificationsActesSousTraitance'] is not None and len(
                    marche['modificationsActesSousTraitance']) > 0 and type( marche['modificationsActesSousTraitance'])== list:
                marche['modificationsActesSousTraitance'] = marche['modificationsActesSousTraitance']['modificationActeSousTraitance']

            if 'actesSousTraitance' in marche.keys() and marche['actesSousTraitance'] is not None and len(
                    marche['actesSousTraitance']) > 0 and type( marche['actesSousTraitance'])== list:
                modifs = []
                for i in range(len((marche['actesSousTraitance']))):
                    if type( marche['actesSousTraitance'][i])== dict and 'acteSousTraitance' in marche['actesSousTraitance'][i].keys():
                        #On affecte au champ actesSousTraitance' le champ acteSousTraitance
                        if type(marche['actesSousTraitance'][i]['acteSousTraitance']) == list:
                            modifs += marche['actesSousTraitance'][i]['acteSousTraitance']
                        else:
                            modifs += [marche['actesSousTraitance'][i]['acteSousTraitance']]
                marche['actesSousTraitance'] = modifs
            elif 'actesSousTraitance' in marche.keys() and marche['actesSousTraitance'] is not None and len(
                    marche['actesSousTraitance']) > 0 and type( marche['actesSousTraitance'])== list:
                marche['actesSousTraitance'] = marche['actesSousTraitance']['acteSousTraitance']

        return dico

    def file_load(self,path:str) ->dict:
        """
        La fonction file_load essaie de lire un fichier JSON et de le convertir en dictionnaire.
        Si le fichier est vide ou invalide, on retourne alors un dictionnaire vide. 
        Pour toute autre erreur, elle enregistre un message d'erreur et renvoie également dico.
         
        Args:

            path: chemin du fichier d'où l'on récupère les données

        """
        if(os.path.exists(path)):
            #On essaye de récupérer le fichier grâce au chemein contenu dans la variable path
            try:
                with open(path, encoding="utf-8") as f:
                    dico = json.load(f)
                if self.dico_exists_marche_in_marches(dico):
                    dico['marches'] = dico['marches']['marche']
            #Cas où le fichier est vide
            except ValueError:
                dico={}
            #Autres cas où le fichier est invalide
            except Exception as err:
                logging.error(f"Exception lors du chargement du fichier json {path} - {err}")
                dico={}
        else:
            print("le fichier {path} est vide")
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
        if is_for_data_gouv:
            dico = self.dico_purge(dico)
            if not self.dico_exists_marche_in_marches(dico):
                dico = {
                    'marches': {
                        'marche': dico.get('marches', [])
                    }
                }
        
        try:
            with open(path, 'w', encoding="utf-8") as f:
                json.dump(dico, f, indent=2, ensure_ascii=False)
            
            if not is_for_data_gouv:
                self.file_dump(path.replace(".json","_data_gouv.json"),dico,True)
        except Exception as err:
            logging.error(f"Exception lors de l'ecriture du fichier json {path} - {err}")
        json_size = os.path.getsize(path)
        logging.info(f"Taille de {path} : {json_size}")
    
    def dico_purge(self,dico:dict) -> dict: 
        """
        La fonction dico_transtypage modifie le type des données du dictionnaire afin de produire en sortie
        des fichiers json au format valide 
 
       Args:

            dico: dictionnaire où on effectue les changements

        """
        for marche in dico['marches']:
            if 'source' in marche:
                del marche["source"]
            if 'idAccordCadre' in marche and marche['idAccordCadre'] == '':
                del marche["idAccordCadre"]
            self.force_int('dureeMois',marche)
            self.force_bool('marcheInnovant',marche)
            self.force_bool('attributionAvance',marche)
            self.force_bool('sousTraitanceDeclaree',marche)
            self.force_bool('actesSousTraitance',marche)
            self.force_bool('modificationsActesSousTraitance',marche)

            if 'titulaires' in marche.keys() and marche['titulaires'] is not None and len(
                    marche['titulaires']) == 0 :
                del marche['titulaires']
            elif not self.is_normalized_list_node(marche,'titulaires', 'titulaire'):
                self.normalize_list_node(marche,'titulaires', 'titulaire')

            if 'concessionnaires' in marche.keys() and marche['concessionnaires'] is not None and len(
                    marche['concessionnaires']) > 0 :
                del marche['concessionnaires']
            elif not self.is_normalized_list_node(marche,'concessionnaires', 'concessionnaire'):
                self.normalize_list_node(marche,'concessionnaires', 'concessionnaire')
            
            if 'donneesExecution' in marche.keys() and marche['donneesExecution'] is not None and len(
                    marche['donneesExecution']) == 0 :
                del marche['donneesExecution']
            elif not self.is_normalized_list_node(marche,'donneesExecution', 'donneesAnnuelles'):
                self.normalize_list_node(marche,'donneesExecution', 'donneesAnnuelles')

            if 'modifications' in marche.keys() and marche['modifications'] is not None and len(
                    marche['modifications']) == 0 :
                del marche['modifications']
            elif not self.is_normalized_list_node(marche,'modifications', 'modification'):
                self.normalize_list_node(marche,'modifications', 'modification')

            if 'modificationsActesSousTraitance' in marche.keys() and marche['modificationsActesSousTraitance'] is not None and len(
                    marche['modificationsActesSousTraitance']) == 0 :
                del marche['modificationsActesSousTraitance']
            elif not self.is_normalized_list_node(marche,'modificationsActesSousTraitance', 'modificationActeSousTraitance'):
                self.normalize_list_node(marche,'modificationsActesSousTraitance', 'modificationActeSousTraitance')

            if 'actesSousTraitance' in marche.keys() and marche['actesSousTraitance'] is not None and len(
                    marche['actesSousTraitance']) == 0 :
                del marche['actesSousTraitance']
            elif not self.is_normalized_list_node(marche,'actesSousTraitance', 'acteSousTraitance'):
                self.normalize_list_node(marche,'actesSousTraitance', 'acteSousTraitance')
                
        return dico

    def force_int(self,cle:str,marche:dict):
        if cle in marche.keys() :
            try:
                # Convertir la valeur en entier
                marche[cle] = int(marche[cle])
                #print(f"La durée en mois pour la clé '{cle}' a été convertie en entier.")
            except ValueError:
                print(f"Erreur : la valeur de la clé '{cle}' ne peut pas être convertie en entier.")
            except TypeError:
                print(f"Erreur : la valeur de la clé '{cle}' est de type incompatible pour la conversion.")

    def force_bool(self,cle:str,marche:dict):
        if cle in marche.keys() :
            if ("true"==marche[cle]) or ("oui"==marche[cle]) or ("1"==marche[cle]):
                marche[cle] = True
            elif ("false"==marche[cle]) or ("non"==marche[cle]) or ("0"==marche[cle]):
                marche[cle] = False

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

    def is_normalized_list_node(self, dico, parent_node, child_node):
        if parent_node in dico:
            parent_dico = dico[parent_node]
            if isinstance(parent_dico, list) and len(parent_dico)==1:
                if isinstance(parent_dico[0], dict) and len(parent_dico[0])==1:
                    for element in parent_dico[0]:
                        # Vérifie si l'élément est un dictionnaire et si le noeud child_node y existe
                        if child_node in element: #isinstance(element, dict) and 
                            return True
        return False

    def normalize_list_node(self, marche, parent_node, child_node):
        if parent_node in marche.keys() and marche[parent_node] is not None and len(
            marche[parent_node]) > 0 and isinstance( marche[parent_node],list):
            for i in range(len((marche[parent_node]))):
                if isinstance( marche[parent_node][i],dict) and child_node not in marche[parent_node][i].keys():
                    #On affecte au champ parent_node, le champ child_node
                    marche[parent_node][i] = { child_node: marche[parent_node][i] }

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
        errors = []  # Liste pour stocker les erreurs
    
        validator = Draft7Validator(jsonScheme)
        for error in sorted(validator.iter_errors(jsonData), key=lambda e: e.path):
            error_path = list(error.path)
            error_message = error.message
            errors.append(f"Path: {error_path} -- Message: {error_message}")
        
        if errors:
            with open('erreur.log.txt', 'w') as error_file:
                error_file.write("\n")
                error_file.write(jsonPath + "\n")
                for error in errors:
                    error_file.write(error + "\n")
            print(f"{len(errors)} erreurs de validation ont été sauvegardées dans erreur.log.txt.")
            return False
        else:
            print("Le fichier JSON est valide.")
            return True     

    def json_validation(self,jsonPath,jsonData):
        scheme_path = 'schemes/schema_decp_v2.0.2.json'
        with open(scheme_path, "r",encoding='utf-8') as jsonfile1:
            jsonScheme = json.load(jsonfile1)
            jsonfile1.close
        result = self.validate_json(jsonPath,jsonData,jsonScheme)
        with open("json_validation_errors", "w") as file:
            json.dump(result, file, indent=4)
        return result

    def dico_merge(self,dico_ancien: dict,dico_nouveau: dict) -> dict:
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
            logging.info(f"Les fichiers decp_2022 et decp_{datetime.now().year}_{datetime.now().month-1} sont vides")
            dico_global={}
        else:
            #dico_global récupère l'ensemble des marchés et concessions des deux fichiers
            dico_global = dico_ancien['marches'] + dico_nouveau['marches']
        return dico_global
    
    def nan_correction(self,df:pd.DataFrame) -> dict:
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
                df.fillna({i:""},inplace=True) 
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


    def upload_datagouv(self):
        """
        Cette fonction exporte decp_2019.json or decp_2022.json sur data.gouv.fr
        """
        config_file = "config.json"
        # read info from config.son
        with open(config_file, "r") as f:
                config = json.load(f)
                api = config["url_api"]
                dataset_id = config["dataset_id"]

        headers = {
            "X-API-KEY": "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyIjoiNWYwZjA0NzZkNzk3NDZjYmU5OGNjYmMwIiwidGltZSI6MTY0ODIxNzg4Ny4wOTg0ODE3fQ.d9b1s_170PeSNAOLyqFFOGoW8irEg1nxNxn-fdGCGAckFbVcIxpaxkEm8H-BlI6nLLvWmvS_lL3nKWaHb7Cd9g"
        }
                
        #Nous sommes le premier du mois, on doit donc mettre à jour le fichier decp_2022 sur datagouv et créer la ressource pour le fichier mensuel et l'upload
        if ((datetime.now().month)!=config["resource_month"]):
            resource_id_global = config["resource_id_global"]
            url = f"{api}/datasets/{dataset_id}/resources/{resource_id_global}/upload/"
            url_month = f"{api}/datasets/{dataset_id}/upload/"

            try:
                files = {
                    "file": (f"decp-2022.json", open(f"results/decp-{self.data_format}.json", "rb"))
                }
            except Exception as err:
                files = {
                    "file": (f"decp-2022.json", None)
                }

            try:
                files_month = {
                    "file": (f"decp-{datetime.now().year}-{datetime.now().month}.json", open(f"results/decp-{datetime.now().year}-{datetime.now().month}.json", "rb"))
                }
            except Exception as err:
                files_month = {
                    "file": (f"decp-{datetime.now().year}-{datetime.now().month}.json", None)
                }

            response = requests.post(url, headers=headers, files=files)
            if response.status_code==200:
                logging.info("Upload du fichier decp-2022 réussi")
            else:
                print("Erreur ",response.status_code)
            
            #Nous sommes le premier du mois, on créer le fichier mensuel sur datagouv
            response_month = requests.post(url_month, headers=headers, files=files_month)
            if response_month.status_code==201:
                logging.info(f"Création du fichier decp-{datetime.now().year}-{datetime.now().month}.json réussie")
                data = response_month.json()
                resource_id = data['id']

                with open(config_file, "r") as file:
                    data = json.load(file)

                data['resource_id_month'] = resource_id
                data['resource_month'] = datetime.now().month

                with open(config_file, "w") as file:
                    json.dump(data, file, indent=4)
            else:
                print("Erreur ",response_month.status_code)
        
        #Cas pour tout les autres jours du mois
        else:
            # Preparation des données de l'appel à l'API
            ressource_id_month = config["resource_id_month"]
            url_upload = f"{api}/datasets/{dataset_id}/resources/{ressource_id_month}/upload/"
            files_month = {
                "file": (f"decp-{datetime.now().year}-{datetime.now().month}.json", open(f"results/decp-{datetime.now().year}-{datetime.now().month}_data_gouv.json", "rb"))
            }

            #On met à jour le fichier mensuel sur datagouv
            response = requests.post(url_upload, headers=headers, files=files_month)
            if response.status_code==200:
                logging.info(f"Upload du fichier decp-{datetime.now().year}-{datetime.now().month}.json réussi")
            else:
                print("Erreur ",response.status_code)