import pandas as pd
import numpy as np
import pytest
import nettoyage


@pytest.fixture
def create_dataframe():
    dftest = pd.DataFrame()
    dftest['id'] = ["a", "b"]
    dftest['source'] = ['AA', 'BB']
    dftest['objet'] = ['BlablaModif', 'BlaBlaRien']
    dftest['datePublicationDonnees'] = ['2023-01-16', '2022-01-16']
    dftest['modifications'] = [[{'dateNotificationModification': '2023-01-16',
                                 'objetModification': 'AU 21/12/2022, le CH de Sarreguemines pourra bénéficier du lot 189.1 avec une qté de 50',
                                 'datePublicationDonneesModification': '2023-01-17',
                                 'montant': 50}, {'dateNotificationModification': '2023-01-17',
                                                  'objetModification': 'AU 21/12/2022, le CH de Sarreguemines pourra bénéficier du lot 189.1 avec une qté de 100',
                                                  'datePublicationDonneesModification': '2023-01-18',
                                                  'montantModification': 77777778, 'dateSignature': '2023-01-01'}], '']
    dftest['uid'] = ['aa', 'bb']
    dftest['uuid'] = ['aaa', 'bbb']
    dftest['_type'] = ['typea', 'typeb']
    dftest['codeCPV'] = [np.nan, '30192000-1']
    dftest['lieuExecution.code'] = ['83220', '97209']
    dftest['lieuExecution.typeCode'] = ['Code postal', 'Code Postal']
    dftest['lieuExecution.nom'] = ['Le Pradet', 'Fort-de-France']
    dftest['dureeMois'] = [2, 3]
    dftest['montant'] = [0, 3.5]
    dftest['dateNotification'] = ['2021-01-01', 'MauvaiseDate']
    dftest['formePrix'] = ['Forme1', 'Forme2']
    dftest['titulaires'] = [[{'typeIdentifiant': 'SIRET',
                              'id': '65950183700010',
                              'denominationSociale': 'CHARLEMAGNE PROFESSIONNEL'}],
                            [{'typeIdentifiant': 'SIRET',
                              'id': '05720137800080',
                              'denominationSociale': 'HUMBERT ET CIE'},
                             {'typeIdentifiant': 'SIRET',
                              'id': '42856174000138',
                              'denominationSociale': 'CISE TP'},
                             {'typeIdentifiant': 'SIRET',
                              'id': '31884522900059',
                              'denominationSociale': 'DURAND LUC SA'}]]
    dftest['dateSignature'] = ['2020-01-01', np.nan]
    dftest['nature'] = ['marché', 'marché']
    dftest['autoriteConcedante.id'] = ['', '']
    dftest['autoriteConcedante.nom'] = ['A', 'B']
    dftest['acheteur.id'] = ['21740276700016', '24840025100158']
    dftest['acheteur.nom'] = ['nomA', 'nomB']
    dftest['donneesExecution'] = ['donneeA', 'donneeB']
    dftest['valeurGlobale'] = [0, 0]
    dftest['concessionnaires'] = ['', '']
    dftest['montantSubventionPublique'] = [10, 10]
    dftest['dateDebutExecution'] = ['2022-10-10', '2023-05-05']
    return dftest


def test_manage_modifications(create_dataframe):
    df = nettoyage.manage_modifications(create_dataframe)
    assert (df.montant.tolist() == [77777778, 3.5])
    assert (df.dateSignature.tolist() == ['2023-01-01', np.nan])


def test_regroupement_marche_complet():
    """
    Compliqué à tester pour pas grand chose. 
    """
    pass


def test_manage_titulaires(create_dataframe):
    df = nettoyage.manage_modifications(create_dataframe)
    df = nettoyage.manage_titulaires(df)
    assert df.loc[:, "id_cotitulaire1"].tolist() == [np.nan, "42856174000138"]
    assert df.loc[:, "id_cotitulaire2"].tolist() == [np.nan, "31884522900059"]
    assert df.loc[:, "id_cotitulaire3"].tolist() == [np.nan, np.nan]
    assert df.loc[:, "idTitulaires"].tolist() == ["65950183700010", "05720137800080"]
    assert df.loc[:, "denominationSociale"].tolist() == ["CHARLEMAGNE PROFESSIONNEL", "HUMBERT ET CIE"]
    assert df.loc[:, "denominationSociale_cotitulaire1"].tolist() == [np.nan, "CISE TP"]


def test_manage_amount(create_dataframe):
    df = nettoyage.manage_modifications(create_dataframe)
    df = nettoyage.manage_titulaires(df)
    df = nettoyage.manage_amount(df)
    assert df.montantCalcule.tolist() == [0,
                                          0]  # 1000 étant au dessus de la borne inf il n'est pas modifié. 3 étant en dessous il est mis à 0
    assert df.montant_inexploitable.tolist() == [True, False]

def test_manage_missing_code(create_dataframe):
    df = nettoyage.manage_modifications(create_dataframe)
    df = nettoyage.manage_titulaires(df)
    df = nettoyage.manage_amount(df)
    df = nettoyage.manage_missing_code(df)
    assert df.codeCPV.tolist() == ['00000000', "30192000-1"]
    assert df.nic.tolist() == ['00010', '00080']
   
def test_manage_region(create_dataframe):
    df = nettoyage.manage_region(create_dataframe)
    assert df.codeDepartementExecution.tolist() == ['83', '972']
    assert df.libelleRegionExecution.tolist() == ["Provence-Alpes-Côte d'Azur", "Martinique"]


def test_manage_date(create_dataframe):
    df = nettoyage.manage_date(create_dataframe)
    assert df.anneeNotification.tolist() == ['2021', 'nan']  # Lorsque c'est pas des digits on a bien des nan
    assert df.moisNotification.tolist() == ['01', 'nan']


def test_correct_date():
    df = pd.DataFrame(columns=['montantCalcule', 'dureeMois'], data=[['360', '360'], ['0', '10000']])
    df = nettoyage.correct_date(df)
    assert df.dureeMoisCalculee.tolist() == [12, 333]
