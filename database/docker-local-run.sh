docker network inspect decp-network >/dev/null 2>&1 || docker network create decp-network
docker run --rm -it --name decp-database \
  --network=decp-network \
  --shm-size=256m \
  -e POSTGRES_PASSWORD=decp_install \
  -e USER_APPLI_PASSWORD=decp_appli \
  -v decp-database-data:/var/lib/postgresql/data \
  -p 5432:5432 \
  decp-database