from general_process.ProcessFactory import ProcessFactory
from general_process.GlobalProcess import GlobalProcess
from reporting.Report import Report
import logging
from utils.StepMngmt import StepMngmt
from utils.Step import Step
import augmente.data_management
import augmente.nettoyage
import augmente.utils
import argparse
import os


args = augmente.utils.parse_args()

step = StepMngmt()
    
def main(report,data_format:str = "2022"):
    """La fonction main() appelle tour à tour les processus spécifiques (ProcessFactory.py/SourceProcess.py) et les
    étapes du Global Process (GlobalProcess.py)."""

    # Init reporting
    # Init resume
    # get arguments from command line to know which process to run, if there is no arguments run all processes
    if args.process:
        p = ProcessFactory(args.process,data_format,report)
        p.run_process()
    else:
        p = ProcessFactory(None,data_format,report)
        p.run_processes()
    gp = GlobalProcess(data_format,report)
    gp.dataframes = p.dataframes
    gp.merge_all() # on a l'équivalent de return DataProcessor().decorator("MonParamètre")(self.process_data)()
    gp.fix_all()
    #gp.drop_by_date_2024()
    gp.drop_duplicate()
    gp.report.fix_statistics('merged')
    gp.export(args.local)
    gp.save_report()
    if not args.local:
        # gp.upload_s3()
        gp.upload_on_datagouv()


def main_augmente(data_format:str = '2022'):
    
    logger.info("Téléchargement des fichiers de données")
    augmente.data_management.main()
    logger.info("Fichiers mis à jour dans le dossier data")

    logger.info(f"Application règles métier format {data_format}")
    augmente.nettoyage.main(data_format)
    
    # Partie désactivé logger.info("Enrichissement des données")
    # enrichissement2.main()
    # logger.info("csv enrichi dans le dossier data")
    if not args.test and not args.local:
        augmente.utils.export_all_csv(data_format,args.local)

if __name__ == "__main__":
    """Lorsqu'on appelle la fonction main (courante), on définit le niveau de logging et le format d'affichage."""
    os.makedirs("logs", exist_ok=True)
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

    if args.rama:
        logging.info("Option exécution decp-rama activée")
    else:
        logging.info("Option exécution decp-rama désactivée")

    if args.augmente:
        logging.info("Option exécution decp-augmente activée")
    else:
        logging.info("Option exécution decp-augmente désactivée")

    if args.local:
        logging.info("Option exécution local activée")
    else:
        logging.info("Option exécution local désactivée")

    if args.test:
        logging.info("Option exécution de test activée")
    else:
        logging.info("Option exécution de test désactivée")

    if args.reset:
        logging.info("Reset previous execution step")
        step.reset()
    else:
        logging.info("Using previous execution history to continue processing")
        
    all_data_format = ['2022']
    for data_format in all_data_format:
        logging.info( "---------------------------------------------------------------")
        logging.info(f"                Traitement pour le format {data_format}")
        logging.info( "---------------------------------------------------------------")
        
        report = Report('decp-rama-augmente',False)
        try:
            if not args.augmente:
                main(report,data_format)
            if not args.rama:
                main_augmente(data_format)
            step.reset()
            report.db_end_session('OK')
        except Exception as err:
            report.db_end_session('KO ')
            logging.error(f"Une erreur est survenue lors du traitement pour le format {data_format} - {err}")
        
        logging.info(f"Traitement pour le format {data_format} terminé")
    
    logging.info("---------------------------------------------------------------")
    logging.info("Exécution de l'application terminée")
    logging.info("---------------------------------------------------------------")
                