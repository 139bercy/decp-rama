#!/bin/bash

#**********************************************************************
#
# Transformation des données du format DECP JSON vers le format OCDS JSON
#
#**********************************************************************

datetime=`date "+%FT%T"`
dataset_id="5cc1bb51dc470946203cc376"
dataset_url="https://data.gouv.fr/fr/datasets/$dataset_id"
ocid_prefix="ocds-78apv2"

jq --arg datetime $datetime --arg datasetUrl $dataset_url --arg ocidPrefix $ocid_prefix -f jq/decp2ocds.jq $1
