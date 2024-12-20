import os
import boto3
import botocore
import argparse
import json
import logging
import pandas as pd
import subprocess
from ftplib import FTP_TLS
import utils

logger = logging.getLogger("main.utils")
logger.setLevel(logging.DEBUG)

ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
USER = os.environ.get("USER_SAAGIE")
PASSWORD = os.environ.get("PASSWORD_SAAGIE")
ENDPOINT_S3 = os.environ.get("ENDPOINT_S3")
PROJECT_NAME = os.environ.get("PROJECT_NAME")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
REGION_NAME = os.environ.get("REGION_NAME") 

USER_DATAECO = os.environ.get("DECP_USER_DATAECO")
PWD_DATAECO = os.environ.get("DECP_PWD_DATAECO")
HOST_DATAECO = os.environ.get("DECP_HOST_DATAECO")
                             
s3 = boto3.resource(service_name='s3',
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY,
                    region_name=REGION_NAME,
                    endpoint_url="https://" + str(ENDPOINT_S3)
                    )
logger = logging.getLogger("main.utils")
logger.setLevel(logging.DEBUG)

# Initialize args parser
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", dest='test', action='store_true', help="run script in test mode with a small sample of data")
    parser.add_argument("-l", dest='local', action='store_true', help="run script locally")
    #parser.add_argument("-f", dest='format', type=str, help="run script for format 2019")
    return parser.parse_args()

args = parse_args()

logger.info(f"Le nom du Bucket utilisé est : {BUCKET_NAME}")

def save_csv(df: pd.DataFrame, file_name: str):
    """
    Cette fonction permet de sauvegarder un dataframe en csv

    Arguments
    -------------
    df : dataframe à sauvegarder
    file_name : nom du fichier à sauvegarder
    """
    path = "data_eclatees"

    if not (os.path.exists(path)):  # Si le chemin data n'existe pas
        os.mkdir(path)

    df.to_csv(os.path.join(path, file_name), index=False, sep=";")
    return None

def download_file(file_name_s3: str, file_name_local: str, verbose=False):
    """
    Cette fonction charge un fichiers de s3.

    Arguments
    -------------
    (file_name_s3) Le nom du fichier à traiter sur s3
    (file_name_local) Le nom à donner au fichier en local
    """
    bucket = s3.Bucket(BUCKET_NAME)
    path, filename = os.path.split(
        file_name_local)  # On télécharge d'abord à la racine du répertoire courant. Puis on déplace. Sinon erreur s3.
    if verbose:
        print(f"Fichier {file_name_s3} téléchargé vers {filename}")
    bucket.download_file(file_name_s3, filename)
    if "/" in file_name_local:
        if not (os.path.exists(path)):  # Si le chemin data n'existe pas (dans le cas de la CI et de Saagie)
            os.mkdir(path)
        os.replace(filename, os.path.join(path, filename))
        if verbose:
            print(f"fichier{filename} déplacé vers {os.path.join(path, filename)}")
    return None

def download_file(file_name:str):
    pass 

def export_file_csv(path_file_to_upload_csv:str,  data_format:str, local:bool=True):
    if not local:
        logger.info(f"Open connection with ftp via bash lftp to download {path_file_to_upload_csv} in subdirectory {data_format}")
        #bash_cmd = [f" ftp -u {USER_DATAECO}:{PWD_DATAECO} {HOST_DATAECO} -e 'set ftp:ssl-force true ; set ssl:verify-certificate false; quit'"] 
        bash_cmd = [f" lftp -u {USER_DATAECO}:{PWD_DATAECO} {HOST_DATAECO} -e 'set ftp:ssl-force true ; set ssl:verify-certificate false;cd decp; cd {data_format};put {path_file_to_upload_csv}; quit'"] # Je n'ai pas trouvé de biblio ftp python satisfaisante. Donc ce sera en bash
        logger.info(bash_cmd)
        subprocess.call(bash_cmd, shell=True)
        logger.info("Bash executed")
    else:
        logger.info(f"Open connection with ftp via ftplib to download {path_file_to_upload_csv} in subdirectory {data_format}")
        ftp = FTP_TLS(host=HOST_DATAECO, user=USER_DATAECO, passwd=PWD_DATAECO)
        ftp.cwd("decp")
        ftp.cwd(data_format)
        #ftp.retrlines('LIST')
        path, filename = os.path.split(path_file_to_upload_csv)
        fileObject = open(path_file_to_upload_csv, "rb");
        file2BeSavedAs = filename
        ftpCommand = "STOR %s"%file2BeSavedAs;
        ftpResponseMessage = ftp.storbinary(ftpCommand, fp=fileObject);
        logger.info(ftpResponseMessage)

def export_all_csv(data_format:str = '2022', local:bool=True):
    export_file_csv(f"data/marche_{data_format}.csv",data_format,local)
    export_file_csv(f"data/marche_exclu_{data_format}.csv",data_format,local)
    export_file_csv(f"data/concession_{data_format}.csv",data_format,local)
    export_file_csv(f"data/concession_exclu_{data_format}.csv",data_format,local)
