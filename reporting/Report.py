from datetime import datetime
import pandas as pd
import json
import os

from database.Db import Db

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
    nb_in_good_marches = 0;
    nb_in_good_concessions = 0;
    nb_duplicated_marches = 0;
    nb_duplicated_concessions = 0;
    nb_out_bad_marches = 0
    nb_out_bad_concessions = 0

    # Constructor
    def __init__(self, application:str):
        self.application = application
        self.init()
        self.db = Db()
        self.session = self.db.add_session('decp-rama')

    # Init statistics
    def init(self):
        self.nb_in_bad_marches = 0;
        self.nb_in_bad_concessions = 0;
        self.nb_in_good_marches = 0;
        self.nb_in_good_concessions = 0;
        self.nb_duplicated_marches = 0;
        self.nb_duplicated_concessions = 0;
        self.nb_out_bad_marches = 0
        self.nb_out_bad_concessions = 0

    # Add a message record from dictionary or panda dataframe
    def add(self,step:str,code_erreur:str,message:str,data):
        if isinstance(data, list):
            for i in range(0,len(data)):
                if 'report__file' in data[i]:
                    file_name = data[i]['report__file']
                    del data[i]['report__file']
                else:
                    file_name = None
                if 'source' in data[i]:
                    source = data[i]['source']
                else:
                    source = None
                if 'report__position' in data[i]:
                    position = int(float(data[i]['report__position']))
                    del data[i]['report__position']
                else:
                    position = None
                if 'report__error' in data[i]:
                    error = data[i]['report__error']
                    del data[i]['report__error']
                else:
                    error = None
                if 'report__path' in data[i]:
                    path = data[i]['report__path']
                    del data[i]['report__path']
                else:
                    path = None
                self.add_message(step,code_erreur,source,file_name,position,error,path,message,i,data[i])
        else:
            dic = []
            for i in range(0,len(data)):
                dic.append(data.iloc[i].to_dict())
            self.add(step,code_erreur,message,dic)

    # Add a message load file failed from dictionary or panda dataframe
    def add_fail(self,step:str,code_erreur:str,error:str,source:str,file_name:str):
        self.add_message(step,code_erreur,source,file_name,0,error,'','',0,[])

    # Add a message record
    def add_message(self,step:str,code_erreur:str,source:str,file_name:str,position:int,error:str,path:str,message:str,index,data):
        if source not in self.messages:
            self.messages[source] = {code_erreur: []}
        if code_erreur not in self.messages[source]:
            self.messages[source][code_erreur] = []
        self.messages[source][code_erreur].append({'index': index, 'error': error, 'path': path, 'position': position,'message': message, 'step': step, 'file': file_name, 'date': datetime.now().strftime('%Y-%m-%d'),'data': data})
        self.db_add_report(step,code_erreur,source,file_name,position,error,path,message,data)

    def db_add_report(self,step:str,code_erreur:str,source:str,file_name:str,position:int,error:str,path:str,message:str,data):
        step_id = self.db.find_or_add_step(step)
        source_id = self.db.find_or_add_source(source)
        file_id = self.db.find_or_add_file(file_name,source_id,0,0)
        exclusion_type_id = self.db.find_or_add_exclusion_type(code_erreur)

        self.db.add_report(self.session, step_id, source_id, file_id, exclusion_type_id, message, error, path, position, data)
        
    def db_add_file(self,source:str,file_name:str, nb_marches:int, nb_concessions:int):
        source_id = self.db.find_or_add_source(source)
        self.db.find_or_add_file(file_name,source_id,nb_marches,nb_concessions)
        
    def db_end_session(self,message:str):
        self.db.end_session(self.session,message)
        

    # Save data report and statistics to files 
    def save(self):
        self.save_report()
        self.save_statistics()
    
    # Save data report to a file
    def save_report(self):
        title = 'Liste des erreurs ayant conduit à la suppression des marchés ou des concessions du résultat'
        currentday = datetime.now().strftime('%Y-%m-%d')
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
            'date': datetime.now().strftime('%Y-%m-%d'),
            'Marchés non valides en entrée': self.nb_in_bad_marches,
            'Concessions non valides en entrée': self.nb_in_bad_concessions,
            'Marchés valides en entrée': self.nb_in_good_marches,
            'Concessions valides en entrée': self.nb_in_good_concessions,
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
        currentday = datetime.now().strftime('%Y-%m-%d')
        json_data = {
            'title': title,
            'date': currentday,
            'sources': self.statistics
            }
        with open(f"results/{currentday}-statistics.json", 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
