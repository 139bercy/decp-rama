import logging
import os
from general_process.SourceProcess import ProcessParams, SourceProcess

class Modula2024Process(SourceProcess):
    def __init__(self,params:ProcessParams):
        super().__init__("modula_2024",params=params)

    def _url_init(self):
        super()._url_init()

    def get(self) -> None:
        super().get()
        """
        Étape de conversion de l'envodage
        """
        os.makedirs(f"sources/{self.source}", exist_ok=True)
        if self.cle_api==[]:
            logging.info("Pas de clé api pour encoder les données")
            self._download_without_metadata()
        else:
            # Rencodage du fichier
            for i in range(len(self.url)):                
                with open(f"sources/{self.source}/{self.title[i]}", encoding='ISO-8859-1') as f:
                    content = f.read()

                #with open(f"sources/{self.source}/{self.title[i]}", 'w', encoding='utf-8') as f:
                #    f.write(content)
        logging.info(f"Encodage : {len(self.url)} fichier(s) OK")

    def convert(self):
        super().convert()
        
    def fix(self):
        super().fix()
