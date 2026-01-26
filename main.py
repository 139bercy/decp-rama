from database.DbDecp import DbDecp
from general_process.ProcessFactory import ProcessFactory
from general_process.GlobalProcess import GlobalProcess
from reporting.Report import Report
import logging
from datetime import date
from utils.StepMngmt import StepMngmt
from utils.Step import Step
import augmente.data_management
import augmente.nettoyage
import augmente.utils
import os
import traceback


args = augmente.utils.parse_args()

step = StepMngmt()
    
def main(report,data_format:str = "2022"):
    """La fonction main() appelle tour à tour les processus spécifiques (ProcessFactory.py/SourceProcess.py) et les
    étapes du Global Process (GlobalProcess.py)."""

    # Init reporting
    # Init resume
    # get arguments from command line to know which process to run, if there is no arguments run all processes
    if not step.bypass("ALL",Step.FIX_ALL):
        if args.process:
            p = ProcessFactory(args.process,data_format,report)
            p.run_process(args)
        else:
            p = ProcessFactory(None,data_format,report)
            p.run_processes(args)
    
    gp = GlobalProcess(data_format,report)
    
    if not step.bypass("ALL",Step.FIX_ALL):
        gp.dataframes = p.dataframes
    
    gp.merge_all() # on a l'équivalent de return DataProcessor().decorator("MonParamètre")(self.process_data)()
    gp.fix_all()
    
    gp.report.fix_statistics('merged')
    gp.save_report()

    gp.update_global_data()
    gp.generate_export(args.local)
    gp.generate_global()

    if not args.local:
        # gp.upload_s3()
        suffixes = gp.get_suffixes_exported_files()
        gp.upload_on_datagouv(suffixes)


def main_augmente(session_id:str,data_format:str = '2022'):
    
    logger.info("Téléchargement des fichiers de données")
    augmente.data_management.main()
    logger.info("Fichiers mis à jour dans le dossier data")

    logger.info(f"Application règles métier format {data_format}")
    start_year, start_month = 2024, 1
    today = date.today()  
    end_year, end_month = today.year, today.month

    # Sauvegarde des marchés et concessions uniques regroupées par année et mois de date de 
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        ref_date = f"{year}-{month:02d}"
        augmente.nettoyage.main(session_id,ref_date,data_format)

        # Partie désactivé logger.info("Enrichissement des données")
        # enrichissement2.main()
        # logger.info("csv enrichi dans le dossier data")
        if not args.test and not args.local:
            augmente.utils.export_all_csv(ref_date,data_format,args.local)

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

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
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    # Ajouter les handlers au logger root
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logging.info("---------------------------------------------------------------")
    logging.info("                      NOUVELLE EXECUTION")
    logging.info("---------------------------------------------------------------")

    logging.info("(-m) Option exécution de decp-rama uniquement " + ("activée" if args.rama else "désactivée"))
    logging.info("(-a) Option exécution de decp-augmente uniquement " + ("activée" if args.augmente else "désactivée"))
    logging.info("(-l) Option exécution locale " + ("activée" if args.local else "désactivée"))
    logging.info("(-t) Option exécution en mode test " + ("activée" if args.test else "désactivée"))
    logging.info("(-r) Option reprise à la dernière étape exécutée " + ("desactivée" if args.reset else "activée"))
    logging.info("(-b) Option reconstruction globale " + ("activée pour " if args.rebuild else "désactivée") + (args.rebuild if args.rebuild else ""))

    # On ne reprend pas l'exécution à la dernière étape du précédent lancement de l'application, on supprime le cache d'exécution
    if args.reset:
        step.reset()

    all_data_format = ['2022']
    for data_format in all_data_format:
        logging.info( "---------------------------------------------------------------")
        logging.info(f"                Traitement pour le format {data_format}")
        logging.info( "---------------------------------------------------------------")

        db = DbDecp()
        session_id = db.add_session("decp-rama-augmente")
        db.close()
        report = Report('decp-rama-augmente',False)
        try:
            # DECP RAMA
            if not args.augmente:
                main(report,data_format)

            # DECP AUGMENTE
            if not args.rama:
                main_augmente(session_id,data_format)

            db = DbDecp()
            db.end_session(session_id,"OK")
            db.close()
        
            step.reset()
            report.db_end_session('OK')
        except Exception as err:
            tb = traceback.format_exc()
            er = err
        else:
            tb = None
            er = None
        finally:
            if not er is None:
                logging.error(f"Une erreur est survenue lors du traitement pour le format {data_format} - {er}")
                logging.error(tb)
                report.save_report()
                report.save_statistics()
                report.db_end_session('KO ')

        logging.info(f"Traitement pour le format {data_format} terminé")
    
    logging.info("---------------------------------------------------------------")
    logging.info("Exécution de l'application terminée")
    logging.info("---------------------------------------------------------------")
                