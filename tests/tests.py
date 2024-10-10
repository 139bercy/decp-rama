import unittest
import numpy as np
import sys
import os
import json
import xmltodict
import pandas as pd


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
pd.options.mode.chained_assignment = None

# Ajoutez le chemin du projet au sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from specific_process import * 
from general_process import * 

class UneClasseDeTest(unittest.TestCase):

    def setUp(self):
        # Initialisation des données de test
        self.process = SampleJsonProcess("2022")
        self.processes = [SampleJsonProcess, SampleXmlProcess, PesNouveauProcess]
        self.global_process = GlobalProcess()
        self.url = []
        
        self.df = pd.DataFrame()

        
    
    def test_select_recent_url(self):
        """
        Test de la fonction check date file, on récupère seulement les fichiers
        qui sont plus récents que les anciens fichiers téléchargés.
        """
        
        old_ressources = [
            {"last_modified": "2022-01-02T00:00:00.000000+00:00", "url": "https://example.com/collectivite1.xml", "title": "Collectivite 1"},
            {"last_modified": "2023-04-02T00:00:00.000000+00:00", "url": "https://example.com/collectivite2.json", "title": "Collectivite 2"},
            {"last_modified": "2023-04-01T00:00:00.000000+00:00", "url": "https://example.com/collectivite3.json", "title": "Collectivite 3"},
            {"last_modified": "2023-01-02T00:00:00.000000+00:00", "url": "https://example.com/collectivite4.json", "title": "Collectivite 4"}
            ]
          


        new_ressources = [
            {"last_modified": "2023-01-01T00:00:00.000000+00:00", "url": "https://example.com/collectivite1.xml", "title": "Collectivite 1"},
            {"last_modified": "2023-04-02T00:00:00.000000+00:00", "url": "https://example.com/collectivite2.json", "title": "Collectivite 2"},
            {"last_modified": "2023-04-16T00:00:00.000000+00:00", "url": "https://example.com/collectivite3.json", "title": "Collectivite 3"},
            {"last_modified": "2023-01-02T00:00:00.000000+00:00", "url": "https://example.com/collectivite4.json", "title": "Collectivite 4"}
            ]
        
        title=[]
        resultats = self.process.check_date_file(self.url, title, new_ressources, old_ressources)

        # Vérification du résultat
        expected_url = (["https://example.com/collectivite1.xml","https://example.com/collectivite3.json"] ,["Collectivite 1", "Collectivite 3"])
        self.assertEqual(resultats, expected_url)
    
    # def test_date_before_2024(self):
    #     with open(f"tests/test_before2024.xml", encoding='utf-8') as xml_file:
    #         dico = xmltodict.parse(xml_file.read(), dict_constructor=dict)
    #     m = dico['marches']['marche']
    #     resultats= self.process.date_before_2024(m[0])
    #     expected_res=True
    #     self.assertEqual(resultats, expected_res)

    def test_date_after_2024(self):
        """
        Test de la fonction date_after_2024, on teste si la fonction détecte si le fichier date d'après 2024 ou non  
        """
        with open(f"tests/test_before2024.xml", encoding='utf-8') as xml_file:
            dico = xmltodict.parse(xml_file.read(), dict_constructor=dict)
        m = dico['marches']['marche']
        resultats= self.process.date_after_2024(m)#ici on séléctionne seulement le premier marché contenu dans m
        expected_res=False
        self.assertEqual(resultats, expected_res)

    def test_has_all_field_and_date_2024(self):
        """
        Test de la fonction has_all_field_and_date_2024, on test si les marchés/concessions possèdent bien les colonnes et les champs necessaires
        au format 2022 ainsi que leurs date.
        """
        with open(f"tests/test_before2024.xml", encoding='utf-8') as xml_file:
            dico = xmltodict.parse(xml_file.read(), dict_constructor=dict)
        m = dico['marches']['marche']
        resultats= self.process._has_all_field_and_date_2024(m,'marche')
        expected_res=False
        self.assertEqual(resultats, expected_res)

    # def test_retain_wit_format(self):
    #     """
    #     Test de la fonction retain_with_fomat, on vérifie que le dictionnaire en paramètre est valide par rapport à notre format 2022
    #     et trie les dictionnaire dans deux listes différentes, une pour les dico valide que l'on va traiter dans la suite du code
    #     et une autre pour les dico invalide que l'on va garder de coté
    #     """
    #     with open(f"tests/test_retain.json", encoding='utf-8') as json_file:
    #         dico = json.load(json_file)
    #     resultats= self.process._retain_with_format(dico,"testFile")
    #     expected_res ={ "marches": {
    #     "marche": [
    #         {
    #         "id": "TEST2022",
    #         "acheteur": {
    #             "id": "21750001630066"
    #         },
    #         "marcheInnovant": True,
    #         "origineUE": 0.1,
    #         "origineFrance": 0.1,
    #         "ccag": "Travaux",
    #         "offresRecues": 4,
    #         "formePrix": "Forfaitaire",
    #         "typesPrix": {
    #             "typePrix": [
    #             "Définitif ferme"
    #             ]
    #         },
    #         "considerationsEnvironnementales": {
    #             "considerationEnvironnementale": [
    #             "Clause environnementale"
    #             ]
    #         },
    #         "attributionAvance": True,
    #         "considerationsSociales": {
    #             "considerationSociale": [
    #             "Clause sociale",
    #             "Critère social"
    #             ]
    #         },
    #         "nature": "Marché",
    #         "objet": "envoi pour Json test 1",
    #         "codeCPV": "45000000-7",
    #         "techniques": {
    #             "technique": [
    #             "Concours",
    #             "Accord-cadre"
    #             ]
    #         },
    #         "modalitesExecution": 
    #         {
    #             "modaliteExecution": [
    #                 "Tranches"]}
    #         ,
    #         "idAccordCadre": "1234567890",
    #         "tauxAvance": 0,
    #         "titulaires": [
    #             {
    #             "titulaire": {
    #                 "id": "55204599900869",
    #                 "typeIdentifiant": "SIRET"
    #             }
    #             }
    #         ],
    #         "typeGroupementOperateurs": "Pas de groupement",
    #         "sousTraitanceDeclaree": True,
    #         "datePublicationDonnees": "2024-05-25",
    #         "actesSousTraitance": [
    #             {
    #             "acteSousTraitance": {
    #                 "id": 1,
    #                 "sousTraitant": {
    #                 "id": "214356",
    #                 "typeIdentifiant": "SIRET"
    #                 },
    #                 "dureeMois": 12,
    #                 "dateNotification": "2024-10-11",
    #                 "montant": 123456.89,
    #                 "variationPrix": "Révisable",
    #                 "datePublicationDonnees": "2024-10-12"
    #             }
    #             }
    #         ],
    #         "modifications": [
    #             {
    #             "modification": {
    #                 "id": 1,
    #                 "dureeMois": 12,
    #                 "montant": 123457.87,
    #                 "titulaires": [
    #                 {
    #                     "titulaire": {
    #                     "id": "868768687576575",
    #                     "typeIdentifiant": "SIRET"
    #                     }
    #                 }
    #                 ],
    #                 "dateNotificationModification": "2024-10-18",
    #                 "datePublicationDonneesModification": "2024-10-20"
    #             }
    #             }
    #         ],
    #         "modificationsActesSousTraitance": [
    #             {
    #             "modificationActeSousTraitance": {
    #                 "id": 1,
    #                 "dureeMois": 12,
    #                 "dateNotificationModificationSousTraitance": "2024-10-20",
    #                 "montant": 23465.87,
    #                 "datePublicationDonnees": "2024-12-15"
    #             }
    #             }
    #         ],

    #         "procedure": "Appel d'offres ouvert",
    #         "lieuExecution": {
    #             "code": "75000",
    #             "typeCode": "Code postal"
    #         },
    #         "dureeMois": 48,
    #         "dateNotification": "2024-05-15",
    #         "montant": 575000
    #         }
    #         ]
    #         }
    #     }
    #     self.assertDictEqual(resultats,expected_res)

    def test_convert(self):
        """
        On teste la fonction convert, on part du principe que la fonction convert_prestataire fonctionne et renvoi un résultat valide
        donc on créer un dataframe qui correspond au résultat de la fonction convert_prestataire et on en créer un autre qui 
        correspond au résultat de notre fonction convert, on vérifie que ces deux dataframe sont identiques
        """
        self.process.dico_2022_marche = [
              {
        "id": "TEST2022",
        "acheteur": {
          "id": "21750001630066"
        },
        "marcheInnovant": False,
        "origineUE": 0.1,
        "origineFrance": 0.1,
        "ccag": "Travaux",
        "offresRecues": 4,
        "formePrix": "Forfaitaire",
        "typesPrix": {
          "typePrix": [
			"Définitif ferme"
		  ]
        },
        "considerationsEnvironnementales": {
          "considerationEnvironnementale": [
            "Clause environnementale"
          ]
        },
        "attributionAvance": "1",
        "considerationsSociales": {
          "considerationSociale": [
            "Clause sociale",
            "Critère social"
          ]
        },
        "nature": "Marché",
        "objet": "envoi pour Json test 1",
        "codeCPV": "45000000-7",
        "techniques": {
          "technique": [
            "Concours",
            "Accord-cadre"
          ]
        },
        "modalitesExecution": 
		{
			"modaliteExecution": [
			  "Tranches"]}
		,
		"idAccordCadre": "1234567890",
        "tauxAvance": 0,
        "titulaires": [
          {
            "titulaire": {
              "id": "55204599900869",
              "typeIdentifiant": "SIRET"
            }
          }
        ],
        "typeGroupementOperateurs": "Pas de groupement",
        "sousTraitanceDeclaree": True,
        "datePublicationDonnees": "2024-05-25",
        "actesSousTraitance": [
          {
            "acteSousTraitance": {
              "id": 1,
              "sousTraitant": {
                "id": "214356",
                "typeIdentifiant": "SIRET"
              },
              "dureeMois": 12,
              "dateNotification": "2023-10-11",
              "montant": 123456.89,
              "variationPrix": "Révisable",
              "datePublicationDonnees": "2023-10-12"
            }
          }
        ],
        "modifications": [
          {
            "modification": {
              "id": 1,
              "dureeMois": 12,
              "montant": 123457.87,
              "titulaires": [
                {
                  "titulaire": {
                    "id": "868768687576575",
                    "typeIdentifiant": "SIRET"
                  }
                }
			  ],
              "dateNotificationModification": "2022-10-18",
              "datePublicationDonneesModification": "2022-10-20"
            }
          }
		],
        "modificationsActesSousTraitance": [
          {
            "modificationActeSousTraitance": {
              "id": 1,
              "dureeMois": 12,
              "dateNotificationModificationSousTraitance": "2022-10-20",
              "montant": 23465.87,
              "datePublicationDonnees": "2022-12-15"
            }
          }
		],
        "procedure": "Appel d'offres ouvert",
        "lieuExecution": {
          "code": "75000",
          "typeCode": "Code postal"
        },
        "dureeMois": 48,
        "dateNotification": "2024-05-15",
        "montant": 575000
      },

      {
        "id": "TEST2022Bis",
        "acheteur": {
          "id": "21750001630040"
        },
        "marcheInnovant": "non",
        "origineUE": 0.1,
        "origineFrance": 0.1,
        "ccag": "Travaux",
        "offresRecues": 4,
        "formePrix": "Forfaitaire",
        "typesPrix": {
          "typePrix": [
			"Définitif ferme"
		  ]
        },
        "considerationsEnvironnementales": {
          "considerationEnvironnementale": [
            "Clause environnementale"
          ]
        },
        "attributionAvance": True,
        "considerationsSociales": {
          "considerationSociale": [
            "Clause sociale",
            "Critère social"
          ]
        },
        "nature": "Marché",
        "objet": "envoi pour Json test 2",
        "codeCPV": "45000000-7",
        "techniques": {
          "technique": [
            "Concours",
            "Accord-cadre"
          ]
        },
        "modalitesExecution": 
		{
			"modaliteExecution": [
				"Tranches"]
		}
		,
        "idAccordCadre": "1234567890",
        "tauxAvance": 0,
        "titulaires": [
          {
            "titulaire": {
              "id": "55204599900869",
              "typeIdentifiant": "SIRET"
            }
          }
        ],
        "typeGroupementOperateurs": "Pas de groupement",
        "sousTraitanceDeclaree": True,
        "datePublicationDonnees": "2024-05-25",
        "actesSousTraitance": [
          {
            "acteSousTraitance": {
              "id": 1,
              "sousTraitant": {
                "id": "214356",
                "typeIdentifiant": "SIRET"
              },
              "dureeMois": 12,
              "dateNotification": "2023-10-11",
              "montant": 123456.89,
              "variationPrix": "Révisable",
              "datePublicationDonnees": "2023-10-12"
            }
          }
        ],
        "modifications": [
          {
            "modification": {
              "id": 1,
              "dureeMois": 12,
              "montant": 123457.87,
              "titulaires": [
                {
                  "titulaire": {
                    "id": "868768687576575",
                    "typeIdentifiant": "SIRET"
                  }
                }
              ],
              "dateNotificationModification": "2022-10-18",
              "datePublicationDonneesModification": "2022-10-20"
            }
          }
		],
        "modificationsActesSousTraitance": [
          {
            "modificationActeSousTraitance": {
              "id": 1,
              "dureeMois": 12,
              "dateNotificationModificationSousTraitance": "2022-10-20",
              "montant": 23465.87,
              "datePublicationDonnees": "2022-12-15"
            }
          }
		],
        "procedure": "Appel d'offres ouvert",
        "lieuExecution": {
          "code": "75000",
          "typeCode": "Code postal"
        },
        "dureeMois": 48,
        "dateNotification": "2024-05-15",
        "montant": 575000
      }
        ]
        
        self.process.convert()
        expected_res=True
        df_notre= self.process.df

        self.process.convert_prestataire()
        df_prestataire = self.process.df

        resultats = df_notre.equals(df_prestataire)
        self.assertEqual(resultats, expected_res)


    def test_convert_boolean(self):

        #Création du dataframe modèle
        dico_modele = {
            "marches": {
                "marche": [
                {
                    "id": "TEST2022",
                    "acheteur": {
                    "id": "21750001630066"
                    },
                    "marcheInnovant": "oui",
                    "offresRecues": None,
                    "attributionAvance": "oui",
                    "sousTraitanceDeclaree": "oui"
                },
                {
                    "id": "TEST2021",
                    "acheteur": {
                    "id": None
                    },
                    "marcheInnovant": "non",
                    "offresRecues": 4,
                    "attributionAvance": "non",
                    "sousTraitanceDeclaree": "non"
                }
                ]
            }
        }
        df_modele = pd.DataFrame.from_dict(dico_modele['marches']['marche'])
        
        #Création du dataframe à tester
        with open (f"tests/test_fix.json", encoding='utf-8') as json_file1:
            json_data = json.load(json_file1)
        self.process.df = pd.DataFrame.from_dict(json_data['marches']['marche'])

        self.process.convert_boolean('marcheInnovant')
        self.process.convert_boolean('attributionAvance')
        self.process.convert_boolean('sousTraitanceDeclaree')

        print(" Dataframe modele :", df_modele)
        print(" Dataframe resultat :", self.process.df)

        expected_result = True
        real_result = self.process.df.equals(df_modele)

        self.assertEqual(expected_result,real_result)


    def test_fix(self):
        #Dans le fichier test_fix, le champ "offreRescue" est vide et celui du champ "acheteur" est vide
        #Création du dataframe modèle   #Attention, les colonnes doivent être du même type
        dico_modele = {
            "marches": {
                "marche": [
                {
                    "id": "TEST2022",
                    "acheteur": {
                        "id": "21750001630066"
                    },
                    "marcheInnovant": "oui",
                    "offresRecues": 0,
                    "attributionAvance": "oui",
                    "sousTraitanceDeclaree": "oui",
                    "source": "sample_json"
                },
                {
                    "id": "TEST2021",
                    "acheteur": {
                        "id": "TEST2021"
                    },
                    "marcheInnovant": "non",
                    "offresRecues": 4,
                    "attributionAvance": "non",
                    "sousTraitanceDeclaree": "non",
                    "source": "sample_json"
                }
                ]
            }
        }

        #Création du dataframe modele
        df_modele = pd.DataFrame.from_dict(dico_modele['marches']['marche'])
        df_modele["offresRecues"] = df_modele["offresRecues"].astype(int)

        #Création du dataframe testé 
        with open (f"tests/test_fix.json") as json_file:
            json_data = json.load(json_file)
        self.process.df = pd.DataFrame.from_dict(json_data['marches']['marche'])

        #Fonction à tester
        self.process.fix()

        # Affichage des DataFrames
        # print("Dataset modele : ", df_modele)
        # print("Dataset résultat : ", self.process.df)

        expected_result = True
        real_result = self.process.df.equals(df_modele)
        
        self.assertEqual(real_result, expected_result)


    def test_tri_format_json(self):
        with open(f"documents/marches_avec_modifications.json", encoding='utf8' ) as json_file1:
            dico1 = json.load(json_file1)

        #JSON
        self.process.tri_format(dico1,"test_tri")
        expected_result_json = [
      {
        "id": "TEST2022",
        "acheteur": {
          "id": "21750001630066"
        },
        "marcheInnovant": False,
        "origineUE": 0.1,
        "origineFrance": 0.1,
        "ccag": "Travaux",
        "offresRecues": 4,
        "formePrix": "Forfaitaire",
        "typesPrix": {
          "typePrix": [
			"Définitif ferme"
		  ]
        },
        "considerationsEnvironnementales": {
          "considerationEnvironnementale": [
            "Clause environnementale"
          ]
        },
        "attributionAvance": "1",
        "considerationsSociales": {
          "considerationSociale": [
            "Clause sociale",
            "Critère social"
          ]
        },
        "nature": "Marché",
        "objet": "envoi pour Json test 1",
        "codeCPV": "45000000-7",
        "techniques": {
          "technique": [
            "Concours",
            "Accord-cadre"
          ]
        },
        "modalitesExecution": 
		{
			"modaliteExecution": [
			  "Tranches"]}
		,
		"idAccordCadre": "1234567890",
        "tauxAvance": 0,
        "titulaires": [
          {
            "titulaire": {
              "id": "55204599900869",
              "typeIdentifiant": "SIRET"
            }
          }
        ],
        "typeGroupementOperateurs": "Pas de groupement",
        "sousTraitanceDeclaree": True,
        "datePublicationDonnees": "2024-05-25",
        "actesSousTraitance": [
          {
            "acteSousTraitance": {
              "id": 1,
              "sousTraitant": {
                "id": "214356",
                "typeIdentifiant": "SIRET"
              },
              "dureeMois": 12,
              "dateNotification": "2023-10-11",
              "montant": 123456.89,
              "variationPrix": "Révisable",
              "datePublicationDonnees": "2023-10-12"
            }
          }
        ],
        "modifications": [
          {
            "modification": {
              "id": 1,
              "dureeMois": 12,
              "montant": 123457.87,
              "titulaires": [
                {
                  "titulaire": {
                    "id": "868768687576575",
                    "typeIdentifiant": "SIRET"
                  }
                }
			  ],
              "dateNotificationModification": "2022-10-18",
              "datePublicationDonneesModification": "2022-10-20"
            }
          }
		],
        "modificationsActesSousTraitance": [
          {
            "modificationActeSousTraitance": {
              "id": 1,
              "dureeMois": 12,
              "dateNotificationModificationSousTraitance": "2022-10-20",
              "montant": 23465.87,
              "datePublicationDonnees": "2022-12-15"
            }
          }
		],
        "procedure": "Appel d'offres ouvert",
        "lieuExecution": {
          "code": "75000",
          "typeCode": "Code postal"
        },
        "dureeMois": 48,
        "dateNotification": "2024-05-15",
        "montant": 575000
      },
      {
        "id": "TEST2022Bis",
        "acheteur": {
          "id": "21750001630040"
        },
        "marcheInnovant": "non",
        "origineUE": 0.1,
        "origineFrance": 0.1,
        "ccag": "Travaux",
        "offresRecues": 4,
        "formePrix": "Forfaitaire",
        "typesPrix": {
          "typePrix": [
			"Définitif ferme"
		  ]
        },
        "considerationsEnvironnementales": {
          "considerationEnvironnementale": [
            "Clause environnementale"
          ]
        },
        "attributionAvance": True,
        "considerationsSociales": {
          "considerationSociale": [
            "Clause sociale",
            "Critère social"
          ]
        },
        "nature": "Marché",
        "objet": "envoi pour Json test 2",
        "codeCPV": "45000000-7",
        "techniques": {
          "technique": [
            "Concours",
            "Accord-cadre"
          ]
        },
        "modalitesExecution": 
		{
			"modaliteExecution": [
				"Tranches"]
		}
		,
        "idAccordCadre": "1234567890",
        "tauxAvance": 0,
        "titulaires": [
          {
            "titulaire": {
              "id": "55204599900869",
              "typeIdentifiant": "SIRET"
            }
          }
        ],
        "typeGroupementOperateurs": "Pas de groupement",
        "sousTraitanceDeclaree": True,
        "datePublicationDonnees": "2024-05-25",
        "actesSousTraitance": [
          {
            "acteSousTraitance": {
              "id": 1,
              "sousTraitant": {
                "id": "214356",
                "typeIdentifiant": "SIRET"
              },
              "dureeMois": 12,
              "dateNotification": "2023-10-11",
              "montant": 123456.89,
              "variationPrix": "Révisable",
              "datePublicationDonnees": "2023-10-12"
            }
          }
        ],
        "modifications": [
          {
            "modification": {
              "id": 1,
              "dureeMois": 12,
              "montant": 123457.87,
              "titulaires": [
                {
                  "titulaire": {
                    "id": "868768687576575",
                    "typeIdentifiant": "SIRET"
                  }
                }
              ],
              "dateNotificationModification": "2022-10-18",
              "datePublicationDonneesModification": "2022-10-20"
            }
          }
		],
        "modificationsActesSousTraitance": [
          {
            "modificationActeSousTraitance": {
              "id": 1,
              "dureeMois": 12,
              "dateNotificationModificationSousTraitance": "2022-10-20",
              "montant": 23465.87,
              "datePublicationDonnees": "2022-12-15"
            }
          }
		],
        "procedure": "Appel d'offres ouvert",
        "lieuExecution": {
          "code": "75000",
          "typeCode": "Code postal"
        },
        "dureeMois": 48,
        "dateNotification": "2024-05-15",
        "montant": 575000
      }
    ]

        self.assertListEqual(expected_result_json, self.process.dico_2022_marche)


    def test_tri_format_xml(self):
        with open(f"tests/test_tri.xml", encoding='utf8') as xml_file1:
            dico3 =  xmltodict.parse(xml_file1.read(), dict_constructor = dict, force_list=('marche',))

        with open(f"tests/test_tri_new_dico.json", "w", encoding='utf8') as jsn_file4:
            jsn_file4.write(json.dumps(dico3))

        #XML
        self.process.tri_format(dico3,"test_tri")
        expected_result_xml = [{
        "id": "20242023F0002600", 
        "acheteur": 
            {"id": "20007067000019", 
            "nom": "CC DU PAYS DE DOL ET DE LA BAIE DU MONT SAINT-MICHEL"
            }, 
        "marcheInnovant": None, 
        "nature": "Marché", 
        "typeContrat": "MARCHE_PUBLIC", 
        "objet": "PROGRAMME PLURIANNUEL BREIZH BOCAGE -TRAVAUX DE PLANTATIONS  POUR LA PERIODE 2023 A 2026 - Fourniture et livraison du paillage copeaux de bois", 
        "codeCPV": "03417000", 
        "procedure": "Proc\u00e9dure adapt\u00e9e", 
        "lieuExecution": 
            {"code": "35", 
             "typeCode": "Code d\u00e9partement", 
             "nom": "(35) Ille-et-Vilaine"
             }, 
        "dureeMois": "36", 
        "dateNotification": "2024-01-22", 
        "datePublicationDonnees": "2024-01-22", 
        "montant": "73500.0", 
        "formePrix": "R\u00e9visable", 
        "titulaires":
         {"titulaire": 
            {"typeIdentifiant": "SIRET", 
             "id": "50327243700032", 
             "denominationSociale": "SCIC ENERGIES RENOUVELABLES PAYS DE RANCE"}},
        "uuid": "431784D1-8731-42D9-A420-53D53704D9DF", 
        "techniques": None, 
        "modalitesExecution": None, 
        "considerationsSociales": None, 
        "considerationsEnvironnementales": None,
        "origineUE": None, 
        "origineFrance": None, 
        "ccag": None, 
        "offresRecues": None, 
        "typesPrix": None, 
        "attributionAvance": None,
        }]

        #print("DICO 2022 :", self.process.dico_2022)
        self.assertListEqual(expected_result_xml, self.process.dico_2022_marche)


    def test_clean(self):
        """
        La fonction réalise le test de la fonction "clean" en utilisant
        le fichier "marches_avec_modifications" qui suit le format 2022.
        """
        self.process.title = ["marches_avec_modifications.json"]
        self.process.clean()
        expected_result =  [
      {
        "id": "TEST2022",
        "acheteur": {
          "id": "21750001630066"
        },
        "marcheInnovant": False,
        "origineUE": 0.1,
        "origineFrance": 0.1,
        "ccag": "Travaux",
        "offresRecues": 4,
        "formePrix": "Forfaitaire",
        "typesPrix": {
          "typePrix": [
			"Définitif ferme"
		  ]
        },
        "considerationsEnvironnementales": {
          "considerationEnvironnementale": [
            "Clause environnementale"
          ]
        },
        "attributionAvance": "1",
        "considerationsSociales": {
          "considerationSociale": [
            "Clause sociale",
            "Critère social"
          ]
        },
        "nature": "Marché",
        "objet": "envoi pour Json test 1",
        "codeCPV": "45000000-7",
        "techniques": {
          "technique": [
            "Concours",
            "Accord-cadre"
          ]
        },
        "modalitesExecution": 
		{
			"modaliteExecution": [
			  "Tranches"]}
		,
		"idAccordCadre": "1234567890",
        "tauxAvance": 0,
        "titulaires": [
          {
            "titulaire": {
              "id": "55204599900869",
              "typeIdentifiant": "SIRET"
            }
          }
        ],
        "typeGroupementOperateurs": "Pas de groupement",
        "sousTraitanceDeclaree": True,
        "datePublicationDonnees": "2024-05-25",
        "actesSousTraitance": [
          {
            "acteSousTraitance": {
              "id": 1,
              "sousTraitant": {
                "id": "214356",
                "typeIdentifiant": "SIRET"
              },
              "dureeMois": 12,
              "dateNotification": "2023-10-11",
              "montant": 123456.89,
              "variationPrix": "Révisable",
              "datePublicationDonnees": "2023-10-12"
            }
          }
        ],
        "modifications": [
          {
            "modification": {
              "id": 1,
              "dureeMois": 12,
              "montant": 123457.87,
              "titulaires": [
                {
                  "titulaire": {
                    "id": "868768687576575",
                    "typeIdentifiant": "SIRET"
                  }
                }
			  ],
              "dateNotificationModification": "2022-10-18",
              "datePublicationDonneesModification": "2022-10-20"
            }
          }
		],
        "modificationsActesSousTraitance": [
          {
            "modificationActeSousTraitance": {
              "id": 1,
              "dureeMois": 12,
              "dateNotificationModificationSousTraitance": "2022-10-20",
              "montant": 23465.87,
              "datePublicationDonnees": "2022-12-15"
            }
          }
		],
        "procedure": "Appel d'offres ouvert",
        "lieuExecution": {
          "code": "75000",
          "typeCode": "Code postal"
        },
        "dureeMois": 48,
        "dateNotification": "2024-05-15",
        "montant": 575000
      },
      {
        "id": "TEST2022Bis",
        "acheteur": {
          "id": "21750001630040"
        },
        "marcheInnovant": "non",
        "origineUE": 0.1,
        "origineFrance": 0.1,
        "ccag": "Travaux",
        "offresRecues": 4,
        "formePrix": "Forfaitaire",
        "typesPrix": {
          "typePrix": [
			"Définitif ferme"
		  ]
        },
        "considerationsEnvironnementales": {
          "considerationEnvironnementale": [
            "Clause environnementale"
          ]
        },
        "attributionAvance": True,
        "considerationsSociales": {
          "considerationSociale": [
            "Clause sociale",
            "Critère social"
          ]
        },
        "nature": "Marché",
        "objet": "envoi pour Json test 2",
        "codeCPV": "45000000-7",
        "techniques": {
          "technique": [
            "Concours",
            "Accord-cadre"
          ]
        },
        "modalitesExecution": 
		{
			"modaliteExecution": [
				"Tranches"]
		}
		,
        "idAccordCadre": "1234567890",
        "tauxAvance": 0,
        "titulaires": [
          {
            "titulaire": {
              "id": "55204599900869",
              "typeIdentifiant": "SIRET"
            }
          }
        ],
        "typeGroupementOperateurs": "Pas de groupement",
        "sousTraitanceDeclaree": True,
        "datePublicationDonnees": "2024-05-25",
        "actesSousTraitance": [
          {
            "acteSousTraitance": {
              "id": 1,
              "sousTraitant": {
                "id": "214356",
                "typeIdentifiant": "SIRET"
              },
              "dureeMois": 12,
              "dateNotification": "2023-10-11",
              "montant": 123456.89,
              "variationPrix": "Révisable",
              "datePublicationDonnees": "2023-10-12"
            }
          }
        ],
        "modifications": [
          {
            "modification": {
              "id": 1,
              "dureeMois": 12,
              "montant": 123457.87,
              "titulaires": [
                {
                  "titulaire": {
                    "id": "868768687576575",
                    "typeIdentifiant": "SIRET"
                  }
                }
              ],
              "dateNotificationModification": "2022-10-18",
              "datePublicationDonneesModification": "2022-10-20"
            }
          }
		],
        "modificationsActesSousTraitance": [
          {
            "modificationActeSousTraitance": {
              "id": 1,
              "dureeMois": 12,
              "dateNotificationModificationSousTraitance": "2022-10-20",
              "montant": 23465.87,
              "datePublicationDonnees": "2022-12-15"
            }
          }
		],
        "procedure": "Appel d'offres ouvert",
        "lieuExecution": {
          "code": "75000",
          "typeCode": "Code postal"
        },
        "dureeMois": 48,
        "dateNotification": "2024-05-15",
        "montant": 575000
      }
    ]   
        self.assertListEqual(expected_result, self.process.dico_2022_marche)
        
    
    def test_drop_duplicate(self):
        #Résultat qu'on doit avoir
        dico_modele = [
      {
        "id": "TEST2022Bis",
        "acheteur": {
          "id": "21750001630040"
        },
        "marcheInnovant": "non",
        "origineUE": 0.1,
        "origineFrance": 0.1,
        "ccag": "Travaux",
        "offresRecues": 4,
        "formePrix": "Forfaitaire",
        "typesPrix": {
          "typePrix": [
      "Définitif ferme"
      ]
        },
        "considerationsEnvironnementales": {
          "considerationEnvironnementale": [
            "Clause environnementale"
          ]
        },
        "attributionAvance": True,
        "considerationsSociales": {
          "considerationSociale": [
            "Clause sociale",
            "Critère social"
          ]
        },
        "nature": "Marché",
        "objet": "envoi pour Json test 2",
        "codeCPV": "45000000-7",
        "techniques": {
          "technique": [
            "Concours",
            "Accord-cadre"
          ]
        },
        "modalitesExecution": 
    {
      "modaliteExecution": [
        "Tranches"]
    }
    ,
        "idAccordCadre": "1234567890",
        "tauxAvance": 0,
        "titulaires": [
          {
            "titulaire": {
              "id": "55204599900869",
              "typeIdentifiant": "SIRET"
            }
          }
        ],
        "typeGroupementOperateurs": "Pas de groupement",
        "sousTraitanceDeclaree": True,
        "datePublicationDonnees": "2024-05-25",
        "actesSousTraitance": [
          {
            "acteSousTraitance": {
              "id": 1,
              "sousTraitant": {
                "id": "214356",
                "typeIdentifiant": "SIRET"
              },
              "dureeMois": 12,
              "dateNotification": "2023-10-11",
              "montant": 123456.89,
              "variationPrix": "Révisable",
              "datePublicationDonnees": "2023-10-12"
            }
          }
        ],
        "modifications": [
          {
            "modification": {
              "id": 1,
              "dureeMois": 12,
              "montant": 123457.87,
              "titulaires": [
                {
                  "titulaire": {
                    "id": "868768687576575",
                    "typeIdentifiant": "SIRET"
                  }
                }
              ],
              "dateNotificationModification": "2022-10-18",
              "datePublicationDonneesModification": "2022-10-20"
            }
          }
    ],
        "modificationsActesSousTraitance": [
          {
            "modificationActesSousTraitance": {
              "id": 1,
              "dureeMois": 12,
              "dateNotificationModificationSousTraitance": "2022-10-20",
              "montant": 23465.87,
              "datePublicationDonnees": "2022-12-15"
            }
          }
    ],
        "procedure": "Appel d'offres ouvert",
        "lieuExecution": {
          "code": "75000",
          "typeCode": "Code postal"
        },
        "dureeMois": 48,
        "dateNotification": "2024-05-15",
        "montant": 575000,
        "source": "sample_json"
      },
        {
        "id": "TEST2022",
        "acheteur": {
          "id": "21750001630066"
        },
        "marcheInnovant": "false",
        "origineUE": "0.1",
        "origineFrance": "0.1",
        "ccag": "Travaux",
        "offresRecues": "4",
        "formePrix": "Forfaitaire",
        "typesPrix": {
          "typePrix": [
      "Définitif ferme"
      ]
        },
        "considerationsEnvironnementales": {
          "considerationEnvironnementale": [
            "Clause environnementale"
          ]
        },
        "attributionAvance": "1",
        "considerationsSociales": {
          "considerationSociale": [
            "Clause sociale",
            "Critère social"
          ]
        },
        "nature": "Marché",
        "objet": "envoi pour Json test 1",
        "codeCPV": "45000000-7",
        "techniques": {
          "technique": [
            "Concours",
            "Accord-cadre"
          ]
        },
        "modalitesExecution": 
    {
      "modaliteExecution": [
        "Tranches"]}
    ,
    "idAccordCadre": "1234567890",
        "tauxAvance": "0",
        "titulaires": [
          {
            "titulaire": {
              "id": "55204599900869",
              "typeIdentifiant": "SIRET"
            }
          }
        ],
        "typeGroupementOperateurs": "Pas de groupement",
        "sousTraitanceDeclaree": "true",
        "datePublicationDonnees": "2024-05-29",
        "actesSousTraitance": [
          {
            "acteSousTraitance": {
              "id": "1",
              "sousTraitant": {
                "id": "214356",
                "typeIdentifiant": "SIRET"
              },
              "dureeMois": "12",
              "dateNotification": "2023-10-11",
              "montant": "123456.89",
              "variationPrix": "Révisable",
              "datePublicationDonnees": "2023-10-12"
            }
          }
        ],
        "modifications": [
          {
            "modification": {
              "id": "1",
              "dureeMois": "12",
              "montant": "123457.87",
              "titulaires": [
                {
                  "titulaire": {
                    "id": "868768687576575",
                    "typeIdentifiant": "SIRET"
                  }
                }
        ],
              "dateNotificationModification": "2022-10-18",
              "datePublicationDonneesModification": "2022-10-20"
            }
          }
    ],
        "modificationsActesSousTraitance": [
          {
            "modificationActesSousTraitance": {
              "id": "1",
              "dureeMois": "12",
              "dateNotificationModificationSousTraitance": "2022-10-20",
              "montant": "23465.87",
              "datePublicationDonnees": "2022-12-15"
            }
          }
    ],
        "procedure": "Appel d'offres ouvert",
        "lieuExecution": {
          "code": "75000",
          "typeCode": "Code postal"
        },
        "dureeMois": "48",
        "dateNotification": "2024-05-15",
        "montant": "575000",
        "source": "sample_xml"
      }
    ]


        df_modele = pd.DataFrame.from_dict(dico_modele)
 
        #Ouverture des fichiers où on récupère les données
        with open(f"documents/marches_avec_modifications.json", encoding='utf8') as json_file :
            dico_json = json.load(json_file)
        with open(f"documents/marches_avec_modifications.xml", encoding='utf8') as xml_file:
            dico_xml =  xmltodict.parse(xml_file.read(), dict_constructor = dict, force_list=('marche','titulaires', \
                                            'modifications', 'actesSousTraitance','modificationsActesSousTraitance', \
                                                     'typePrix','considerationEnvironnementale', 'modaliteExecution'))
        #Transformation Ddes dictionnaires en dataframe dans l'objet GlobalProcess
        df_json = pd.DataFrame.from_dict(dico_json["marches"]["marche"])
        df_json = df_json.assign(source="sample_json")
        
        df_xml = pd.DataFrame.from_dict(dico_xml["marches"]["marche"])
        df_xml = df_xml.assign(source="sample_xml")
        
        self.global_process.dataframes = [df_json, df_xml]
        self.global_process.merge_all()
        
        #Fonction à tester
        self.global_process.drop_duplicate()

        result = df_modele.equals(self.global_process.df)
        expected_result = True

        self.assertEqual(expected_result,result)


if __name__ == '__main__':
    #unittest.main()

    obj = UneClasseDeTest()
    obj.setUp()
    obj.test_drop_duplicate()

