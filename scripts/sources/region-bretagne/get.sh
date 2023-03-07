
#!/bin/bash

# Récupération des données


echo "Telechargement region bretagne 2019"
wget -q -O decp2019_regionbretagne.xml https://data.bretagne.bzh/api/datasets/1.0/decp-crb0/alternative_exports/2019_decp_crb_xml
echo "Telechargement region bretagne 2020"
wget -q -O decp2020_regionbretagne.xml https://data.bretagne.bzh/api/datasets/1.0/decp-crb0/alternative_exports/2020_decp_crb_xml
echo "Telechargement region bretagne 2021"
wget -q -O decp2021_regionbretagne.xml https://data.bretagne.bzh/api/datasets/1.0/decp-crb0/alternative_exports/2021_decp_crb_xml
echo "Telechargement region bretagne 2022"
wget -q -O decp2022_regionbretagne.xml https://data.bretagne.bzh/api/datasets/1.0/decp-crb0/alternative_exports/2022_decp_crb_xml
