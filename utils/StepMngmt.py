import json
import pandas as pd
from utils.Step import Step

class StepMngmt:
    _instance = None

    BASE_PATH = 'process/'
    STATUS_FILEPATH = 'process/run_status.json'
    
    FORMAT_DICT = 'dict'
    FORMAT_DATAFRAME = 'dataframe'

    SOURCE_ALL = 'ALL'

    init_status = {}
    current_status = {}


    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(StepMngmt, cls).__new__(cls)
            cls._instance.load_data()  # Charger les données lors de l'initialisation
        return cls._instance

    def load_data(self):
        # Charger les données depuis un fichier JSON
        try:
            with open(self.STATUS_FILEPATH, 'r') as json_file:
                self.init_status = json.load(json_file)

            with open(self.STATUS_FILEPATH, 'r') as json_file:
                self.current_status = json.load(json_file)

            print("Données chargées :", self.current_status)
        except FileNotFoundError:
            print("Le fichier data.json n'a pas été trouvé.")
            self.current_status = {}

    def __init__DEPRECATED(self):
        with open(self.STATUS_FILEPATH, 'r') as json_file:
            self.init_status = json.load(json_file)

        with open(self.STATUS_FILEPATH, 'r') as json_file:
            self.current_status = json.load(json_file)


    def decorator(self, source:str,step:Step,format:str):
        def wrapper(func):
            def inner_wrapper(self_wrapper, *args, **kwargs):

                if not self.bypass(source,step,format):
                    
                    # Opération avant l'appel à la méthode
                    print(f"Avant l'appel à {func.__name__} avec paramètre: {source},{step},{format}, données classe: {self.bypass(source,step,format)}")

                    # Appel à la méthode de classe
                    result = func(self_wrapper, *args, **kwargs)

                    # Opération après l'appel à la méthode
                    print(f"Après l'appel à {func.__name__} avec paramètre: {source},{step},{format}")

                    # Accéder aux données de l'instance de MyClass
                    if format == self.FORMAT_DATAFRAME:
                        self.snapshot_dataframe(source,step,self_wrapper.df)
                    else:
                        self.snapshot_dict(source,step,self_wrapper.dico)
                else:
                    result = None
                    if format == self.FORMAT_DATAFRAME:
                        self_wrapper.df = self.resume(source,step,format)
                    else:
                        self_wrapper.dico = self.snapshot(source,step,format)

                return result
            return inner_wrapper
        return wrapper
    
    def snapshot_dataframe(self,source:str,step:Step,df:pd.DataFrame):
        path = self._get_snapshot_path(source,step,self.FORMAT_DATAFRAME)
        df.to_pickle(path)
        self._update_status(source,step)


    def snapshot_dict(self,source:str,step:Step,dc:dict):
        path = self._get_snapshot_path(source,step,self.FORMAT_DICT)
        with open(path, 'w', encoding="utf-8") as f:
            json.dump(dc, f, indent=2, ensure_ascii=False)
        self._update_status(source,step)


    def resume(self,source:str,step:Step,format:str) -> pd.DataFrame|dict:
        path = self._get_snapshot_path(source,step,format)
        if format == self.FORMAT_DATAFRAME:
            return pd.read_pickle(path)
        else:
            with open(path, encoding="utf-8") as json_file:
                return json.load(json_file)


    def bypass(self,source:str,step:Step,format:str) -> pd.DataFrame|dict:
        init_status = self._check_init_status(source)
        if init_status == Step.NONE:
            return False
        elif init_status.value == step.value:   # Previous launch end here, need to process operation
            return True
        elif init_status.value < step.value:    # Previous launch ended earlier, need to process operation
            return False
        elif init_status.value > Step.value:    # Previous launch ended further, just continue
            return True


    def restore_point(self,source:str,step:Step,format:str,data:pd.DataFrame|dict) -> pd.DataFrame|dict:
        init_status = self._check_init_status(source)
        if init_status == Step.NONE:
            self.snapshot(source,step,data)
            return data
        elif init_status.value == Step.value:
            return self.resume(source,step,format)
        elif init_status.value < step.value:    # Previous launch ended earlier, need to process operation
            return data
        elif init_status.value > Step.value:    # Previous launch ended further, just continue
            return None

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




if __name__ == '__main__':
    s = StepMngmt()
    s._update_status('source',Step.CLEAN)