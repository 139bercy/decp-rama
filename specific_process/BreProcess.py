from general_process.SourceProcess import SourceProcess
import logging
import os
import os
import json
import pandas as pd
import xmltodict
import re

class BreProcess(SourceProcess):
    def __init__(self,data_format):
        super().__init__("bre",data_format)

    def _url_init(self):
        self.metadata[self.key]["url"] = [self.metadata[self.key]["url_source"]]
        self.url = self.metadata[self.key]["url"]
        self.file_name = [f"{self.metadata[self.key]['code']}_{i}" for i in range(len(self.url))]

    def get(self):
        super().get()

    def convert(self):
        """Étape de conversion des fichiers qui supprime les ' et concatène les fichiers présents
        dans {self.source} dans un seul DataFrame"""
        logging.info("  ÉTAPE CONVERT")
        # suppression des '
        count = 0
        repertoire_source = f"sources/{self.source}"
        for path in os.listdir(repertoire_source):
            if os.path.isfile(os.path.join(repertoire_source, path)):
                count += 1
        for i in range(count):
            file_path = f"sources/{self.source}/{self.file_name[i]}.{self.format}"
            with open(file_path) as file:
                chaine = re.sub("\'", " ", file.read())
            with open(file_path, "w") as file:
                file.write(chaine)
        if count != len(self.url):
            logging.warning("Nombre de fichiers en local inégal au nombre d'url trouvé")
        logging.info(f"Début de convert: mise au format DataFrame de {self.source}")
        if self.format == 'xml':
            li = []
            for i in range(count):
                with open(
                        f"sources/{self.source}/{self.file_name[i]}.{self.format}", encoding="utf-8") as xml_file:
                        dico = xmltodict.parse(xml_file.read(), dict_constructor=dict)
                if dico['csv'] is not None:
                    df = pd.DataFrame.from_dict(dico['csv']['marche'])
                else:
                    logging.warning(f"Le fichier {self.file_name[i]} est vide, il est ignoré")
                self._add_column_type(df,"Concession")
                li.append(df)
            df = pd.concat(li)
            df = df.reset_index(drop=True)
            self.df = df
        logging.info("Conversion OK")
        logging.info(f"Nombre de marchés dans {self.source} après convert : {len(self.df)}")

    def fix(self):
        """
        On a des problèmes avec acheteur_id et acheteur_nom qui sont séparés dans ce xml. Groupons les.
        On a également des strign étrange. Toutes les valeurs dans titulaires_denominationLegale se finissent par des |, on les retire.
        """
        self.df.loc[:, "titulaires_denominationLegale"] = self.df.loc[:, "titulaires_denominationLegale"].str.replace("|||||||||||||||", "", regex=False)
        self.df["acheteur"] = [{"id":x, "nom":y} for (x,y) in zip(self.df.loc[:, "acheteur_id"], self.df.loc[:, "acheteur_nom"])]
        rename_mapping = {"acheteur_id" :"acheteur.id", "acheteur_nom":"acheteur.nom",
        "lieuExecution_code" : "lieuExecution.code", "lieuExecution_typeCode" : "lieuExecution.typeCode",
        "lieuExecution_nom":"lieuExecution.nom",  }
        # Mettre titulaires dans une liste
        self.df["titulaires"] = [{"typeIdentifiant":x ,"id":y, "denominationSociale":z} for (x,y, z) in zip(self.df.loc[:, "titulaires_typeIdentifiant"], self.df.loc[:, "titulaires_id"], self.df.loc[:, "titulaires_denominationLegale"])]
        self.df["titulaires"] = self.df["titulaires"].apply(lambda x:[{"titulaire":x}]) # Pour respecter la forme du reste des données
        self.df = self.df.rename(columns=rename_mapping)
        columns_to_drop = ["Annee", "titulaires_typeIdentifiant", "titulaires_id", "titulaires_denominationLegale"]
        self.df = self.df.drop(columns_to_drop, axis=1)

