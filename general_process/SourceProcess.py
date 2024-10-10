import linecache
from xml.etree import ElementTree
import wget
import os
import json
import xml
import xmlschema
import jsonschema
from jsonschema import validate,Draft7Validator,Draft202012Validator
from dateutil.parser import parse
from lxml import etree
from datetime import datetime
import pandas as pd
import xmltodict
import dict2xml
import re
import logging
import shutil
from urllib.parse import urlparse
import csv
pd.options.mode.chained_assignment = None
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
# pd.set_option('display.width', None)
# pd.set_option('display.max_colwidth', None)

class SourceProcess:
   
    """La classe SourceProcess est une classe abstraite qui sert de parent à chaque classe enfant de
    sources. Elle sert à définir le cas général des étapes de traitement d'une source : création des
    variables de classe (__init__), nettoyage des dossiers de la source (_clean_metadata_folder),
    récupération des URLs (_url_init), get, convert et fix."""

    def __init__(self, key,data_format):
        """L'étape __init__ crée les variables associées à la classe SourceProcess : key, source,
        format, df, title, url, cle_api et metadata.
        
        Args:
            key: clé qui permettant d'identifier la source du processus
            data_format: il s'agit de l'année 2022 ou 2019
        """
        logging.info("  ÉTAPE INIT")
        self.key = key
        self.data_format = data_format
        with open("metadata/metadata.json", 'r+') as f:
            self.metadata = json.load(f)
        self.source = self.metadata[self.key]["code"]
        self.format = self.metadata[self.key]["format"]
        self.url_source = self.metadata[self.key]["url_source"]
        self.df = pd.DataFrame()
        self.title = []
        # Lavage des dossiers de la source
        self._clean_metadata_folder()

        # Récupération des urls
        self._url_init() 

        # Liste des dictionnaires pour l'étape de nettoyage
        self.dico_2022_marche = []
        self.dico_2022_concession = []


    def _clean_metadata_folder(self) -> None:
        """La fonction _clean_metadata_folder permet le nettoyage de /metadata/{self.source}"""
        # Lavage des dossiers dans metadata
        logging.info(f"Début du nettoyage de metadata/{self.source}")
        if os.path.exists(f"metadata/{self.source}"):
            shutil.rmtree(f"metadata/{self.source}")
        logging.info(f"Nettoyage metadata/{self.source} OK")


    def _url_init(self) -> None:
        """_url_init permet la récupération de l'ensemble des url des fichiers qui doivent être
        téléchargés pour une source. Ces urls sont conservés dans self.metadata."""

        logging.info("Initialisation")
        os.makedirs(f"metadata/{self.source}", exist_ok=True) 
        os.makedirs(f"old_metadata/{self.source}", exist_ok=True)
        self.cle_api = self.metadata[self.key]["cle_api"]
        #Liste contenant les urls à partir desquels on télécharge les fichiers
        if self.cle_api==[]:
            self.url = [self.url_source]
        else:
            self.url, self.title = self.create_metadata_file(len(self.cle_api))
           
        logging.info("Initialisation finie")
    

    def create_metadata_file(self,n:int)->tuple[list,list]:
        """
        Fonction réalisant le téléchargement des métadatas, la copie des
        fichiers métadatas et la création des listes contenant les titres
        et les urls des fichiers.
        
        Args: 

            n: nombre de clé api 

        """
        logging.info("Début de la récupération de la liste des url")
        title = []  
        url = []    
        for i in range(n):
            #Téléchargement du fichier de metadata de self.source et création de la 1ere variable json pour la comparaison 
            wget.download(f"https://www.data.gouv.fr/api/1/datasets/{self.cle_api[i]}/",
                            f"metadata/{self.source}/metadata_{self.key}_{i}.json")
            with open(f"metadata/{self.source}/metadata_{self.key}_{i}.json", 'r+') as f:
                ref_json = json.load(f)
            ressources = ref_json["resources"]

            #Creation de la deuxième variable json pour la comparaison si le fichier old_metadata existe
            if os.path.exists(f"old_metadata/{self.source}/old_metadata_{self.key}_{i}.json"):
                with open(f"old_metadata/{self.source}/old_metadata_{self.key}_{i}.json", 'r+') as fl:
                    refjson = json.load(fl)
                old_ressources = refjson["resources"]
            else:
                old_ressources = []
            
            #Création de la liste des urls selon 2 cas: 1er téléchargement, i-nième téléchargement
            if old_ressources==[]:
                url = url + [d["url"] for d in ressources if
                            (d["url"].endswith("xml") or d["url"].endswith("json"))]
                title = title + [d["title"] for d in ressources]
            else: 
                url, title = self.check_date_file(url,title, ressources, old_ressources)
                # print("Les urls dont le contenu a été modifié sont: ", url)

            #Cas où les fichiers old_metadata existent: on écrit dedans à nouveau
            if os.path.exists(f"old_metadata/{self.source}/old_metadata_{self.key}_{i}.json"):
                with open(f"metadata/{self.source}/metadata_{self.key}_{i}.json", 'r') as source_file:
                    contenu = source_file.read()
                with open(f"old_metadata/{self.source}/old_metadata_{self.key}_{i}.json", 'w') as destination_file:
                    destination_file.write(contenu)
            #Cas où les fichiers old_metadata n'existent pas: on fait une copie
            else:
                shutil.copy(f"metadata/{self.source}/metadata_{self.key}_{i}.json",f"old_metadata/{self.source}/old_metadata_{self.key}_{i}.json")
                print(os.listdir(f"old_metadata/{self.source}"))
            logging.info("Récupération des url OK")
            return url,title


    def check_date_file(self,url:list, title: list, new_ressources:dict,old_ressources:dict)->list:
        """
        Fonction vérifiant si la date de dernière modification des fichiers ressources 
        dans les metadatas est strictement antérieure à la date de dernière modification.

        Args:

            url: la liste contenant les liens pour télécharger les fichiers
            new_ressources: dictionnaire correspondant au champ "resources" dans le fichier metadata de la source
            old_ressources: dictionnaire correspondant au champ "resources" dans le fichier old_metadata de la source

        """
        diff = len(new_ressources) - len(old_ressources)
        #On traite d'abord les nouveaux fichiers qui n'ont pas été traité lors d'une précédente exécution
        for i in range(diff):
            print("fichier testé",new_ressources[i]['title'])
            if new_ressources[i]["url"].endswith("xml") or new_ressources[i]["url"].endswith("json"):
                url = url + [new_ressources[i]["url"]] 
                title = title + [new_ressources[i]["title"]]
        #On traite ensuite tout les marchés qui ont déjà été traités lors d'une précédente exécution
        for i in range(diff,len(old_ressources)):
            #condition1 : test si les nouvelles métadonnées sont plus récentes que les anciennes

            condition1=new_ressources[i]["last_modified"]>old_ressources[i-diff]["last_modified"]
            #condition2 : vérification de l'extension
            condition2=(new_ressources[i]["url"].endswith("xml") or new_ressources[i]["url"].endswith("json"))
            if condition1 and condition2 :
                url = url + [new_ressources[i]["url"]] 
                title = title + [new_ressources[i]["title"]]
        print("url",url)
        return url, title         
    
        # for i in range(len(new_ressources)):
        #     #condition1 : test si les nouvelles métadonnées sont plus récentes que les anciennes
        #     condition1=new_ressources[i]["last_modified"]>old_ressources[i]["last_modified"]
        #     #condition2 : vérification de l'extension
        #     condition2=(new_ressources[i]["url"].endswith("xml") or new_ressources[i]["url"].endswith("json"))
        #     if condition1 and condition2 :
        #         url = url + [new_ressources[i]["url"]] 
        #         title = title + [new_ressources[i]["title"]] 
        # return url, title            


    def get(self) -> None:
        """
        Étape get qui permet le lavage du dossier sources/{self.source} et 
        la récupération de l'ensemble des fichiers présents sur chaque url.
        """
        logging.info("  ÉTAPE GET")
        logging.info(f"Début du téléchargement : {len(self.url)} fichier(s)")
        os.makedirs(f"sources/{self.source}", exist_ok=True)
        # print("SELF.URL:" , self.url)
        if self.cle_api==[]:
            print("Pas  de clé api")
            self.download_without_metadata()
        else:
            # Verification de l'existence d'un eventuel doublon + nettoyage + 
            # Téléchargement du nouveau fichier
            for i in range(len(self.url)):
                try:
                    if os.path.exists(f"sources/{self.source}/{self.title[i]}"):
                        os.remove(f"sources/{self.source}/{self.title[i]}")
                        logging.info(f"Fichier : {self.title[i]} existe déjà, nettoyage du doublon ")
                    wget.download(self.url[i], f"sources/{self.source}/{self.title[i]}")
                except:
                    logging.error("Problème de téléchargement du fichier ", self.url[i])
        logging.info(f"Téléchargement : {len(self.url)} fichier(s) OK")


    def download_without_metadata(self) -> None:
        """
        Fonction téléchargeant un fichier n'ayant pas de clé api. Par 
        conséquent, le téléchargement s'effectue grâce à l'url dans 
        l'attribut url_source
        """
        nom_fichiers = os.listdir(f"sources/{self.source}")
        parsed_url = urlparse(self.url[0])

        # Obtenir le chemin de l'URL et extraire le nom du fichier
        file_name = parsed_url.path.split('/')[-1]

        if nom_fichiers!=[]:   #Dossier non vide
            os.remove(f"sources/{self.source}/{nom_fichiers[0]}")
            logging.info(f"Le fichier {nom_fichiers[0]} était présent. Il a été supprimé")
            wget.download(self.url[0], f"sources/{self.source}/{file_name}")
            self.title = [ file_name ]
            logging.info(f"Titre des fichiers : {self.title}")

        #Le dossier est vide car il s'agit du 1er téléchargement. Téléchargement 
        #dans le dossier puis affectation du nom du fichier à l'attribut titre
        else:
            wget.download(self.url[0], f"sources/{self.source}/")
            print(os.listdir(f"sources/{self.source}"))
            self.title = [ os.listdir(f"sources/{self.source}")[0] ]
            logging.info(f"Titre des fichiers : {self.title}")


    def clean(self) -> None:
        """
        Cette fonction extrait les dictionnaires des fichiers 
        (suivant le format 2022) pour qu'ils puissent être nettoyé.
        Grâce à la fonction tri_format, un tri est effectué sur ces
        dictionnaires pour séparer les bons marchés, des mauvais.
        """
        logging.info(" ÉTAPE CLEAN")
        logging.info("Début du tri des nouveaux fichiers")
        #Ouverture des fichiers
        dico = {}
        for i in range(len(self.title)):            
            if self.format == 'xml':
                try:
                    with open(f"sources/{self.source}/{self.title[i]}", encoding='utf-8') as xml_file:
                        dico = xmltodict.parse(xml_file.read(), dict_constructor=dict, \
                                               force_list=('marche','titulaires', 'modifications', 'actesSousTraitance',
                                               'modificationsActesSousTraitance', 'typePrix','considerationEnvironnementale',
                                               'modaliteExecution'))
                except Exception as err:
                    logging.error(f"Exception lors du chargement du fichier xml {self.title[i]} - {err}")

            elif self.format == 'json':
                try:
                    with open(f"sources/{self.source}/{self.title[i]}", encoding="utf-8") as json_file1:
                        dico = json.load(json_file1)
                except Exception as err:
                    logging.error(f"Exception lors du chargement du fichier json {self.title[i]} - {err}")
            try:
                self.tri_format(dico['marches'], self.title[i])    #On obtient 2 fichiers qui sont mis jour à chaque tour de boucle
            except Exception as err:
                logging.error("clean: Balise 'marches' inexistante")
            
        logging.info("Fin du tri")
        logging.info("Nettoyage OK")


    def tri_format(self, dico:dict, file_name:str) -> None:
        """
        Cette fonction permet de vérifier la structure du dictionnaire fournit en
        entrée. Si le schéma est respecté, les marchés et concessions correctes
        sont stockés dans des listes et des fichiers pour une future utilisation.
        Il en est de même pour les marchés et les concessions incorrectes.

        Args:

            dico : il s'agit d'un dictionnaire avec 2 clés: 'marchés' et 'contrat-concession'
            file_name : nom du fichier où se trouve le dictionnaire dico

        """
        n, m = 0, 0
        dico_ignored_marche, dico_ignored_concession = [], []

        #Creation des dossiers
        os.makedirs(f"bad_results", exist_ok=True) 
        os.makedirs(f"bad_results/{self.source}", exist_ok=True)

        if 'marche' in dico:
            while n < len(dico['marche']) :
                self.dico_2022_marche.append(dico['marche'][n])
                dico_test = {'marches': {'marche': self.dico_2022_marche,'contrat-concession': self.dico_2022_concession}}

                if not self.check(dico_test, None):
                    self.dico_2022_marche.remove(dico['marche'][n])
                    dico_ignored_marche.append(dico['marche'][n])
                n+=1


        if 'contrat-concession' in dico:
            while m < len(dico['contrat-concession']) :
                self.dico_2022_concession.append(dico['contrat-concession'][m])
                dico_test = {'marches': {'marche': self.dico_2022_marche,'contrat-concession': self.dico_2022_concession}}


                if not self.check(dico_test, None):
                    self.dico_2022_concession.remove(dico['contrat-concession'][m])
                    dico_ignored_concession.append(dico['contrat-concession'][m])
                m+=1
           

        # Structure du nouveau fichier JSON, création des dictionnaires valides et invalides
        jsonfile = {'marches': {'marche':  dico_ignored_marche, 'contrat-concession': dico_ignored_concession}}

        #Ecriture dans les nouveaux fichiers
        with open(f'bad_results/{self.source}/mauvais_marches_{self.source}.json', "w", encoding='utf8') as new_f2:
            json.dump(jsonfile, new_f2, ensure_ascii=False, indent=4)

        logging.info(f"Nombre de marchés et concessions invalides dans {file_name}: {len(dico_ignored_marche)+len(dico_ignored_concession)} ")
        logging.info(f"Nombre de marchés et de concessions valides dans {file_name}: {len(self.dico_2022_marche)+len (self.dico_2022_concession)} ")

    def date_norm(self,datestr:str ) -> str:
        """
        Permet de modifier le format d'une date. Plus
        précsément, les '+' sont remplacés par des '-'
        """
        return datestr.replace('+','-') if datestr else datestr


    def date_before_2024(self, record:dict, nature:str) -> bool:
        """ 
        La fonction vérifie que les dates contenues dans un marché/une 
        concession sont postérieures à 2024 et sont de la forme Y-M-J
        pour les colonnes date et date_de_publication. 

        Args:

            record: dictionnaire dans lequel se fait la vérification
            nature: il s'agit soit d'une concession, soit d'un marché

        """
        if nature == "marché":
            if not record['nature'] is None  and 'concession' in record['nature'].lower():
                if 'dateDebutExecution' in record:
                    if record['dateDebutExecution'] and self.date_norm(record['dateDebutExecution'])<'2024-01-01':
                        return True
                if 'datedebutexecution' in record:
                    if record['datedebutexecution'] and self.date_norm(record['datedebutexecution'])<'2024-01-01':
                        return True
            else:
                if 'dateNotification' in record:
                    if record['dateNotification'] and self.date_norm(record['dateNotification'])<'2024-01-01':
                        return True
                if 'datenotification' in record:
                    if record['datenotification'] and self.date_norm(record['datenotification'])<'2024-01-01':
                        return True
        else:
            if 'dateNotification' in record:
                if record['dateNotification'] and self.date_norm(record['dateNotification'])<'2024-01-01':
                    return True
            if 'datenotification' in record:
                if record['datenotification'] and self.date_norm(record['datenotification'])<'2024-01-01':
                    return True
        return False
    

    def date_after_2024(self, record:dict) -> bool:
            """
            La fonction prend en entrée un dictionnaire et renvoie un 
            booléeen.Les dates postérieures à 2024 doivent être de la
            forme Y-M-J pour les colonnes date et date_de_publication.

            Args:

                record: dictionnaire dans lequel se fait la vérification

            """
            first = datetime.strptime("2024-01-01", "%Y-%m-%d")
            pattern1 = r'20[0-9]{2}-[0-1]{1}[0-9]{1}-[0-9]{2}'
            pattern2 = r'20[0-9]{2}/[0-1]{1}[0-9]{1}/[0-9]{2}'
            if record['nature']=='Marché':
                col_date = 'dateNotification'
            else :
                col_date = 'dateDebutExecution'
            col_date_publication='datePublicationDonnees'
            col_list = [col_date,col_date_publication]
            for col in col_list:
                if col in record and record[col] and (re.match(pattern1,record[col]) or re.match(pattern2,record[col])):
                    try:
                        date = datetime.strptime(record[col], "%Y-%m-%d")
                        if date>=first:
                            if col == col_date_publication:
                                record[col_date] = record[col_date_publication]
                            return True
                    except:
                        None
            return False


    def _add_column_type(self, df: pd.DataFrame, default_type_name:str = None) -> None :
        """
        La fonction ajoute une colonne "_type" dans le dataframe
        dont les valeurs seront: "Marché" ou "Concession". 

        Args: 

            df: dataframe à compléter
            default_type_name: il s'agit de l'une des 2 valeurs possibles

        """
        if self.data_format=='2022' and not "_type" in df.columns and (default_type_name or "nature" in df.columns):
            if default_type_name:
                df['_type'] = default_type_name
            else:
                df['_type'] = df["nature"].apply(lambda x: "Marché" if x=="Marché" else "Concession")


    # def convert_prestataire(self):
    #     """Étape de conversion des fichiers qui supprime les ' et concatène les fichiers présents
    #     dans {self.source} dans un seul DataFrame"""
    #     logging.info("  ÉTAPE CONVERT")
    #     # suppression des '
    #     count = 0
    #     list_path = []    #list_path sera la liste de tous les fichiers car self.title est la liste des noms de fichiers qui ont été téléchargés
    #     repertoire_source = f"sources/{self.source}"
    #     #on récupère le nom de chaque fichier et on le met dans liste path, en plus de compter le nombre de fichiers présent dnas le dossier source
    #     for path in os.listdir(repertoire_source):
    #         if os.path.isfile(os.path.join(repertoire_source, path)):
    #             list_path = list_path + [path] 
    #             count += 1
    #     for i in range(count):
    #         # print ("title",self.title) 
    #         # print ("i :",i) 
    #         file_path = f"sources/{self.source}/{list_path[i]}"
    #         file_exist = os.path.exists(file_path)
    #         if not file_exist:
    #             logging.warning(f"Le fichier {file_path} n'existe pas.")

    #     # if count != len(self.url):
    #     #     logging.warning("Nombre de fichiers en local inégal au nombre d'url trouvé")
    #     # if count != len(self.url):
    #     #     logging.warning("Nombre de fichiers en local inégal au nombre d'url trouvé")
    #     logging.info(f"Début de convert: mise au format DataFrame de {self.source}")
    #     if self.format == 'xml':
    #         li = []
    #         for i in range(count):
    #             if self.data_format=='2022':
    #                 if not self.check(None,f"sources/{self.source}/{list_path[i]}"):
    #                     logging.warning(f"sources/{self.source}/{list_path[i]} not a valide xml")
    #                     continue
    #                     #raise Exception(f"sources/{self.source}/{self.file_name[i]}.{self.format} not a valide xml")
    #             try:
    #                 with open(f"sources/{self.source}/{list_path[i]}", encoding='utf-8') as xml_file:
    #                     dico = xmltodict.parse(xml_file.read(), dict_constructor=dict)
 
    #                 if dico['marches'] is not None:
    #                     dico = self.format_2022(dico,f"sources/{self.source}/{list_path[i]}_ignored.{self.format}")
                        
    #                     if 'marches' in dico:
    #                         # Add marchés
    #                         if 'marche' in dico['marches']:   #à chaque noueau marché, on ajoute une colonne, qui sera utilisé par un dataframe. Ce dataframe sera ajouté dans la liste li
    #                             df = pd.DataFrame.from_dict(dico['marches']['marche'])
    #                             self._add_column_type(df,"Marché")
    #                             li.append(df)
    #                             ##del df

    #                         # Add Concession
    #                         if self.data_format=='2022' and 'contrat-concession' in dico['marches']:
    #                             df = pd.DataFrame.from_dict(dico['marches']['contrat-concession'])
    #                             self._add_column_type(df,"Concession")
    #                             li.append(df)
    #                             ##del df
    #                     ##del dico
    #                 else:  # cas presque null
    #                     logging.warning(f"Le fichier {list_path[i]} est vide, il est ignoré")
    #             except Exception as err:
    #                 logging.error(f"Exception lors du chargement du fichier xml {list_path[i]} - {err}")

    #         if len(li) != 0:
    #             df = pd.concat(li)
    #             ##del li
    #             df = df.reset_index(drop=True)
    #         else:
    #             # create empty dataframe
    #             df = pd.DataFrame()
    #         return df
    #     elif self.format == 'json':
    #         li = []
    #         for i in range(count):
    #             try:
    #                 with open(f"sources/{self.source}/{list_path[i]}", encoding="utf-8") as json_file:
                        
    #                     #check for format compliance (only for data_format 2022)
    #                     if self.data_format=='2022':
    #                         if not self.check(json_file,None):
    #                             logging.warning(f"sources/{self.source}/{list_path[i]} not a valid json")
    #                             raise Exception("Json format not valid")
                        
    #                         dico = json.load(json_file)
    #                         self._retain_with_format(dico,f"sources/{self.source}/{list_path[i]}_ignored.{self.format}")

                            
    #                         if 'marches' in dico:
    #                             # Add marchés
    #                             if 'marche' in dico['marches']:
    #                                 df = pd.DataFrame.from_dict(dico['marches']['marche'])
    #                                 self._add_column_type(df,"Marché")
    #                                 li.append(df)
    #                                 ##del df

    #                             # Add Concession
    #                             if self.data_format=='2022' and 'contrat-concession' in dico['marches']:
    #                                 df = pd.DataFrame.from_dict(dico['marches']['contrat-concession'])
    #                                 self._add_column_type(df,"Concession")
    #                                 li.append(df)
    #                                 ##del df
    #                     else:
    #                         dico = json.load(json_file)
    #                         self._retain_with_format(dico,f"sources/{self.source}/{list_path[i]}_ignored.{self.format}")
    #                         df = pd.DataFrame.from_dict(dico['marches'])
    #                         self._add_column_type(df)
    #                         li.append(df)
    #                         ##del df
    #                     ##del dico
    #             except Exception as err:
    #                 logging.error(f"Exception lors du chargement du fichier json {list_path[i]} - {err}")
    #         df = pd.concat(li)
    #         ##del li
    #         df = df.reset_index(drop=True)
    #         return df
    #     logging.info("Conversion OK")
    #     logging.info(f"Nombre de marchés dans {self.source} après convert : {len(self.df)}")


    def convert(self) -> None:
        """
        Étape de conversion des fichiers qui concatène les fichiers présents dans 
        {self.source} dans un seul DataFrame. Elle utilise le dictionnaire 
        des marchés/concessions valides de chaque fichier pour le convertir en un 
        dataframe. L'ensemble des dataframes est stocké dans une liste. 
        """
        logging.info("  ÉTAPE CONVERT")
        logging.info(f"Début de convert: mise au format DataFrame de {self.source}")

        #Mise à jour des dictionnaires
        # old_files = list(set(os.listdir(f"sources/{self.source}")) - set(self.title))   #liste des titres des fichiers déja présents en local
    
        # for i in range(len(old_files)):
        #     logging.info("Extraction des données des anciens fichiers")

        #     if self.format == 'xml':
        #         try:
        #             with open(f"sources/{self.source}/{old_files[i]}", encoding='utf-8') as xml_file:
        #                 dico = xmltodict.parse(xml_file.read(), dict_constructor=dict,  \
        #                                        force_list=('marche','titulaires', 'modifications', 'actesSousTraitance',
        #                                        'modificationsActesSousTraitance', 'typePrix','considerationEnvironnementale',
        #                                        'modaliteExecution'))
        #                 #Ajout du dictionnaire dans la bonne variable (dico_2022_marche, dico_2022_concession, dico_ignored_marche, dico_ignored_concession)
        #                 # try:
        #                 #     self.tri_format(dico["marches"], f"sources/{self.source}/{old_files[i]}")
        #                 # except Exception as err:
        #                 #     logging.error("Balise 'marches' inexistante")
        #         except Exception as err:
        #             logging.error(f"Exception lors du chargement du fichier xml {old_files[i]} - {err}")

        #     elif self.format == 'json':
        #             try:
        #                 with open(f"sources/{self.source}/{old_files[i]}", encoding="utf-8") as json_file:
        #                     dico = json.load(json_file)
        #                     #Ajout du dictionnaire dans la bonne variable (dico_2022_marche, dico_2022_concession, dico_ignored_marche, dico_ignored_concession)
        #                 # try:
        #                 #     self.tri_format(dico["marches"], f"sources/{self.source}/{old_files[i]}")
        #                 # except Exception as err:
        #                 #     logging.error("Balise 'marches' inexistante")

        #             except Exception as err:
        #                 logging.error(f"Exception lors du chargement du fichier json {old_files[i]} - {err}")

        logging.info(f"Début de convert: mise au format DataFrame de {self.source}")
        #Liste qui conservera les dataframes. 
        li = []

        # Ajout d'un marché à la liste des dataframes
        df = pd.DataFrame.from_dict(self.dico_2022_marche)
        if "_type" not in df.columns:
            self._add_column_type(df,"Marché")
        li.append(df)

    
        # Ajoutd'une concession à la liste des dataframes
        df = pd.DataFrame.from_dict(self.dico_2022_concession)
        if "_type" not in df.columns:
            self._add_column_type(df,"Concession")
        li.append(df)
           
        #Concaténation des dataframes de la liste li en une dataframe                  
        if len(li) != 0:
            df = pd.concat(li)
            df = df.reset_index(drop=True)
        else:
            # create empty dataframe
            df = pd.DataFrame()
        self.df = df
        logging.info("Conversion OK")
        logging.info(f"Nombre de marchés dans {self.source} après convert : {len(self.df)}")


    def validateJson(self,jsonData:dict,jsonScheme:dict) -> bool:
        """
        Fonction vérifiant si le fichier jsn "jsonData" respecte
        le schéma spécifié dans le  schéma en paramètre "jsonScheme". 

        Args: 

            jsonData: dictionnaire qui va être vérifié par le validateur
            jsonScheme: schéma à respecter

        """
        try:
            #Draft7Validator.check_schema(jsonScheme)
            #Draft202012Validator.check_schema(jsonScheme)
            validate(instance=jsonData, schema=jsonScheme)
        except jsonschema.exceptions.ValidationError as err: 
            logging.error(f"Erreur de validation json - {err}")
            with open(f'bad_results/{self.source}/log_erreurs_{self.source}.txt', 'a', encoding='utf8') as error_file:
              error_file.write(str(err) + '\n')
            return False
        return True     

    def validateXml(self, xml_path: str, xsd_path: str) -> bool:
        """
        Fonction vérifiant si un fichier xml  respecte 
        le schéma spécifié.

        Args:

            xml_path: chemin du fichier à vérifier
            xsd_path: chemin du schéma 

        """
        xml_schema_doc = etree.parse(xsd_path)
        xml_schema = etree.XMLSchema(xml_schema_doc)

        xml_doc = etree.parse(xml_path)

        try:
            result = xml_schema.validate(xml_doc)
        except jsonschema.exceptions.ValidationError as err:
            logging.error(f"Erreur de validation xml - {err}")
            with open(f'bad_results/{self.source}/log_erreurs_{self.source}.txt', 'a', encoding='utf8') as error_file:
              error_file.write(str(err) + '\n')
            return False
        return result
    
    def check(self,jsonData,xml_path) -> bool:
        """
        Fonction qui prend en paramètre une donnée json ou xml 
        et vérifiant, grâce à un schéma, que la donnée est valide.

        Args:

            jsonData : donnée json en entrée (None si on vérifie un fichier xml)
            xml_path : chemin du fichier xml en entrée (None si on vérifie un fichier json)

        """
        #on vérifie que la donnée en entrée est valide par rapport au schéma
        if self.format=='json':
            scheme_path = 'schemes/schema_decp_v2.0.2.json'
            with open(scheme_path, "r",encoding='utf-8') as jsonfile1:
                jsonScheme = json.load(jsonfile1)
                jsonfile1.close
            return self.validateJson(jsonData,jsonScheme)
        else: 
            scheme_path = 'schemes/schema_decp_v2.0.2.xml'   # xml
            try:
                with open(xml_path, 'r', encoding='utf-8') as xml_file:
                    xml_content = xml_file.read()
                return xmlschema.validate(xml_content, scheme_path)==None
            except xmlschema.exceptions.XMLSchemaException as err:
                logging.error(f"Erreur de validation xml - {err}")
                with open(f'bad_results/{self.source}/log_erreurs_{self.source}.txt', 'a', encoding='utf8') as error_file:
                    error_file.write(str(err) + '\n')
                return False

    def convert_boolean(self,col_name:str) -> None:
        """
        Permet de remplacer les valeurs booléennes "Vrai" ou "Faux" par "oui" ou "non"

        Args:

            col_name: colonne où s'effectue le changement

        """
        #Conversion si il s'agit de string
        if self.df[col_name].dtypes == 'object':  
            self.df[col_name] = self.df[col_name].astype(str).replace({'1': 'oui', 'true': 'oui', '0': 'non', 'false': 'non','True': 'oui', 'False': 'non'})
        else:
            self.df[col_name] = self.df[col_name].astype(str).replace({'True': 'oui', 'False': 'non' }) 


    def fix(self) -> None:
        """
        Étape fix qui crée la colonne source dans le
        DataFrame et qui supprime les doublons purs.
        """
            
        def check_dico(dico):
        #Prend en entrée le dictionnaire du champ "acheteur"
            if dico=={} or dico is None or dico['id']==None:
                return True
            return False
        
        def update_id(ligne):
            #Modifie le champ "id" du champ acheteur
            if check_dico(ligne["acheteur"]):
                   ligne["acheteur"] = {"id": ligne["id"] }
            return ligne      

        
        logging.info("  ÉTAPE FIX")
        logging.info(f"Début de fix: Ajout source et suppression des doublons de {self.source}")
        # Ajout de source
        self.df = self.df.assign(source=self.source)

        # Transformation des acheteurs
        if "acheteur" in self.df.columns:
            df_marche = self.df.loc[self.df['nature'].str.contains('March', case=False, na=False)] #on récupère que les lignes de nature "marché"
            self.df.loc[df_marche.index,['id','acheteur']]= self.df.loc[df_marche.index,['id','acheteur']].apply(update_id,axis=1)
        # Force type integer on column offresRecues
        if "offresRecues" in self.df.columns: 
            self.df['offresRecues'] = self.df['offresRecues'].fillna(0).astype(int)
        if "marcheInnovant" in self.df.columns:
            #print("TYPE COLONNE MARCHE INNOVANT:", self.df['marcheInnovant'].dtype)
            self.convert_boolean('marcheInnovant')
        if "attributionAvance" in self.df.columns:
            #print("TYPE COLONNE ATTRIBUTION AVANCEE:", self.df['attributionAvance'].dtype)
            self.convert_boolean('attributionAvance')
        if "sousTraitanceDeclaree" in self.df.columns:
            #print("TYPE COLONNE sous traitance:", self.df['sousTraitanceDeclaree'].dtype)
            self.convert_boolean('sousTraitanceDeclaree')


       
        # Suppression des doublons
        df_str = self.df.astype(str)
        # duplicates = df_str[df_str.duplicated()] 
        # doublons = duplicates.to_json(orient='records', lines=True, force_ascii=False)
        # jsonfile = {'marches': doublons}

        # #Ecriture dans les nouveaux fichiers
        # with open(f'bad_results/{self.source}/doublons_{self.source}.json', "a", encoding='utf8') as new_f:
        #     json.dump(jsonfile, new_f, ensure_ascii=False, indent=4)

        # # print("duplicates",duplicates)
        # # duplicates.to_csv(f'bad_results/{self.source}/doublons_{self.source}.csv', sep = ';', encoding ='utf-8', mode= 'a', index = False)
        # # with open(f'bad_results/{self.source}/doublons_{self.source}.csv', 'a', encoding='utf-8') as f:
        # #     writer = csv.writer(f, delimiter = ';')
        # #     writer.writerow(duplicates.iloc[:][:]) 
        index_to_keep = df_str.drop_duplicates().index.tolist()
        self.df = self.df.iloc[index_to_keep]
        self.df = self.df.reset_index(drop=True)
        logging.info(f"Fix de {self.source} OK")
        logging.info(f"Nombre de marchés dans {self.source} après fix : {len(self.df)}")
    

    def mark_mandatory_field(self,df: pd.DataFrame,field_name:str) -> pd.DataFrame:
        """
        Complète les lignes vides de la colonne "field_name" avec
        le string 'MQ'

        Args:

            df: dataframe dans lequel s'effectue les modifications
            filed_name: nom d'une colonne qui est obligatoire
        """
        if field_name in df.columns:
            empty_mandatory = ~pd.notna(df[field_name]) | pd.isnull(df[field_name])
            if not empty_mandatory.empty:
                df.loc[empty_mandatory,field_name] = 'MQ'
        return df

    def mark_optional_field(self,df: pd.DataFrame,field_name:str) -> pd.DataFrame:
        """
        Complète les lignes vides de la colonne "field_name" avec
        le string 'CDL'

        Args:

            df: dataframe dans lequel s'effectue les modifications
            filed_name: nom d'une colonne qui est optionnel
        """
        if field_name in df.columns:
            empty_optional  = ~pd.notna(df[field_name]) | pd.isnull(df[field_name])
            if not empty_optional.empty:
                df.loc[empty_optional,field_name] = 'CDL'
        return df

    def marche_mark_fields(self,df: pd.DataFrame) -> pd.DataFrame:
        """
        Commente toutes les colonnes du dataframe en 
        appelant les fonctions mark_mandatory_field
        et mark_optional_field. Le dataframe doit 
        contenir que des marchés.

        Args:

            df: dataframe dans lequel s'effectue les modifications
        """
        df = self.mark_mandatory_field(df,"id")
        df = self.mark_mandatory_field(df,"nature")
        df = self.mark_mandatory_field(df,"objet")
        df = self.mark_mandatory_field(df,"technique")
        df = self.mark_mandatory_field(df,"modaliteExecution")
        df = self.mark_mandatory_field(df,"codeCPV")
        df = self.mark_mandatory_field(df,"procedure")
        df = self.mark_mandatory_field(df,"dureeMois")
        df = self.mark_mandatory_field(df,"dateNotification")
        df = self.mark_mandatory_field(df,"considerationsSociales")
        df = self.mark_mandatory_field(df,"considerationsEnvironnementales")
        df = self.mark_mandatory_field(df,"marcheInnovant")
        df = self.mark_mandatory_field(df,"origineUE")
        df = self.mark_mandatory_field(df,"origineFrance")
        df = self.mark_mandatory_field(df,"ccag")
        df = self.mark_mandatory_field(df,"offresRecues")
        df = self.mark_mandatory_field(df,"montant")
        df = self.mark_mandatory_field(df,"formePrix")
        df = self.mark_mandatory_field(df,"typePrix")
        df = self.mark_mandatory_field(df,"attributionAvance")
        df = self.mark_mandatory_field(df,"datePublicationDonnees")
        df = self.mark_mandatory_field(df,"acheteur.id")
        df = self.mark_mandatory_field(df,"lieuExecution.code")
        df = self.mark_mandatory_field(df,"lieuExecution.typeCode")
        df = self.mark_mandatory_field(df,"titulaire_id_1")
        df = self.mark_mandatory_field(df,"titulaire_typeIdentifiant_1")
        df = self.mark_mandatory_field(df,"idActeSousTraitanceModification")
        df = self.mark_mandatory_field(df,"typeIdentifiantActeSousTraitanceModification")
        df = self.mark_mandatory_field(df,"dureeMoisActeSousTraitanceModification")
        df = self.mark_mandatory_field(df,"dateNotificationActeSousTraitanceModification")
        df = self.mark_mandatory_field(df,"montantActeSousTraitanceModification")
        df = self.mark_mandatory_field(df,"datePublicationDonneesActeSousTraitanceModification")

        df = self.mark_optional_field(df,"idAccordCadre")
        df = self.mark_optional_field(df,"tauxAvance")
        df = self.mark_optional_field(df,"typeGroupementOperateurs")
        df = self.mark_optional_field(df,"sousTraitanceDeclaree")
        df = self.mark_optional_field(df,"idSousTraitance")
        df = self.mark_optional_field(df,"dureeMoisSousTraitance")
        df = self.mark_optional_field(df,"dateNotificationSousTraitance")
        df = self.mark_optional_field(df,"montantSousTraitance")
        df = self.mark_optional_field(df,"variationPrixSousTraitance")
        df = self.mark_optional_field(df,"datePublicationDonneesSousTraitance")
        df = self.mark_optional_field(df,"idActeSousTraitance")
        df = self.mark_optional_field(df,"typeIdentifiantActeSousTraitance")
        df = self.mark_optional_field(df,"idModification")
        df = self.mark_optional_field(df,"dureeMoisModification")
        df = self.mark_optional_field(df,"montantModification")
        df = self.mark_optional_field(df,"titulairesModification")
        df = self.mark_optional_field(df,"typeIdentifiantModification")
        df = self.mark_optional_field(df,"dateNotificationModification")
        df = self.mark_optional_field(df,"datePublicationDonneesModification")
        
        return df

    def concession_mark_fields(self,df: pd.DataFrame) -> pd.DataFrame:
        """
        Commente toutes les colonnes du dataframe en 
        appelant es fonctions mark_mandatory_field
        et mark_optional_field. Le dataframe doit 
        contenir que des concessions.

        Args:

            df: dataframe dans lequel s'effectue les modifications
        """

        df = self.mark_mandatory_field(df,"id")
        df = self.mark_mandatory_field(df,"nature")
        df = self.mark_mandatory_field(df,"objet")
        df = self.mark_mandatory_field(df,"procedure")
        df = self.mark_mandatory_field(df,"dureeMois")
        df = self.mark_mandatory_field(df,"dateDebutExecution")
        df = self.mark_mandatory_field(df,"dateSignature")
        df = self.mark_mandatory_field(df,"considerationsSociales")
        df = self.mark_mandatory_field(df,"considerationsEnvironnementales")
        df = self.mark_mandatory_field(df,"valeurGlobale")
        df = self.mark_mandatory_field(df,"montantSubventionPublique")
        df = self.mark_mandatory_field(df,"datePublicationDonnees")
        df = self.mark_mandatory_field(df,"autoriteConcedante.id")
        df = self.mark_mandatory_field(df,"concessionnaire_id_1")
        df = self.mark_mandatory_field(df,"concessionnaire_typeIdentifiant_1")
        df = self.mark_mandatory_field(df,"depensesInvestissement")
        df = self.mark_mandatory_field(df,"datePublicationDonneesExecution")
        df = self.mark_mandatory_field(df,"intituleTarif")
        df = self.mark_mandatory_field(df,"tarif")

        df = self.mark_optional_field(df,"idModification")
        df = self.mark_optional_field(df,"dureeMoisModification")
        df = self.mark_optional_field(df,"valeurGlobaleModification")
        df = self.mark_optional_field(df,"dateSignatureModification")
        df = self.mark_optional_field(df,"datePublicationDonneesModification")

        return df
    
    def comment(self) -> None:
        """
        Cette étape permet de marquer les cases vides du
        dataframe avec un indicateur ("MD", ou "CDL").
        """
        # séparation des marchés et des concessions, car traitement différent
        df_marche = self.df.loc[~self.df['nature'].str.contains('concession', case=False, na=False)]

        df_concession1 = self.df.loc[self.df['nature'].str.contains('concession', case=False, na=False)]

        # df_concession prend aussi en compte les lignes restantes ou la colonne "_type" contient "concession" dans le df_marche et concatène les deux dataframes
        df_concession = pd.concat([self.df_concession1, df_marche.loc[df_marche['_type'].str.contains('concession', case=False, na=False)]])
        # remove old df for memory
        del df_concession1
        df_marche = df_marche.loc[~df_marche['_type'].str.contains('concession', case=False, na=False)]

        self.marche_mark_fields(df_marche)
        self.concession_mark_fields(df_concession)