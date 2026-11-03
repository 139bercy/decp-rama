"""Chemins centralisés de tous les fichiers produits par l'application.

Toutes les données générées (téléchargements, métadonnées, résultats, logs, cache
d'exécution...) sont regroupées sous DATA_DIR. Le répertoire racine peut être
surchargé avec la variable d'environnement DECP_DATA_DIR (Docker, CI, tests).
"""
import os

DATA_DIR = os.environ.get("DECP_DATA_DIR", "data")

# decp-rama
SOURCES_DIR = os.path.join(DATA_DIR, "sources")            # fichiers téléchargés par source
METADATA_DIR = os.path.join(DATA_DIR, "metadata")          # métadonnées data.gouv courantes par source
OLD_METADATA_DIR = os.path.join(DATA_DIR, "old_metadata")  # métadonnées du précédent traitement
PROCESSING_DIR = os.path.join(DATA_DIR, "processing")      # run_status.json + snapshots des étapes
RESULTS_DIR = os.path.join(DATA_DIR, "reports")            # rapports errors/statistics
RESULTS_DATA_GOUV = os.path.join(DATA_DIR, "data_gouv")
RESULTS_GLOBAL = os.path.join(DATA_DIR, "global")
RESULTS_DATA_ECO = os.path.join(DATA_DIR, "data_eco")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
RESULT_TRACE_FILE = os.path.join(DATA_DIR, "result_trace.txt")

# decp-augmente
REFERENTIELS_DIR = os.path.join(DATA_DIR, "referentiels")  # cpv, sirene, insee...
DATA_ECLATEES_DIR = os.path.join(DATA_DIR, "data_eclatees")

# Configuration (entrée, versionnée) : liste des sources à traiter
SOURCES_CONFIG = os.path.join("confs", "metadata.json")
