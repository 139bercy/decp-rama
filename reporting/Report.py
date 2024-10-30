from datetime import datetime
import pandas as pd
import json
import os

# Class for managing reports about records which are excluded from results during processibg
class Report:

    E_VALIDATION = 'E_VALIDATION'
    D_DUPLICATE = 'E_DUPLICATE'
    
    # Class members
    application = None          # Application launching this instance
    messages = {}                # Dict of reporting message about stream process to log 
    statistics = []
    nb_in_bad_marches = 0;
    nb_in_bad_concessions = 0;
    nb_in_marches = 0;
    nb_in_concessions = 0;
    nb_duplicated_marches = 0;
    nb_duplicated_concessions = 0;
    nb_out_bad_marches = 0
    nb_out_bad_concessions = 0

    # Constructor
    def __init__(self, application:str):
        self.application = application
        self.init()

    # Init statistics
    def init(self):
        self.nb_in_bad_marches = 0;
        self.nb_in_bad_concessions = 0;
        self.nb_in_marches = 0;
        self.nb_in_concessions = 0;
        self.nb_duplicated_marches = 0;
        self.nb_duplicated_concessions = 0;
        self.nb_out_bad_marches = 0
        self.nb_out_bad_concessions = 0

    # Add a message record from dictionary or panda dataframe
    def add(self,step:str,code_erreur:str,message:str,data):
        if isinstance(data, list):
            for i in range(0,len(data)):
                file_name = data[i]['file']
                del data[i]['file']
                source = data[i]['source']
                del data[i]['source']
                if 'error_validation' in data[i]:
                    error = data[i]['error_validation']
                    del data[i]['error_validation']
                else:
                    error = None
                self.add_message(step,code_erreur,source,file_name,error,message,i,data[i])
        else:
            dic = []
            for i in range(0,len(data)):
                dic.append(data.iloc[i].to_dict())
            self.add(step,code_erreur,message,dic)

    # Add a message load file failed from dictionary or panda dataframe
    def add_fail(self,step:str,code_erreur:str,error:str,source:str,file_name:str):
        self.add_message(step,code_erreur,source,file_name,error,'',0,[])

    # Add a message record
    def add_message(self,step:str,code_erreur:str,source:str,file_name:str,error:str,message:str,index,data):
        if source not in self.messages:
            self.messages[source] = {code_erreur: []}
        if code_erreur not in self.messages[source]:
            self.messages[source][code_erreur] = []
        self.messages[source][code_erreur].append({'index': index, 'error': error, 'message': message, 'step': step, 'file': file_name, 'data': data})

    # Save data report and statistics to files 
    def save(self):
        self.save_report()
        self.save_statistics()
    
    # Save data report to a file
    def save_report(self):
        title = 'Liste des erreurs ayant conduit à la suppression des marchés ou des concessions du résultat'
        currentday = f"{datetime.now().year}-{datetime.now().month}-{datetime.now().day}"
        json_data = {
            'title': title,
            'date': currentday,
            'sources': self.messages
            }
        with open(f"results/{currentday}-errors.json", 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

    # Save in memory current statistics and reinit statistics 
    def fix_statistics (self,source):
        self.statistics.append ({'source': {
            'name': source, 
            'Marchés non valides en entrée': self.nb_in_bad_marches,
            'Concessions non valides en entrée': self.nb_in_bad_concessions,
            'Marchés valides en entrée': self.nb_in_marches,
            'Concessions valides en entrée': self.nb_in_concessions,
            'Doublons de marchés supprimés': self.nb_duplicated_marches,
            'Doublons de concessions supprimées': self.nb_duplicated_concessions,
            'Marchés erronés en sortie' : self.nb_out_bad_marches,
            'Concessions erronées en sortie': self.nb_out_bad_concessions
            }
        })
        self.init()
    
    # Save statistics to a file 
    def save_statistics(self):
        title = 'Nombre de marchés et de concessions en entrées de rama par sources'
        currentday = f"{datetime.now().year}-{datetime.now().month}-{datetime.now().day}"
        json_data = {
            'title': title,
            'date': currentday,
            'sources': self.statistics
            }
        with open(f"results/{currentday}-statistics.json", 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
