
#!/bin/bash

# Récupération des données


wget -r -q -nc -nd -nH --accept=xml -np  https://data.bretagne.bzh/api/datasets/1.0/decp-crb/alternative_exports/decp2021_regionbretagne_csv_xml
