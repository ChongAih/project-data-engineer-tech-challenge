#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Read Docker config and export for docker-compose usage
. "$SCRIPT_DIR"/section4/conf/section4_postgresql.ini
. "$SCRIPT_DIR"/section4/conf/section4_python.ini
. "$SCRIPT_DIR"/section4/conf/section4_grafana.ini

export POSTGRES_USER
export POSTGRES_PASSWORD
export POSTGRES_DB
export POSTGRES_PORT

command="$1"

if [ "$command" = "start" ]; then

  echo && echo "==================================== BUILDING DOCKER IMAGE ====================================" && echo

  # Remove the old image
  docker image ls | grep -q "$PIPELINE_IMAGE_NAME" && docker image rm -f "$PIPELINE_IMAGE_NAME":"$PIPELINE_TAG_NAME"
  docker image ls | grep -q "$POSTGRES_IMAGE_NAME" && docker image rm -f "$POSTGRES_IMAGE_NAME":"$POSTGRES_TAG_NAME"

  # Build a new image based on the Dockerfile
  docker build \
    --build-arg DEPLOYMENT_ENV="docker" \
    -t "$PIPELINE_IMAGE_NAME":"$PIPELINE_TAG_NAME" -f "$SCRIPT_DIR"/docker/section4_python_dockerfile .

  # Build a new image based on the Dockerfile
  docker build \
    --build-arg POSTGRES_USER="$POSTGRES_USER" \
    --build-arg POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    --build-arg POSTGRES_DB="$POSTGRES_DB" \
    -t "$POSTGRES_IMAGE_NAME":"$POSTGRES_TAG_NAME" -f "$SCRIPT_DIR"/docker/section4_postgres_dockerfile .

  echo && echo "==================================== CREATING DOCKER NETWORK ====================================" && echo

  docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK"

  echo && echo "==================================== RUNNING DOCKER CONTAINER ====================================" && echo

  docker container run \
    --rm --name "$POSTGRES_CONTAINER_NAME" \
    -p "$POSTGRES_EXTERNAL_PORT":"$POSTGRES_PORT" \
    --hostname "$POSTGRES_HOSTNAME" \
    --network "$NETWORK" \
    -d "$POSTGRES_IMAGE_NAME":"$POSTGRES_TAG_NAME"

  docker container run \
    -v "${PWD}"/section4:/data_pipeline/section4 \
    --network "$NETWORK" \
    --rm --name "$PIPELINE_CONTAINER_NAME" -p 80:4040 -d "$PIPELINE_IMAGE_NAME":"$PIPELINE_TAG_NAME"

  docker container run \
    --rm --name "$GF_CONTAINER_NAME" \
    -p "$GF_EXTERNAL_PORT":"$GF_PORT" \
    --network "$NETWORK" \
    -e GF_INSTALL_PLUGINS="$GF_INSTALL_PLUGINS" \
    -e GF_SECURITY_ADMIN_USER="$GF_SECURITY_ADMIN_USER" \
    -e GF_SECURITY_ADMIN_PASSWORD="$GF_SECURITY_ADMIN_PASSWORD" \
    -e GF_USERS_ALLOW_SIGN_UP="$GF_USERS_ALLOW_SIGN_UP" \
    -e GF_DASHBOARDS_JSON_ENABLED="$GF_DASHBOARDS_JSON_ENABLED" \
    -d "$GF_IMAGE_TAG_NAME"

  echo && echo "==================================== INGEST P1Y COVID-19 DATA ====================================" && echo

  # Sleep while waiting for postgresql to complete setup
  sleep 10;

  # Ingest Covid data to postgresql
  docker container exec "$PIPELINE_CONTAINER_NAME" bash -c 'python3 section4_manage.py --task-config section4_process.yaml'

  echo && echo "==================================== CREATING AND POSTING DASHBOARD ====================================" && echo

  # Sleep while waiting for grafana to complete setup
  sleep 10;

  # Create datasource JSON
  cat "$SCRIPT_DIR"/section4/grafana/postgres_datasource_template.json | \
    sed "s/\$postgres_hostname/$POSTGRES_HOSTNAME/g" | \
    sed "s/\$postgres_port/$POSTGRES_PORT/g" | \
    sed "s/\$postgres_password/$POSTGRES_PASSWORD/g" | \
    sed "s/\$postgres_user/$POSTGRES_USER/g" | \
    sed "s/\$postgres_db/$POSTGRES_DB/g" > "$SCRIPT_DIR"/section4/grafana/postgres_datasource.json

  curl --user "$GF_SECURITY_ADMIN_USER":"$GF_SECURITY_ADMIN_PASSWORD" \
    -H 'Accept: application/json' -H 'Content-Type: application/json; charset=UTF-8' \
    -X POST --data @"$SCRIPT_DIR"/section4/grafana/postgres_datasource.json \
    http://localhost:"$GF_EXTERNAL_PORT"/api/datasources

  curl --user "$GF_SECURITY_ADMIN_USER":"$GF_SECURITY_ADMIN_PASSWORD" \
    -H 'Accept: application/json' -H 'Content-Type: application/json; charset=UTF-8' \
    -X POST --data @"$SCRIPT_DIR"/section4/grafana/covid_dashboard.json \
    http://localhost:"$GF_EXTERNAL_PORT"/api/dashboards/db

elif [ "$command" = "stop" ]; then

  echo && echo "==================================== STOPPING DOCKER CONTAINER ====================================" && echo

  # docker stop and remove existing instance if any
  docker container ls -a -q --filter "name=$POSTGRES_CONTAINER_NAME" | grep -q . && docker container stop "$POSTGRES_CONTAINER_NAME"
  docker container ls -a -q --filter "name=$PIPELINE_CONTAINER_NAME" | grep -q . && docker container stop "$PIPELINE_CONTAINER_NAME"
  docker container ls -a -q --filter "name=$GF_CONTAINER_NAME" | grep -q . && docker container stop "$GF_CONTAINER_NAME"

else

  echo "sh section4_runner.sh <start | stop> "
  echo "<start | stop> start or stop all docker container"
  exit 1

fi
