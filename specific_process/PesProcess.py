from general_process.SourceProcess import SourceProcess
import json


class PesProcess(SourceProcess):
    def __init__(self,data_format):
        super().__init__("pes",data_format)

    def fix(self):
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
                        x_['titulaires'] = x_['titulaires']['titulaire']
            return x
        # On enlève les OrderedDict et on se ramène au format souhaité
        self.df['titulaires'] = self.df['titulaires'].apply(
            lambda x: x if x is None or type(x) == list else [x])
        self.df['modifications'] = self.df['modifications'].apply(
            lambda x: x if x is None else json.loads(json.dumps(x)))
        self.df['modifications'] = self.df['modifications'].apply(
            lambda x: x if type(x) == list else [] if x is None else [x])
        self.df['modifications'] = self.df["modifications"].apply(trans)