#!/bin/bash

#**********************************************************************
#
# Transformation des données du format DECP JSON vers le format OCDS JSON
#
#**********************************************************************

# fail on error
set -e

# Création du fichier de release OCDS à partir des DECP
jq --arg datetime $datetime --arg datasetUrl $dataset_url --arg ocidPrefix $ocid_prefix --arg packageUri $package_uri -f scripts/jq/ocds/decp2ocds.jq $1
