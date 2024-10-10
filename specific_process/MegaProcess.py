import logging

from general_process.SourceProcess import SourceProcess


class MegaProcess(SourceProcess):
    def __init__(self,data_format):
        super().__init__("mega",data_format)

    def _url_init(self):
        super()._url_init()

    def get(self):
        super().get()

    def convert(self):
        print("Début de la fonction convert de MegaProcess")
        # les fichiers xml de megalis ne sont pas au bon format
        for i in range(len(self.url)):
            with open(f"sources/{self.source}/{self.title[i]}", 'r', encoding='utf-8') as file:
                data = file.read().splitlines(True)
            with open(f"sources/{self.source}/{self.title[i]}", 'w', encoding='utf-8') as file:
                file.write('<?xml version= "1.0"  encoding= "utf8" ?>\n')
                file.writelines(data[1:])
        print("Début de la fonction convert de SourceProcess")
        super().convert()
        print("Fin de la fonction convert de SourceProcess")
        print("Fin de la fonction convert de MegaProcess")

    def fix(self):
        print("Début de la fonction fix de MegaProcess")
        # if df is empty then return
        if len(self.df) == 0:
            logging.warning(f"Le fichier {self.source} est vide, il est ignoré")
            return
        print("Début de la fonction fix de SourceProcess")
        super().fix()
        print("Fin de la fonction fix de SourceProcess")
        self.df['titulaires'] = self.df['titulaires'].apply(
            lambda x: x if x is None or type(x) == list else [x])
        # Dans Megalis, il n'y a pas de colonne modifications, donc on l'ajoute
        if 'modifications' not in self.df.columns:
            self.df['modifications'] = self.df['titulaires'].apply(lambda x: [])
        print("Fin de la fonction fix de MegaProcess")

