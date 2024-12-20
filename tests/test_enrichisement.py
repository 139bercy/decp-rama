import pandas as pd
import numpy as np
import enrichissement

"""Peut prendre du temps si on ne commente pas la ligne utils.download_data_enrichissement() dans enrichissement.
Pour les tests il vaut mieux avoir les fichiers en local puis commenter la ligne et executer pytest.

Ces tests sont principalement des tests de non-régression. Qu'on s'assure que les modifications faites ne perturbent pas certains fonctionnement.
"""


def test_enrichissement_acheteur():
    df = pd.DataFrame(columns=["siret", "acheteur.id"], data=[['21740276700016', '21740276700016']])
    df = enrichissement.enrichissement_acheteur(df)
    assert df.loc[0, "libelleCommuneAcheteur"] == "TANINGES"


def test_renommage_et_recategorisation():
    df = pd.DataFrame(columns=["nomAcheteur", "idAcheteur", "siretEtablissement","sirenEtablissement", "denominationSociale_x", "id_cotitulaire1", "denominationSociale_cotitulaire1", 
    "id_cotitulaire2", "denominationSociale_cotitulaire2", "id_cotitulaire3", "denominationSociale_cotitulaire3"], 
    data=[['MauvaisNom', '24840025100158', "2222877785295","877785295", "UneDenomination", "99692002100028", "nom_cotit1", "005564", "nom2", "01575266000041", "nom3" ],
    ['MauvaisNom', '24840025100158',"111877785295", "877785295", "UneDenomination", np.nan, np.nan, np.nan, np.nan, np.nan] ])
    df = enrichissement.renommage_et_recategorisation(df)
    assert (df.nomAcheteur.values == ["COMMUNAUTE D'AGGLOMERATION DU GRAND AVIGNON"]*2).all()
    assert (df.denominationUniteLegale.values == ["MK ETANCHEITE"]*2).all()
    assert (df.loc[:, "denominationSociale_x"].values == ["UneDenomination"]*2).all()
    # Testons les cotitulaires
    assert (df.loc[0, "denominationSociale_cotitulaire1"] == "ENTREPRISE REYNIER") # La deuxième data n'a pas de nom pour les cotit
    assert (df.loc[0, "denominationSociale_cotitulaire2"] == "nom2") # En effet l'id est un id aléatoire de mauvaise taille donc n'aura pas de correpsondance
    assert (df.loc[0, "denominationSociale_cotitulaire3"] == "nom3") # La deuxième data n'a pas de nom pour les cotit
    assert(df.loc[1, "siretEtablissement"] == "00111877785295" )

def test_apply_luhn():
    df = pd.DataFrame(columns=["idAcheteur", "sirenEtablissement", "siretEtablissement", "typeIdentifiantEtablissement"], data=[['24840025100158', "877785295", "87778529500000", "SIRET"]])   
    df = enrichissement.apply_luhn(df)
    assert df.sirenAcheteurValide.values == True
    assert df.sirenEtablissementValide.values == True
    assert df.siretEtablissementValide.values == "False" # En effet il est faux, les deux premiers sont extrait de vrais entités (cf les deux fonctions plus haut). le siret est créé sans considération dela formule.
    # Pourquoi a-t-on un string au lieu d'un boolean ? A cause du np.where où l'une des possibilités est un string. Ce qui donne une colonne de string. Donc un "False"


def test_enrichissement_cpv():
    df = pd.DataFrame(columns=['codeCPV'], data=['33121100-5', "45421000-4"])
    df = enrichissement.enrichissement_cpv(df)
    assert df.refCodeCPV.tolist() == ['Électroencéphalographes', 'Travaux de menuiserie']

def test_enrichissement_departement():
    df = pd.DataFrame(columns=["codePostalAcheteur", "codePostalEtablissement"],
    data=[['85000', "91140"], ["69330", "27100"]])
    df = enrichissement.enrichissement_departement(df)
    assert (df.libelleDepartementAcheteur.values == ['Vendée', 'Rhône']).all()
    assert (df.libelleDepartementEtablissement.values == ['Essonne', 'Eure']).all()
    assert (df.codeRegionAcheteur.values ==['52', '84']).all()
    assert (df.codeRegionEtablissement.values ==['11', "28"]).all()