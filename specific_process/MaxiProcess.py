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
        """Étape get qui permet le lavage du dossier sources/{self.source} et la récupération de
        l'ensemble des fichiers présents sur chaque url.
        AJOUT d'un try except car certaines URL ne sont plus bonnes (je suppose donc qu'elles peuvent être down)"""
        logging.info("  ÉTAPE GET")
        # Lavage des dossiers dans "sources"
        logging.info(f"Début du nettoyage de sources/{self.source}")
        if os.path.exists(f"sources/{self.source}"):
            shutil.rmtree(f"sources/{self.source}")
        logging.info(f"Nettoyage sources/{self.source} OK")
        # Étape get des url
        logging.info(f"Début du téléchargement : {len(self.url)} fichier(s)")
        self.file_name = [f"{self.metadata[self.key]['code']}_{i}" for i in range(len(self.url))]
        os.makedirs(f"sources/{self.source}", exist_ok=True)
        for i in range(len(self.url)):
            try:
                wget.download(self.url[i], f"sources/{self.source}/{self.file_name[i]}.{self.format}")
            except:
                print(f" Le lien {self.url[i]} ne peut être téléchargé")
        logging.info(f"Téléchargement : {len(self.url)} fichier(s) OK")


    def convert(self):
        super().convert()

    def fix(self):
        super().fix()

