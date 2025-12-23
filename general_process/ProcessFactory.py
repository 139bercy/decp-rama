from general_process.SourceProcess import ProcessParams
from specific_process import * 
# Source non traitée pour l'instant
import logging

from reporting.Report import Report
from utils.Step import Step
from utils.StepMngmt import StepMngmt

class ProcessFactory:

    def __init__(self, process=None, data_format=None, report:Report=None):
        """Création de la liste des Processus qui correspondent chacun à une classe importée en début de document."""
        #self.processes = [PesProcess, AwsProcess, AifeProcess, EmarProcess, LyonProcess, MegaProcess]
        #self.processes = [MaxiProcess]
        # self.processes = [DecpAwsProcess, BfcProcess, PesProcess, AwsProcess, AifeProcess, EmarProcess, LyonProcess, MegaProcess]  # Supprimer le BRe car pris en compte dans megalisbre, DecpAwsProcess
        #self.processes = [DecpAwsProcess, EmarProcess, LyonProcess]  # Supprimer le BRe car pris en compte dans megalisbre, DecpAwsProcess
        #self.processes = [PesProcess, LyonProcess, EmarProcess]
        #self.processes = [MegaProcess]
        #self.processes = [Emar2024Process]
        #self.processes = [SampleJsonProcess]
        #self.processes = [SampleXmlProcess]
        self.processes = [Emar2024Process,Pes2024Process,Ppsmj2024Process,Xmarches2024Process,Aws2024Process,Modulademat2024Process,Atexo2024Process]
        #self.processes = [Proxilegales2024Process,Achatspublicscorse2024Process,Marchespublicspro2024Process,Provencecorse2024Process,Antilleslegales2024Process,Marchedemat2024Process]
        #self.processes = [Atexo2024Process,Megalis2024Process,Aws2024Process]
        #self.processes = [Megalis2024Process]
        #self.processes = [Emar2024Process]
        #self.processes = [Ppsmj2024Process]
        #self.processes = [Atexo2024Process]
        #self.processes = [SampleXmlProcess]
        #self.processes = [Aife2024Process]
        #self.processes = [Xmarches2024Process]
        #self.processes = [Aws2024Process]
        #self.processes = [Pes2024Process]
        #self.processes = [Modula2024Process]
        # if data_format=='2022':
        # self.processes = [SampleXmlProcess] # For test ECO
        #self.processes = [SampleJsonProcess] # For test ECO
        self.dataframes = []
        self.data_format = data_format
        self.report = report
        self.step = StepMngmt()

        # si on lance main avec un process spécifié :
        if process:
            for proc in self.processes:
                if proc.__name__ == process:
                    self.process = proc
                    break

    def run_processes(self,args):
        """Création d'une boucle (1 source=1 itération) qui appelle chacun des processus de chaque source."""
        for process in self.processes:
            loaded = ''
            try:
                logging.info( "---------------------------------------------------------------")
                logging.info(f"               Traitement de {process.__name__} ")
                logging.info( "---------------------------------------------------------------")
                params = ProcessParams(key=None,data_format=self.data_format, report=self.report, rebuild=args.rebuild.strip() if args.rebuild else None)
                p = process(params)
                logging.info(self.step.get_status(p.source))
                if not self.step.bypass(p.source,Step.GET):
                    p.get()
                    self.step.snapshot(p.source,Step.GET)
                if not self.step.bypass(p.source,Step.CLEAN):
                    p.clean()
                    self.step.snapshot_dicts(p.source,Step.CLEAN,p.dico_2022_marche,p.dico_2022_concession)
                else:
                    p.dico_2022_marche,p.dico_2022_concession = self.step.resume_dicts(p.source,Step.CLEAN,StepMngmt.FORMAT_DICTS)
                if not self.step.bypass(p.source,Step.CONVERT):
                    p.convert()
                    self.step.snapshot_dataframe(p.source,Step.CONVERT,p.df)
                else:
                    p.df = self.step.resume(p.source,Step.CONVERT,StepMngmt.FORMAT_DATAFRAME)
                if not self.step.bypass(p.source,Step.FIX):
                    p.fix()
                    self.step.snapshot_dataframe(p.source,Step.FIX,p.df)
                else:
                    p.df = self.step.resume(p.source,Step.FIX,StepMngmt.FORMAT_DATAFRAME)
                p.fix_statistics()
                logging.info (f"Ajout des données de la source {process.__name__}")
                self.dataframes.append(p.df) #p.df['tmp__max_date'].apply(lambda x: type(x)).value_counts() #
                p.df = None
                logging.info( "---------------------------------------------------------------")
                logging.info(f"             Fin du traitement {process.__name__}")
                logging.info( "---------------------------------------------------------------")
            except Exception as err:
                loaded = self.step.get_status(p.source)
                if loaded != '':
                    logging.error(f"Erreur à l'étape {loaded}  - {err}")
                else:
                    logging.error(f"Source introuvable - {err}")

    def run_process(self,args):
        """Lance un seul processus"""
        logging.info(f"------------------------------{self.process.__name__}------------------------------")
        params = ProcessParams(key=None,data_format=self.data_format, report=self.report, rebuild=args.rebuild)
        p = self.process()
        if not self.step.bypass(p.source,Step.GET):
            p.get()
            self.step.snapshot(p.source,Step.GET)
        if not self.step.bypass(p.source,Step.CLEAN):
            p.clean()
            self.step.snapshot_dicts(p.source,Step.GET,p.dico_2022_marche,p.dico_2022_concession)
        else:
            p.dico_2022_marche,p.dico_2022_concession = self.step.resume_dicts(p.source,Step.GET,StepMngmt.FORMAT_DICTS)
        if not self.step.bypass(p.source,Step.CONVERT):
            p.convert()
            self.step.snapshot_dataframe(p.source,Step.CONVERT,p.df)
        else:
            p.df = self.step.resume(p.source,Step.CONVERT,StepMngmt.FORMAT_DATAFRAME)
        if not self.step.bypass(p.source,Step.FIX):
            p.fix()
            self.step.snapshot_dataframe(p.source,Step.FIX,p.df)
        else:
            p.df = self.step.resume(p.source,Step.FIX,StepMngmt.FORMAT_DATAFRAME)
        self.dataframes.append(p.df)
        
