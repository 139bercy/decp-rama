from general_process.SourceProcess import SourceProcess


import json


class PesNouveauProcess(SourceProcess):
    def __init__(self,data_format):
        super().__init__("pes2024",data_format)

    def get(self):
        # TODO implement load of data
        super().get()
        #None
        
    def fix(self):
        super().fix()
