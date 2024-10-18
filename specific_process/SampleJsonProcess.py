from general_process.SourceProcess import SourceProcess
import json


class SampleJsonProcess(SourceProcess):
    def __init__(self,data_format):
        super().__init__("sample_json",data_format)

    def _url_init(self):
        super()._url_init()

    def get(self):
        super().get()

    def convert(self):
        super().convert()

    def fix(self):
        self.df = self.df.reset_index(drop=True)
        super().fix()
        def trans(x):
            """
            Cette fonction transforme correctement les modifications.
            """
            if len(x)>0:
                x_ = x[0]['modification']
                if type(x_)==list: # Certains format sont des listes d'un élement. Format rare mais qui casse tout.
                    x_ = x_[0].copy()
                if "titulaires" in x_.keys():
                    if type(x_["titulaires"])==dict:
                        x_['titulaires'] = x_['titulaires']
                    
            return x
                
        if 'titulaires' in self.df.columns:
            bool_nan_titulaires = ~self.df.loc[:, "titulaires"].isna()
            self.df.loc[bool_nan_titulaires, "titulaires"] = self.df.loc[bool_nan_titulaires, "titulaires"].apply(
                lambda x: x if x is None or type(x) == list else x['titulaire'] 
                    if type(x['titulaire']) == list else [x['titulaire']])
        if 'modifications' in self.df.columns:
            self.df['modifications'] = self.df['modifications'].apply(
                lambda x: x if x is None else json.loads(json.dumps(x)))
            if self.data_format=='2019':
                self.df['modifications'] = self.df['modifications'].apply(
                    lambda x: x if type(x) == list else [] if x is None else [x])
        #self.df['modifications'] = self.df["modifications"].apply(trans)