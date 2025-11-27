#!/usr/bin/env bash
set -Eeo pipefail

echo "Le dump a remonter sera téléchargé depuis le bucket"
/bin/bash /db-shell/maintenance/run-download.sh $1
DUMP_ENC_PATH=`ls -t /backup/*.enc | head -1 `

if [ ! -f "$DUMP_ENC_PATH" ]; then
    echo "le chemin $DUMP_ENC_PATH est incorrect."
fi
BACKUP_FILE=$(basename $DUMP_ENC_PATH)
RESTORE_FULL_PATH=/backup/${BACKUP_FILE%%.*}.tar

# Decryptage du dump :
#=====================

openssl smime -decrypt -in ${DUMP_ENC_PATH} -binary \
  -inform DEM -inkey /keys/backup_key.pem -out ${RESTORE_FULL_PATH}

# Terminaison des processus en cours :
#=====================================

echo "Terminer les process en cours"
psql=(psql -v ON_ERROR_STOP=0)

psqlInstall=${psql}
psqlInstall+=( --username "$POSTGRES_USER" -e --dbname "$POSTGRES_DB")

"${psqlInstall[@]}" -c \
"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname ='${POSTGRES_DB}' AND pid <> pg_backend_pid();" || true

# Exécution de la restauration :
#===============================

echo "Dump à restaurer : ${RESTORE_FULL_PATH}"
pg_restore --clean --dbname "$POSTGRES_DB" --username "$POSTGRES_USER" --exit-on-error -F t ${RESTORE_FULL_PATH}
echo "Dump ${RESTORE_FULL_PATH} restauré"

find /backup/ -name 'dump_*' -mtime +30 -exec rm -f {} \; -print