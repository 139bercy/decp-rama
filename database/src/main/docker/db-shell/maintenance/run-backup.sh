#!/usr/bin/env bash
set -Eeo pipefail

dbname=$POSTGRES_DB
DATE=$(date +%Y%m%d_%H%M%S)
NOW_MONTH=$(date +"%Y-%m")

BUCKET_DAILY="s3/${BUCKET_DAILY_NAME}/"
BUCKET_WEEKLY="s3/database/${BUCKET_WEEKLY_NAME}/"
BUCKET_MONTHLY="s3/database/${BUCKET_MONTHLY_NAME}/"

S3_BIN="mc"
S3_ENDPOINT="${S3_URL}"
BACKUP_FULL_PATH=/backup/dump_${dbname}_${DATE}.tar.enc
KEY_PUB_PATH="/keys/backup_key.pem.pub"

# Récupérer le jour de la semaine
jour_semaine=$(date +%u)

# Récupérer le jour du mois
jour_mois=$(date +%d)

# Récupérer le mois
mois=$(date +%m)

backup_psql(){
    if [ "`date +%d`" = "17" ]
        then
            echo "`date` : vacuum full analyze"
            psql -c "vacuum full analyze;"
        else
            echo "`date` : vacuum"
            psql -c "vacuum;"
        fi

        date=`date '+%Y-%m-%d'`
        pg_dump -F t -d $dbname | openssl smime -encrypt -aes256 -binary -outform DEM -out  ${BACKUP_FULL_PATH} ${KEY_PUB_PATH}

    if [ "`date +%u`" = "7" ]
    then
        /usr/bin/reindexdb -a
    fi
}

upload_s3(){
    ${S3_BIN} cp -r ${BACKUP_FULL_PATH} ${BUCKET_DAILY}
    # Vérifier si c'est un vendredi
    if [[ $jour_semaine == "5" ]]; then
        echo "On est vendredi, les règles hebdommadaires s'appliquent"
        ${S3_BIN} cp -r ${BACKUP_FULL_PATH} ${BUCKET_WEEKLY}
    fi
    # Vérifier si c'est le premier du mois
    if [[ $jour_mois -eq 01 ]]; then
        echo "On est le premier du mois, le règles mensuelles s'appliquent"
        ${S3_BIN} cp -r ${BACKUP_FULL_PATH} ${BUCKET_MONTHLY}
    fi
}

export PATH=$PATH:$HOME/minio-binaries/

mc alias set s3 ${S3_ENDPOINT} $S3_ACCESSKEY $S3_SECRETKEY --api S3v4
history -c

backup_psql
upload_s3

find /backup/ -name 'dump_*' -mtime +2 -exec rm -f {} \; -print