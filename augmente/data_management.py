import wget
import boto3
import json
import os
from zipfile import ZipFile 
import pathlib
import logging
import requests
from utils.StepMngmt import StepMngmt
from utils.Step import Step


logger = logging.getLogger("main.weekly")
logger.setLevel(logging.DEBUG)
url_geoflar = "https://public.opendatasoft.com/explore/dataset/geoflar-communes-2015/download/?format=csv&timezone=Europe/Berlin&lang=fr&use_labels_for_header=true&csv_separator=%3B"
url_cpv = "https://www.economie.gouv.fr/files/files/directions_services/daj/marches_publics/oeap/recensement/cpv_2008_fr.xls"
url_departement = "https://www.insee.fr/fr/statistiques/fichier/4316069/departement2020-csv.zip"
url_region = "https://www.insee.fr/fr/statistiques/fichier/4316069/region2020-csv.zip"
url_commune = "https://www.insee.fr/fr/statistiques/fichier/5057840/commune2021-csv.zip"
url_arrondissement = "https://www.insee.fr/fr/statistiques/fichier/5057840/arrondissement2021-csv.zip"
url_stockEtablissement = "https://files.data.gouv.fr/insee-sirene/StockEtablissement_utf8.zip"
url_stockUniteLegale = "https://files.data.gouv.fr/insee-sirene/StockUniteLegale_utf8.zip"
#urls = [url_geoflar, url_cpv, url_departement, url_region, url_commune, url_arrondissement, url_stockEtablissement, url_stockUniteLegale]
urls = ["geoflar", "cpv", "departement", "region", "commune", "arrondissement", "stockEtablissement", "stockUniteLegale"]
titres = ["geoflar.csv", "cpv_2008_fr.xls", "departement2020.csv", "region2020.csv", "commune2021.csv",
           "arrondissement2021.csv", "StockEtablissement_utf8.csv", "StockUniteLegale_utf8.csv"]
data_path = "data"


def load_files_and_unzip(urls):
    """
    Cette fonction télécharge les fichiers utiles pour l'enrichissement. Puis les unzip.
    """
    with open("metadata/metadata.json", 'r+',  encoding='utf8') as f:
            metadata = json.load(f)
    data_exists = os.path.exists(data_path) #Creation du dossier data si inexitant
    if not data_exists:
        os.mkdir(data_path)
    # Téléchargements des fichiers
    cpt = 0
    for url in urls :
        if url=="geoflar":
            file=url+".csv"
        elif url=="cpv":
            file=url+".xls"
        else:
            file=url+".zip"
        if (not os.path.exists(f"data/{titres[cpt]}")) and (not os.path.exists(f"data/{url}.zip")):
            logger.info(f"Téléchargement de {url}")

            #wget.download(metadata[url]["url_source"], out=os.path.join(data_path, file))
            #wget.download(metadata[url]["url_source"], out=os.path.join(data_path, file),**{'user_agent': 'Mozilla/5.0',  'cookies': True } )         
            try:
                # Utilisation de requests pour télécharger le fichier
                response = requests.get(metadata[url]["url_source"], headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()  # Lève une erreur pour les codes de statut HTTP 4xx/5xx
                with open(os.path.join(data_path, file), 'wb') as f:
                    f.write(response.content)
                logger.info(f"{url}{metadata[url]['format']} téléchargé")
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur lors du téléchargement de {url}: {e}")
        else : 
            logger.info(f"Le fichier {url} est déjà présent, on ne le retélécharge pas")
        cpt = cpt+1

        
    # Unzip 
    extension = ".zip"
    for file in os.listdir(data_path):
        if file.endswith(extension): # On unzip que les fichiers zip
            file_path = os.path.join(pathlib.Path(__file__).parent, '..', data_path, file) # Full path
            with ZipFile(file_path, 'r') as zobj:
                zobj.extractall(path=data_path)
            logger.info(f"Fichier {file_path} dézippé")
            os.remove(file_path) # Supprime les .zip
    return None

def main():
    step = StepMngmt()
    if not step.bypass(StepMngmt.SOURCE_ALL,Step.AUGMENTE_LOAD):
        load_files_and_unzip(urls)
        step.snapshot(StepMngmt.SOURCE_ALL,Step.AUGMENTE_LOAD)
    

if __name__ == "__main__":
    main()
