#!/usr/bin/env bash
set -Eeo pipefail

if [ -z "$USER_APPLI_PASSWORD" ]; then
    echo "Error : la variable d'environnement USER_APPLI_PASSWORD doit être renseignée"
    exit 1
fi

psql=(psql -v ON_ERROR_STOP=1)

psqlInstall=${psql}
psqlInstall+=( --username "$POSTGRES_USER" -e --dbname "$POSTGRES_DB")

"${psqlInstall[@]}" -c \
"REVOKE CONNECT ON DATABASE \"${POSTGRES_DB}\" FROM PUBLIC"

"${psqlInstall[@]}" -c \
"REVOKE CONNECT ON DATABASE postgres FROM PUBLIC"

# ROLE USER_APPLI :
# =================
"${psqlInstall[@]}" -c \
"CREATE ROLE \"${USER_APPLI}\" WITH LOGIN NOINHERIT PASSWORD '${USER_APPLI_PASSWORD}'"

# SCHEMA APPLICATIF :
# ===================
"${psqlInstall[@]}" -c \
"CREATE SCHEMA $SCHEMA AUTHORIZATION \"${POSTGRES_USER}\""

# DROITS :
# ========
"${psqlInstall[@]}" -c \
"GRANT CONNECT ON DATABASE \"${POSTGRES_DB}\" TO \"${USER_APPLI}\""

"${psqlInstall[@]}" -c \
"GRANT USAGE ON SCHEMA PUBLIC, $SCHEMA TO \"${USER_APPLI}\""

"${psqlInstall[@]}" -c \
"ALTER DEFAULT PRIVILEGES IN SCHEMA $SCHEMA GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE ON TABLES TO \"${USER_APPLI}\""

"${psqlInstall[@]}" -c \
"ALTER DEFAULT PRIVILEGES IN SCHEMA $SCHEMA GRANT SELECT, UPDATE, USAGE ON SEQUENCES TO \"${USER_APPLI}\""

# SEARCH_PATH :
# =============
"${psqlInstall[@]}" -c \
"ALTER ROLE \"${POSTGRES_USER}\" IN DATABASE \"${POSTGRES_DB}\" SET SEARCH_PATH TO $SCHEMA, PUBLIC"

"${psqlInstall[@]}" -c \
"ALTER ROLE \"${USER_APPLI}\" IN DATABASE \"${POSTGRES_DB}\" SET SEARCH_PATH TO $SCHEMA, PUBLIC"