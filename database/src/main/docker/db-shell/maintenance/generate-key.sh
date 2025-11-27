#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

# Permettre la surcharge via variable d'environnement KEY_DIR (défaut: /backup)
KEY_DIR="${KEY_DIR:-/backup}"
KEY_PATH="${KEY_DIR}/backup_key.pem"
KEY_PUB_PATH="${KEY_DIR}/backup_key.pem.pub"

# Crée le répertoire si nécessaire
mkdir -p "${KEY_DIR}"

openssl req -x509 -nodes -days 1000000 -newkey rsa:4096 \
	-keyout "${KEY_PATH}" \
	-subj "/O=coordocontrol/CN=axyus.com" \
	-out "${KEY_PUB_PATH}"

echo "----------------------------------------------------"
echo "NOTES :"
echo "----------------------------------------------------"
echo "La clé publique a été générée dans : ${KEY_PUB_PATH}"
echo "La clé privée a été générée dans : ${KEY_PATH}"
echo "Merci de copier la clé privée en local puis de la supprimer ici."
echo "La clé privée doit être placée sur le serveur de restauration de la base."
echo "----------------------------------------------------"
echo "----------------------------------------------------"
