#!/usr/bin/env bash
set -Eeo pipefail
export PATH=$PATH:$HOME/minio-binaries/

mc alias set s3 ${S3_URL} $S3_ACCESSKEY $S3_SECRETKEY --api S3v4
history -c

DUMPDIR=/backup

if [ -z "$1" ]; then
    KEY=`mc ls s3/$BUCKET_DAILY_NAME --recursive | sort | tail -n 1 | awk '{print $6}'`
    mc cp s3/$BUCKET_DAILY_NAME/$KEY ${DUMPDIR}
else
    mc cp s3/$1 ${DUMPDIR}
fi