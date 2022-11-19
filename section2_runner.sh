#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Read Docker config and export for docker-compose usage
. "$SCRIPT_DIR"/section2/conf/section2_postgresql.ini

export POSTGRES_USER
export POSTGRES_PASSWORD
export POSTGRES_DB
export POSTGRES_PORT

command="$1"

if [ "$command" = "start" ]; then

  echo && echo "==================================== BUILDING DOCKER IMAGE ====================================" && echo

  # Build a new image based on the Dockerfile
  docker build \
    --build-arg POSTGRES_USER="$POSTGRES_USER" \
    --build-arg POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    --build-arg POSTGRES_DB="$POSTGRES_DB" \
    -t "$POSTGRES_IMAGE_NAME":"$POSTGRES_TAG_NAME" -f "$SCRIPT_DIR"/docker/section2_dockerfile .

  echo && echo "==================================== RUNNING DOCKER CONTAINER ====================================" && echo

  docker container run \
    --rm --name "$POSTGRES_CONTAINER_NAME" -p "$POSTGRES_PORT":"$POSTGRES_PORT" -d "$POSTGRES_IMAGE_NAME":"$POSTGRES_TAG_NAME"

elif [ "$command" = "stop" ]; then

  echo && echo "==================================== STOPPING DOCKER CONTAINER ====================================" && echo

  # docker stop and remove existing instance if any
  docker container ls -a -q --filter "name=$POSTGRES_CONTAINER_NAME" | grep -q . && docker container stop "$POSTGRES_CONTAINER_NAME"

else

  echo "sh section2_runner.sh <start | stop> "
  echo "<start | stop> start or stop all docker container"
  exit 1

fi
