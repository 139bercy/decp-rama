from general_process.SourceProcess import SourceProcess
import logging
import os
import shutil
import wget


class MaxiProcess(SourceProcess):
    def __init__(self,data_format):
        super().__init__("maxi",data_format)

    def _url_init(self):
        super()._url_init()

    def get(self):
         super().get()

    def convert(self):
        super().convert()

    def fix(self):
        super().fix()

