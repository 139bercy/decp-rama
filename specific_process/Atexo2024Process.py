from general_process.SourceProcess import ProcessParams, SourceProcess
import logging
import os
import pandas as pd
import re
import shutil
import wget


class Atexo2024Process(SourceProcess):
    def __init__(self,params:ProcessParams):
        super().__init__("atexo_2024",params=params)

    def _url_init(self):
        super()._url_init()

    def filter_urls(self, url, title, url_date):
        
        filtered_url = []
        filtered_title = []
        filtered_date = []
        for u, t, d in zip(url, title, url_date):
            token = t.rsplit('-', 1)[-1][0:4]
            date_from_file_name = pd.to_datetime((token if token.isdigit() and len(token) == 4 else None) + '-12-31 23:59:59').tz_localize(None)
            date = pd.to_datetime(d).tz_localize(None)
            if date_from_file_name < date:
                date = date_from_file_name
            if self.start_date<date and date<=self.end_date: 
                filtered_url.append(u)
                filtered_title.append(t)
                filtered_date.append(date)
            url = filtered_url
            title = filtered_title
            url_date = filtered_date
        return super().filter_urls(filtered_url,filtered_title, filtered_date)
    

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
        

