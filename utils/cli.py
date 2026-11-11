"""Arguments de la ligne de commande et configuration du mode test.

Ce module ne doit importer aucun module du projet : il est chargé par main.py
AVANT utils.Paths et database.DbDecp, afin que le mode test (-t) puisse modifier
les variables d'environnement lues à l'import de ces modules.
"""
import argparse
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", dest='test', action='store_true',
                        help="mode test : base decp_test, répertoire data_test, pas de publication data.gouv")
    parser.add_argument("-l", dest='local', action='store_true', help="run script locally")
    parser.add_argument("-r", dest='reset', action='store_true', help="reset execution cache")
    parser.add_argument('-P', dest='process', type=str, help='run a specific process')
    parser.add_argument("-m", dest='rama', action='store_true', help="Execute only decp-rama")
    parser.add_argument("-a", dest='augmente', action='store_true', help="Execute only decp-augmente")
    #parser.add_argument("-f", dest='format', type=str, help="run script for format 2019")
    parser.add_argument("-b", dest='rebuild', type=str, help="Rebuild a given year")
    return parser.parse_args()


def configure_test_mode():
    """Active le mode test. À appeler AVANT tout import de utils.Paths / database.DbDecp.

    - DECP_TEST_MODE=1 : DbDecp se connecte à la base de test (DECP.DB_NAME_TEST, défaut decp_test)
    - DECP_DATA_DIR suffixé par _test : data -> data_test, /app/data -> /app/data_test
    """
    os.environ["DECP_TEST_MODE"] = "1"
    base_dir = os.environ.get("DECP_DATA_DIR", "data").rstrip("/\\")
    os.environ["DECP_DATA_DIR"] = base_dir + "_test"
