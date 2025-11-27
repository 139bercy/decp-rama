FROM postgres:16.10-alpine

ENV POSTGRES_DB=decp-database \
    POSTGRES_USER=decp_install \
    USER_APPLI=decp_appli \
    SCHEMA=decp \
    POSTGRES_INITDB_ARGS="--locale-provider=icu --icu-locale=fr_FR --locale=fr_FR.utf8" \
    TZ=Europe/Paris

RUN apk add --no-cache curl openssl && apk upgrade --no-cache
RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc   --create-dirs   -o ~/minio-binaries/mc
RUN chmod +x $HOME/minio-binaries/mc
RUN export PATH=$PATH:$HOME/minio-binaries/

COPY src/main/docker/db-shell/maintenance /db-shell/maintenance/
COPY src/main/docker/db-shell/docker-entrypoint-initdb.d/* /docker-entrypoint-initdb.d/

RUN mkdir /backup \
    && chown -R postgres:postgres /db-shell /backup \
    && chmod 700 /db-shell/maintenance/*.sh