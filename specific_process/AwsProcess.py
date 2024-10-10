from general_process.SourceProcess import SourceProcess


class AwsProcess(SourceProcess):
    def __init__(self,data_format):
        super().__init__("aws",data_format)

    def _url_init(self):
        super()._url_init()

    def fix(self):
        super().fix()
        # self.df['dureeMois'] = self.df['dureeMois'].astype(str)
        # self.df['montant'] = self.df['montant'].astype(str)
        # On se ramène au format souhaité pour titulaires, modifications et concessionnaires
        if 'modifications' in self.df.columns:
            self.df['modifications'] = [x if str(x) == 'nan' or str(x) == '[]'
                                        else ([{'modification': [y for y in x]}] if len(x) > 1
                                            else [{'modification': x[0]}])
                                        for x in self.df['modifications']]
        if 'titulaires' in self.df.columns:
            self.df['titulaires'] = [x if str(x) == 'nan' or str(x) == '[]'
                                    else ([{'titulaire': [y for y in x]}] if len(x) > 1 else [{'titulaire': x[0]}])
                                    for x in self.df['titulaires']]
        if 'concessionnaires' in self.df.columns:
            self.df['concessionnaires'] = [x if str(x) == 'nan' or str(x) == '[]'
                                        else ([{'concessionnaire': [y for y in x]}]
                                                if len(x) > 1 else [{'concessionnaire': x[0]}])
                                        for x in self.df['concessionnaires']]

        # cette étape permet de gérer les différences de formats entre XML et Json convertis en dataframe
        if 'modifications' in self.df.columns:
            for modification_dict in self.df['modifications']:
                if len(modification_dict) > 0:
                    modifications = modification_dict[0]['modification']
                    if type(modifications) is list:
                        for i in range(len(modifications)):
                            if 'titulaires' in modification_dict[0]['modification'][i]:
                                modifs_titulaire = modification_dict[0]['modification'][i]['titulaires']
                                if modifs_titulaire : # Certains nouveaux formats de données renvoient des listes vides de modifs de titulaires.
                                    modification_dict[0]['modification'][i]['titulaires'] = \
                                        ([modifications for modifications in modifs_titulaire]) if len(modifs_titulaire) > 1 else [modifs_titulaire[0]]
                    else:
                        if 'titulaires' in modification_dict[0]['modification']:
                            modifs_titulaire = modification_dict[0]['modification']['titulaires']
                            # Dans les données si il y a un champ titulaire vide, ça crash. Corrigeons ça
                            if modifs_titulaire:
                                modification_dict[0]['modification']['titulaires'] = \
                                    ([modifications for modifications in modifs_titulaire]) if len(modifs_titulaire) > 1 else [modifs_titulaire[0]]
                            # Sinon on fait rien car le champ titulaire est vide.
