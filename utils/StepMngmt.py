import json
import os
import pandas as pd
import shutil
from utils.Step import Step
import logging

class StepMngmt:
    _instance = None

    BASE_PATH = 'processing/'
    STATUS_FILEPATH = 'processing/run_status.json'
    
    FORMAT_DICTS = 'dicts'
    FORMAT_DATAFRAME = 'dataframe'

    SOURCE_ALL = 'ALL'
    SOURCE = 'SOURCE'

    init_status = {}
    current_status = {}


    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(StepMngmt, cls).__new__(cls)
            cls._instance.load_data()  # Charger les données lors de l'initialisation
        return cls._instance


    def load_data(self):
        if not os.path.exists(StepMngmt.BASE_PATH):
            os.makedirs(StepMngmt.BASE_PATH)

        try:
            with open(self.STATUS_FILEPATH, 'r') as json_file:
                self.init_status = json.load(json_file)

            with open(self.STATUS_FILEPATH, 'r') as json_file:
                self.current_status = json.load(json_file)

            logging.info("Resume execution")

        except FileNotFoundError:
            self.current_status = {}
            with open(self.STATUS_FILEPATH, 'w') as json_file:
                json.dump(self.current_status, json_file)


    def decorator(self, step:Step, format:str):
        def wrapper(func):
            def inner_wrapper(self_wrapper, *args, **kwargs):

                if hasattr(self_wrapper, 'source'):
                    source = getattr(self_wrapper, 'source')
                else:
                    source = self.SOURCE_ALL
                    
                if not self.bypass(source,step):
                    
                    # Appel à la méthode de classe
                    result = func(self_wrapper, *args, **kwargs)

                    # Accéder aux données de l'instance de MyClass
                    if format == self.FORMAT_DATAFRAME:
                        self.snapshot_dataframe(source,step,self_wrapper.df)
                    elif format == self.FORMAT_DICTS:
                        self.snapshot_dicts(source,step,self_wrapper.dico_2022_marche,self_wrapper.dico_2022_concession)
                    elif format is None:
                        self.snapshot(source,step)
                else:
                    result = None
                    if format == self.FORMAT_DATAFRAME:
                        self_wrapper.df = self.resume(source,step,format)
                    elif format == self.FORMAT_DICTS:
                        self_wrapper.dico_2022_marche,self_wrapper.dico_concession = self.resume_dicts(source,step,format)

                return result
            return inner_wrapper
        return wrapper


    def snapshot(self,source:str,step:Step):
        self._update_status(source,step)


    def snapshot_dataframe(self,source:str,step:Step,df:pd.DataFrame):
        path = self._get_snapshot_path(source,step,self.FORMAT_DATAFRAME)
        df.to_pickle(path)
        self._update_status(source,step)


    def snapshot_dict(self,source:str,step:Step,dc:dict):
        path = self._get_snapshot_path(source,step,self.FORMAT_DICT)
        with open(path, 'w', encoding="utf-8") as f:
            json.dump(dc, f, indent=2, ensure_ascii=False)
        self._update_status(source,step)


    def snapshot_dicts(self,source:str,step:Step,dc_marche:dict,dc_concession:dict):
        path = self._get_snapshot_path(source,step,self.FORMAT_DICTS+'_marche')
        with open(path, 'w', encoding="utf-8") as f:
            json.dump(dc_marche, f, indent=2, ensure_ascii=False)
        path = self._get_snapshot_path(source,step,self.FORMAT_DICTS+'_concession')
        with open(path, 'w', encoding="utf-8") as f:
            json.dump(dc_concession, f, indent=2, ensure_ascii=False)
        self._update_status(source,step)


    def resume(self,source:str,step:Step,format:str) -> pd.DataFrame|dict:
        path = self._get_snapshot_path(source,step,format)
        if os.path.exists(path):
            if format == self.FORMAT_DATAFRAME:
                return pd.read_pickle(path)
            else:
                with open(path, encoding="utf-8") as json_file:
                    return json.load(json_file)
        return None

    def resume_dicts(self,source:str,step:Step,format:str) -> tuple[dict,dict]:
        path = self._get_snapshot_path(source,step,format+'_marche')
        if os.path.exists(path):
            with open(path, encoding="utf-8") as json_file:
                dico_marche = json.load(json_file)
        path = self._get_snapshot_path(source,step,format+'_concession')
        if os.path.exists(path):
            with open(path, encoding="utf-8") as json_file:
                dico_concession = json.load(json_file)
        return dico_marche, dico_concession


    def bypass(self,source:str,step:Step) -> pd.DataFrame|dict:
        init_status = self._check_init_status(source)
        if init_status == Step.NONE:                # Previous launchnot found, need to process operation
            return False
        elif init_status.value == step.value:       # Previous launch end here, need to process operation
            return True
        elif init_status.value < step.value:        # Previous launch ended earlier, need to process operation
            return False
        elif init_status.value > step.value:        # Previous launch ended further, just continue
            logging.info(f"PASS step {step}")
            return True


    def restore_point(self,source:str,step:Step,format:str,data:pd.DataFrame|dict) -> pd.DataFrame|dict:
        init_status = self._check_init_status(source)
        if init_status == Step.NONE:
            self.snapshot(source,step)
            return data
        elif init_status.value == Step.value:
            return self.resume(source,step,format)
        elif init_status.value < step.value:    # Previous launch ended earlier, need to process operation
            return data
        elif init_status.value > Step.value:    # Previous launch ended further, just continue
            return None


    def reset(self):
        self.current_status = {}
        self.init_status = {}
        with open(self.STATUS_FILEPATH, 'w') as json_file:
            json.dump(self.current_status, json_file)
        self._empty_directory(self.BASE_PATH)


    def _get_snapshot_path(self,source:str,step:Step,format:str) -> str:
        return self.BASE_PATH + source + '_'+ step.name + '_' + format + '.pkl'


    def _check_init_status(self,source:str):
        if source in self.init_status:
            return Step(self.init_status[source])
        else:
            return Step.NONE


    def _update_status(self,source:str,step:Step):

        self.current_status[source] = step.value

        with open(self.STATUS_FILEPATH, 'w') as json_file:
            json.dump(self.current_status, json_file)

    def _empty_directory(self,path):
        # Vérifie si le répertoire existe
        if os.path.exists(path):
            for fichier in os.listdir(path):
                if not fichier == '.gitignore':
                    chemin_complet = os.path.join(path, fichier)
                    if os.path.isdir(chemin_complet):
                        shutil.rmtree(chemin_complet)
                    else:
                        os.remove(chemin_complet)


if __name__ == '__main__':
    s = StepMngmt()
    s._update_status('source',Step.CLEAN)