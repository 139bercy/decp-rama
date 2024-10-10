from general_process.ProcessFactory import ProcessFactory
from general_process.GlobalProcess import GlobalProcess
import logging
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('-P', dest='process', type=str, help='run a specific process')
parser.add_argument("-l", dest='local', action='store_true', help="run script locally")
#parser.add_argument("-f", dest='format', type=str, help="run script for format 2019")
args = parser.parse_args()

def main(data_format:str = 2022):
    """La fonction main() appelle tour à tour les processus spécifiques (ProcessFactory.py/SourceProcess.py) et les
    étapes du Global Process (GlobalProcess.py)."""

    # get arguments from command line to know which process to run, if there is no arguments run all processes
    if args.process:
        p = ProcessFactory(args.process,data_format)
        p.run_process()
    else:
        p = ProcessFactory(None,data_format)
        p.run_processes()
    gp = GlobalProcess(data_format)
    gp.dataframes = p.dataframes
    gp.merge_all()
    gp.fix_all()
    #gp.drop_by_date_2024()
    gp.drop_duplicate()
    gp.export()
    print("Exportation faite")
    if not args.local:
        # gp.upload_s3()
        gp.upload_datagouv()

if __name__ == "__main__":
    """Lorsqu'on appelle la fonction main (courante), on définit le niveau de logging et le format d'affichage."""
    os.makedirs(f"logs", exist_ok=True)
    file_handler = logging.FileHandler(filename="logs/app.log", mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # Création du StreamHandler pour afficher les logs dans la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Définir le format du log
    formatter = logging.Formatter(u'%(asctime)s %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Obtenir le logger root
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Ajouter les handlers au logger root
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logging.info("---------------------------------------------------------------")
    logging.info("                      NOUVELLE EXECUTION")
    logging.info("---------------------------------------------------------------")

    print('Launching ...')

    all_data_format = ['2022']
    for data_format in all_data_format:
        print(f"---------------------------------------------------------------")
        print(f"Traitement pour le format {data_format}")
        # try:
        main(data_format)
        # except Exception as err:
        #     print(f"Une erreur est survenue lors du traitement pour le format {data_format} - {err}")
