#!/bin/bash

# Récupération des données


# À partir du répertoire racine (où se trouve README.md), création d'un repértoire temporaire

# Récupération des données, tous les fichiers sont stockés dans le même dossier
# Le nombre de fichiers sur cette source pouvant un jour atteindre des sommets, cette solution n'est pas pérenne
wget -q -r -nd -A xml http://files.data.gouv.fr/decp/

count=`ls -1 | wc -l`

echo ""
echo "$count fichiers téléchargés."
