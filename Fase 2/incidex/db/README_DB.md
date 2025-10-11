Creamos la base de datos
docker compose --env-file ../../.env up -d

Levantar el contenedor
docker compose --env-file ../../.env up -d

Primer Script SQL
docker exec -i incidex-mysql `
  sh -c "mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE}" `
  < ../../db/migrations/001_init.sql

Segundo Script SQL
docker exec -i incidex-mysql `
  sh -c "mysql -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE}" `
  < ../../db/migrations/002_core_tables.sql

Apagar el contenedor (sin borrar datos)
docker compose --env-file ../../.env down

Revisar BD
http://localhost:8080