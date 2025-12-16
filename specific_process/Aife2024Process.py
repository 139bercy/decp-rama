from general_process.SourceProcess import ProcessParams, SourceProcess


import json
import numpy as np


class Aife2024Process(SourceProcess):
    def __init__(self, params:ProcessParams):
        super().__init__("aife_2024",params=params)

    def _url_init(self):
        super()._url_init()

    def get(self):
        super().get()

    def convert(self):
        super().convert()
        
    def fix(self):
        super().fix()
    
    def old_code_no_more_need(self):
        def normalize_list(node,element_name:str):
            lst = []
            if element_name in node and isinstance(node[element_name],list): 
                lst.clear()
                for i in range(0,len(node[element_name])):
                    lst.append({element_name: node[element_name][i]})
            elif isinstance(node,dict):
                lst = [node]
            return lst

        def trans(x,sub_element:str):
            """
            Cette fonction transforme correctement les modifications.
            """
            modifs = []
            if len(x)>0 and isinstance(x,list) and isinstance(x[0],dict):
                x_ = x[0][sub_element]
                if isinstance(x_,list): # Certains format sont des listes d'un élement. Format rare mais qui casse tout.
                    # deleted x_ = x_[0].copy()
                    modifs.clear()
                    for i in range(0,len(x_)):
                        if 'modification' == sub_element and 'titulaires' in x_[i] and not isinstance(x_[i]['titulaires'],list): 
                            x_[i]['titulaires'] = normalize_list(x_[i]['titulaires'],'titulaire')
                        modifs.append({sub_element: x_[i]})
                    x = [{sub_element: modifs}]
                elif isinstance(x_,dict):
                    if 'modification' == sub_element and 'titulaires' in x_ and not isinstance(x_['titulaires'],list): 
                        x_['titulaires'] = normalize_list(x_['titulaires'],'titulaire')
                    x = [{sub_element: { sub_element: x_}}]
            return x
        # On enlève les OrderedDict et on se ramène au format souhaité
        if 'titulaires' in self.df:
            self.df['titulaires'] = self.df['titulaires'].apply(
                lambda x: x if x is None or type(x) == list else [x])
            self.df['titulaires'] = self.df["titulaires"].apply(trans,sub_element='titulaire')

        if 'modifications' in self.df:
            self.df['modifications'] = self.df['modifications'].apply(
                lambda x: x if x is None else json.loads(json.dumps(x)))
            self.df['modifications'] = self.df['modifications'].apply(
                lambda x: x if type(x) == list else [] if x is None else [x])
            self.df['modifications'] = self.df["modifications"].apply(trans,sub_element='modification')
        