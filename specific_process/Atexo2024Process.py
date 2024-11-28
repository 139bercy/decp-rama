from general_process.SourceProcess import SourceProcess
import logging
import os
import shutil
import wget


class Atexo2024Process(SourceProcess):
    def __init__(self,data_format,report):
        super().__init__("atexo_2024",data_format,report)

    def _url_init(self):
        super()._url_init()

    def get(self):
        super().get()

    def convert(self):
        super().convert()

    def fix(self):
        super().fix()

    def old_code_no_more_need(self):
        if 'modifications' in self.df.columns:
            self.df['modifications'] = [x if str(x) == 'nan' or str(x) == '[]'
                                        else ([{'modification': [y for y in x]}] if len(x) > 1
                                            else [{'modification': x[0]}])
                                        for x in self.df['modifications']]
        if 'titulaires' in self.df.columns:
            self.df['titulaires'] = [x if str(x) == 'nan' or str(x) == '[]'
                                    else ([{'titulaire': [y for y in x]}] if len(x) > 1 else [{'titulaire': x[0]}])
                                    for x in self.df['titulaires']]

        if 'modifications' in self.df.columns:
            if len(self.df['modifications']) > 0:
                for x in self.df['modifications']:
                    if 'modification' in self.df['modifications']:
                        y = x[0]['modification']
                        if type(y) is list:
                            for i in range(len(y)):
                                if 'titulaires' in x[0]['modification'][i]:
                                    z = x[0]['modification'][i]['titulaires']
                                    x[0]['modification'][i]['titulaires'] = \
                                        ([y for y in z]) if len(z) > 1 else [z[0]]
                        else:
                            if 'titulaires' in x[0]['modification']:
                                z = x[0]['modification']['titulaires']
                                x[0]['modification']['titulaires'] = \
                                    ([y for y in z]) if len(z) > 1 else [z[0]]
        

